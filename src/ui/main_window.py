import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QToolBar,
                             QDockWidget, QListWidget, QInputDialog, QMessageBox,
                             QCheckBox, QSlider, QDialog, QButtonGroup, QRadioButton,
                             QProgressDialog)
from PyQt6.QtCore import Qt, QTimer
import cv2
from PyQt6.QtWidgets import QApplication

from ui.startup import StartupDialog
from ui.canvas import VideoCanvas
from project.manager import ProjectManager
from video.processor import VideoProcessor, ObjectTracker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Annotator")
        self.resize(1200, 800)

        self.project_manager = None
        self.video_processor = None
        self.tracker = ObjectTracker()

        self.current_frame_idx = 0
        self.current_frame_data = None

        # Will be populated with data: dict of frame_idx -> list of dicts: {'box': (x,y,w,h), 'class_id': int}
        self.annotations = {}

        self.init_ui()

    def init_ui(self):
        # Center Canvas
        self.canvas = VideoCanvas()
        self.setCentralWidget(self.canvas)
        self.canvas.box_drawn.connect(self.on_box_drawn)
        self.canvas.box_resized.connect(self.on_box_resized)

        self.pending_suggestions = [] # List of tuples: {'box': (x,y,w,h), 'class_id': int}

        # Top Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.btn_load_video = QPushButton("Load Video")
        self.btn_load_video.clicked.connect(self.load_video)
        toolbar.addWidget(self.btn_load_video)

        self.cb_load_full = QCheckBox("Load Full Video")
        toolbar.addWidget(self.cb_load_full)

        self.cb_suggestions = QCheckBox("Show Tracking Suggestions")
        self.cb_suggestions.setChecked(True)
        toolbar.addWidget(self.cb_suggestions)

        toolbar.addSeparator()

        self.btn_auto_scan = QPushButton("Auto Scan (Motion)")
        self.btn_auto_scan.clicked.connect(self.auto_scan_motion)
        toolbar.addWidget(self.btn_auto_scan)

        self.btn_auto_track = QPushButton("Auto Track (Propagate)")
        self.btn_auto_track.clicked.connect(self.auto_track)
        toolbar.addWidget(self.btn_auto_track)

        toolbar.addSeparator()

        self.btn_review = QPushButton("Review Groups")
        self.btn_review.clicked.connect(self.open_review_window)
        toolbar.addWidget(self.btn_review)

        self.btn_bulk = QPushButton("Bulk Actions")
        self.btn_bulk.clicked.connect(self.open_bulk_window)
        toolbar.addWidget(self.btn_bulk)

        toolbar.addSeparator()

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.export_dataset)
        self.btn_save.setStyleSheet("background-color: darkgreen; color: white;")
        toolbar.addWidget(self.btn_save)

        self.btn_train = QPushButton("Export YOLO Model")
        self.btn_train.clicked.connect(self.train_model)
        self.btn_train.setStyleSheet("background-color: darkblue; color: white;")
        toolbar.addWidget(self.btn_train)

        # Draw Tools Toolbar
        draw_toolbar = QToolBar("Drawing Tools")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, draw_toolbar)

        self.btn_grp = QButtonGroup(self)
        self.rad_rect = QRadioButton("Rectangle")
        self.rad_rect.setChecked(True)
        self.rad_poly = QRadioButton("Polygon")
        self.rad_auto = QRadioButton("Auto-Scale")

        self.btn_grp.addButton(self.rad_rect)
        self.btn_grp.addButton(self.rad_poly)
        self.btn_grp.addButton(self.rad_auto)

        draw_toolbar.addWidget(QLabel("<b>Drawing Tools</b>"))
        draw_toolbar.addWidget(self.rad_rect)
        draw_toolbar.addWidget(self.rad_poly)
        draw_toolbar.addWidget(self.rad_auto)

        self.rad_rect.toggled.connect(lambda: self.canvas.set_mode("rectangle") if self.rad_rect.isChecked() else None)
        self.rad_poly.toggled.connect(lambda: self.canvas.set_mode("polygon") if self.rad_poly.isChecked() else None)
        self.rad_auto.toggled.connect(lambda: self.canvas.set_mode("autoscale") if self.rad_auto.isChecked() else None)

        # Bottom Frame Controls
        frame_dock = QDockWidget("Frame Controls", self)
        frame_widget = QWidget()
        frame_layout = QVBoxLayout()

        # Playback row
        play_layout = QHBoxLayout()
        self.btn_play = QPushButton("▶ Play")
        self.btn_play.clicked.connect(self.toggle_play)

        self.btn_play_model = QPushButton("▶ Play with Model")
        self.btn_play_model.setStyleSheet("background-color: darkblue; color: white;")
        self.btn_play_model.clicked.connect(self.toggle_play_model)

        self.cb_auto_confirm = QCheckBox("Auto-Confirm Suggestions during Play")

        self.btn_confirm_sug = QPushButton("Confirm Suggestions (Enter)")
        self.btn_confirm_sug.setStyleSheet("background-color: darkcyan; color: white;")
        self.btn_confirm_sug.clicked.connect(self.confirm_suggestions)
        self.btn_confirm_sug.hide()

        play_layout.addWidget(self.btn_play)
        play_layout.addWidget(self.btn_play_model)
        play_layout.addWidget(self.cb_auto_confirm)
        play_layout.addWidget(self.btn_confirm_sug)
        play_layout.addStretch()

        # Scrubber row
        scrub_layout = QHBoxLayout()
        self.btn_prev = QPushButton("<<")
        self.btn_prev.clicked.connect(self.prev_frame)

        self.lbl_frame = QLabel("Frame: 0 / 0")

        self.btn_next = QPushButton(">>")
        self.btn_next.clicked.connect(self.next_frame)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.slider_moved)

        scrub_layout.addWidget(self.btn_prev)
        scrub_layout.addWidget(self.slider)
        scrub_layout.addWidget(self.lbl_frame)
        scrub_layout.addWidget(self.btn_next)

        frame_layout.addLayout(play_layout)
        frame_layout.addLayout(scrub_layout)

        frame_widget.setLayout(frame_layout)
        frame_dock.setWidget(frame_widget)

        # Timer for playback
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.advance_playback)
        self.is_playing = False
        self.is_playing_with_model = False
        self.cached_yolo_model = None
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, frame_dock)

        # Right Sidebar - Categories
        cat_dock = QDockWidget("Categories", self)
        cat_widget = QWidget()
        cat_layout = QVBoxLayout()

        self.list_categories = QListWidget()
        self.btn_add_cat = QPushButton("Add Category")
        self.btn_add_cat.clicked.connect(self.add_category)

        self.btn_change_cat = QPushButton("Change Class of Selected")
        self.btn_change_cat.clicked.connect(self.change_box_category)

        self.btn_delete_box = QPushButton("Delete Selected Box")
        self.btn_delete_box.clicked.connect(self.delete_box)

        self.btn_delete_cat = QPushButton("Delete Entire Category")
        self.btn_delete_cat.setStyleSheet("background-color: darkred; color: white;")
        self.btn_delete_cat.clicked.connect(self.delete_category)

        cat_layout.addWidget(QLabel("Select to draw or change:"))
        cat_layout.addWidget(self.list_categories)
        cat_layout.addWidget(self.btn_add_cat)
        cat_layout.addWidget(self.btn_change_cat)
        cat_layout.addWidget(self.btn_delete_box)
        cat_layout.addWidget(self.btn_delete_cat)
        cat_widget.setLayout(cat_layout)
        cat_dock.setWidget(cat_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, cat_dock)


    def start_project(self):
        dialog = StartupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.project_path:
            self.project_manager = ProjectManager(dialog.project_path)
            self.setWindowTitle(f"Video Annotator - {self.project_manager.get_project_name()}")
            self.update_category_list()
        else:
            sys.exit(0)

    def update_category_list(self):
        self.list_categories.clear()
        for i, name in sorted(self.project_manager.categories.items()):
            self.list_categories.addItem(f"{i}: {name}")

    def add_category(self):
        name, ok = QInputDialog.getText(self, "New Category", "Category Name:")
        if ok and name:
            self.project_manager.add_category(name)
            self.update_category_list()

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        if path:
            self.video_processor = VideoProcessor(path, self.cb_load_full.isChecked())
            self.slider.setMaximum(self.video_processor.total_frames - 1)
            self.current_frame_idx = 0
            self.show_frame()

    def show_frame(self):
        if not self.video_processor:
            return

        self.current_frame_data = self.video_processor.get_frame(self.current_frame_idx)
        if self.current_frame_data is not None:
            self.canvas.set_image(self.current_frame_data)

            # Draw existing annotations for this frame (hide if playing with model)
            if not getattr(self, 'is_playing_with_model', False) or not self.is_playing:
                frame_anns = self.annotations.get(self.current_frame_idx, [])
                self.canvas.draw_boxes(frame_anns, self.project_manager.categories)
            else:
                self.canvas.clear_boxes()

            # Draw suggestions if any
            if self.pending_suggestions:
                self.canvas.draw_suggestions(self.pending_suggestions, self.project_manager.categories)
                self.btn_confirm_sug.show()
            else:
                self.btn_confirm_sug.hide()

            self.lbl_frame.setText(f"Frame: {self.current_frame_idx} / {self.video_processor.total_frames - 1}")
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_frame_idx)
            self.slider.blockSignals(False)

    def confirm_suggestions(self):
        if not self.pending_suggestions:
            return

        if self.current_frame_idx not in self.annotations:
            self.annotations[self.current_frame_idx] = []

        for sug in self.pending_suggestions:
            self.annotations[self.current_frame_idx].append({'box': sug['box'], 'class_id': sug['class_id']})

        self.pending_suggestions = []
        self._save_current_frame_to_dataset()
        self.show_frame()

    def generate_suggestions(self):
        if not self.cb_suggestions.isChecked() or not self.video_processor:
            return

        # Clear old suggestions
        self.pending_suggestions = []

        # Skip generating OpenCV tracking suggestions if the current frame already has annotations,
        # BUT allow YOLO model predictions to run so we can visualize them.
        is_playing_model = getattr(self, 'is_playing_with_model', False) and self.is_playing
        if not is_playing_model and self.current_frame_idx in self.annotations and self.annotations[self.current_frame_idx]:
            return

        current_frame_img = self.video_processor.get_frame(self.current_frame_idx)
        if current_frame_img is None:
            return

        # 1. Try to use trained YOLO Model if running in "Play with Model" mode
        if getattr(self, 'is_playing_with_model', False):
            project_name = self.project_manager.get_project_name()
            best_model_path = self.project_manager.models_path / f"{project_name}_model" / "weights" / "best.pt"

            if best_model_path.exists():
                if self.cached_yolo_model is None:
                    from ultralytics import YOLO
                    self.cached_yolo_model = YOLO(str(best_model_path))

                # Predict
                results = self.cached_yolo_model(current_frame_img, verbose=False)

                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        # Convert xyxy to xywh
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        w = x2 - x1
                        h = y2 - y1
                        cls_id = int(box.cls[0].item())

                        self.pending_suggestions.append({'box': (int(x1), int(y1), int(w), int(h)), 'class_id': cls_id})
                return
            else:
                self._toggle_playback()
                QMessageBox.warning(self, "No Model Found", "Please train the YOLO model first by clicking 'Export YOLO Model'.")
                return

        # 2. Fallback to standard OpenCV CSRT tracking from previous consecutive frame
        prev_idx = self.current_frame_idx - 1
        if prev_idx >= 0 and prev_idx in self.annotations and self.annotations[prev_idx]:
            prev_frame = self.video_processor.get_frame(prev_idx)
            if prev_frame is not None:
                boxes = [ann['box'] for ann in self.annotations[prev_idx]]
                class_ids = [ann['class_id'] for ann in self.annotations[prev_idx]]

                self.tracker.init_trackers(prev_frame, boxes)
                new_boxes = self.tracker.update(current_frame_img)

                for idx, box in enumerate(new_boxes):
                    if box is not None:
                        self.pending_suggestions.append({'box': box, 'class_id': class_ids[idx]})

    def next_frame(self):
        if self.video_processor and self.current_frame_idx < self.video_processor.total_frames - 1:
            self.current_frame_idx += 1
            # Before showing, attempt to generate suggestions from the previous frame
            self.generate_suggestions()
            self.show_frame()

    def prev_frame(self):
        if self.video_processor and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.show_frame()

    def toggle_play(self):
        if not self.video_processor: return
        self.is_playing_with_model = False
        self._toggle_playback()

    def toggle_play_model(self):
        if not self.video_processor: return

        if not self.is_playing: # If we are about to start playing
            project_name = self.project_manager.get_project_name()
            best_model_path = self.project_manager.models_path / f"{project_name}_model" / "weights" / "best.pt"

            if not best_model_path.exists():
                QMessageBox.warning(self, "No Model Found", "Please train the YOLO model first by clicking 'Export YOLO Model'.")
                return

        self.is_playing_with_model = True
        self._toggle_playback()

    def _toggle_playback(self):
        if self.is_playing:
            self.play_timer.stop()
            self.is_playing = False
            self.btn_play.setText("▶ Play")
            self.btn_play_model.setText("▶ Play with Model")
        else:
            fps = self.video_processor.fps if self.video_processor.fps > 0 else 30
            self.play_timer.start(int(1000 / fps))
            self.is_playing = True
            if self.is_playing_with_model:
                self.btn_play_model.setText("⏸ Pause")
            else:
                self.btn_play.setText("⏸ Pause")

    def advance_playback(self):
        if self.video_processor and self.current_frame_idx < self.video_processor.total_frames - 1:
            self.next_frame()
            if self.cb_auto_confirm.isChecked() and self.pending_suggestions:
                self.confirm_suggestions()
        else:
            self._toggle_playback() # Stop at end

    def slider_moved(self, value):
        self.current_frame_idx = value
        self.show_frame()

    def get_selected_class_id(self):
        selected = self.list_categories.currentItem()
        if selected:
            text = selected.text()
            return int(text.split(":")[0])
        return 0 # Default to 0 if none selected

    def _save_current_frame_to_dataset(self):
        """Immediately exports the current frame's data to the YOLO folder (Auto-Save)."""
        if not self.video_processor or self.current_frame_data is None:
            return

        frame_idx = self.current_frame_idx
        anns = self.annotations.get(frame_idx, [])

        img_h, img_w = self.current_frame_data.shape[:2]
        yolo_anns = []

        for ann in anns:
            x, y, w, h = ann['box']
            x_center = (x + w / 2) / img_w
            y_center = (y + h / 2) / img_h
            norm_w = w / img_w
            norm_h = h / img_h

            yolo_anns.append({
                'class_id': ann['class_id'],
                'x_center': x_center,
                'y_center': y_center,
                'width': norm_w,
                'height': norm_h
            })

        img_name = f"frame_{frame_idx:06d}.jpg"
        self.project_manager.save_annotation(img_name, self.current_frame_data, yolo_anns)

    def on_box_drawn(self, box):
        class_id = self.get_selected_class_id()
        if self.current_frame_idx not in self.annotations:
            self.annotations[self.current_frame_idx] = []
        self.annotations[self.current_frame_idx].append({'box': box, 'class_id': class_id})
        self._save_current_frame_to_dataset()
        self.show_frame() # Refresh to show label

    def on_box_resized(self, index, new_box):
        if self.current_frame_idx in self.annotations and 0 <= index < len(self.annotations[self.current_frame_idx]):
            self.annotations[self.current_frame_idx][index]['box'] = new_box
            self._save_current_frame_to_dataset()
            self.show_frame()

    def undo_last_box(self):
        if self.current_frame_idx in self.annotations and self.annotations[self.current_frame_idx]:
            self.annotations[self.current_frame_idx].pop()
            self._save_current_frame_to_dataset()
            self.show_frame()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Z:
            self.undo_last_box()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            self.confirm_suggestions()
        super().keyPressEvent(event)

    def change_box_category(self):
        if self.current_frame_idx not in self.annotations or not self.annotations[self.current_frame_idx]:
            return

        selected_idx = self.canvas.get_selected_box_index()
        if selected_idx is not None and 0 <= selected_idx < len(self.annotations[self.current_frame_idx]):
            new_class_id = self.get_selected_class_id()
            self.annotations[self.current_frame_idx][selected_idx]['class_id'] = new_class_id
            self._save_current_frame_to_dataset()
            self.show_frame()
        else:
            QMessageBox.warning(self, "No Selection", "Please click on a bounding box to select it before changing its class.")

    def delete_box(self):
        if self.current_frame_idx not in self.annotations or not self.annotations[self.current_frame_idx]:
            return

        selected_idx = self.canvas.get_selected_box_index()
        if selected_idx is not None and 0 <= selected_idx < len(self.annotations[self.current_frame_idx]):
            self.annotations[self.current_frame_idx].pop(selected_idx)
            self._save_current_frame_to_dataset()
            self.show_frame()
            self.canvas.clear_selection()
        else:
            QMessageBox.warning(self, "No Selection", "Please click on a bounding box to select it before deleting.")

    def delete_category(self):
        selected_item = self.list_categories.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a category from the list to delete.")
            return

        class_id = int(selected_item.text().split(":")[0])
        class_name = self.project_manager.categories.get(class_id, "Unknown")

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to completely delete the category '{class_name}'? "
                                     f"This will remove ALL bounding boxes across ALL frames for this category.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from annotations
            for frame_idx, anns in self.annotations.items():
                self.annotations[frame_idx] = [a for a in anns if a.get('class_id') != class_id]

            # Remove from project manager and disk
            if class_id in self.project_manager.categories:
                del self.project_manager.categories[class_id]
                self.project_manager._save_yaml()
                self.project_manager.delete_exported_data_for_class(class_id)

            self.update_category_list()
            self.show_frame()
            QMessageBox.information(self, "Deleted", f"Category '{class_name}' completely removed.")

    def auto_scan_motion(self):
        if not self.video_processor:
            return

        progress = QProgressDialog("Scanning for motion...", "Cancel", 0, self.video_processor.total_frames, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        # Temporary dict to hold scan results
        temp_anns = {}

        for i in range(self.video_processor.total_frames):
            progress.setValue(i)
            QApplication.processEvents()

            if progress.wasCanceled():
                break

            frame = self.video_processor.get_frame(i)
            if frame is None:
                continue

            boxes = self.video_processor.detect_motion(frame)
            if boxes:
                temp_anns[i] = []
                for b in boxes:
                    temp_anns[i].append({'box': b, 'class_id': -1}) # -1 for unassigned

        progress.setValue(self.video_processor.total_frames)

        if not temp_anns:
            QMessageBox.information(self, "No Motion", "No moving objects detected.")
            return

        # Show review dialog for just the scanned items
        from ui.review import ReviewDialog
        dialog = ReviewDialog(self, custom_annotations=temp_anns, title="Review Auto Scan Results")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Merge assigned items into main annotations
            frames_to_save = set()
            for frame_idx, anns in temp_anns.items():
                for ann in anns:
                    # Only merge if it was assigned a valid category (not -1 and not deleted)
                    if ann['class_id'] != -1:
                        if frame_idx not in self.annotations:
                            self.annotations[frame_idx] = []
                        self.annotations[frame_idx].append(ann)
                        frames_to_save.add(frame_idx)

            # Auto-save the merged frames
            orig_idx = self.current_frame_idx
            for f_idx in frames_to_save:
                self.current_frame_idx = f_idx
                self.current_frame_data = self.video_processor.get_frame(f_idx)
                self._save_current_frame_to_dataset()
            self.current_frame_idx = orig_idx
            self.current_frame_data = self.video_processor.get_frame(orig_idx)

        self.show_frame()

    def auto_track(self):
        if not self.video_processor or self.current_frame_idx not in self.annotations:
            return

        current_anns = self.annotations[self.current_frame_idx]
        if not current_anns:
            return

        boxes = [ann['box'] for ann in current_anns]
        class_ids = [ann['class_id'] for ann in current_anns]

        self.tracker.init_trackers(self.current_frame_data, boxes)

        total_steps = self.video_processor.total_frames - self.current_frame_idx
        progress = QProgressDialog("Tracking objects...", "Cancel", 0, total_steps, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        step = 0
        for i in range(self.current_frame_idx + 1, self.video_processor.total_frames):
            progress.setValue(step)
            QApplication.processEvents()

            if progress.wasCanceled():
                break

            frame = self.video_processor.get_frame(i)
            if frame is None:
                break

            new_boxes = self.tracker.update(frame)

            if i not in self.annotations:
                self.annotations[i] = []

            for idx, box in enumerate(new_boxes):
                if box is not None:
                    self.annotations[i].append({'box': box, 'class_id': class_ids[idx]})
            step += 1

        progress.setValue(total_steps)
        self.show_frame()

    def open_review_window(self):
        from ui.review import ReviewDialog
        dialog = ReviewDialog(self)
        dialog.exec()
        self.show_frame() # Refresh in case classes changed

    def open_bulk_window(self):
        from ui.bulk_action import BulkActionDialog
        dialog = BulkActionDialog(self, self)
        dialog.exec()
        self.show_frame() # Refresh in case classes changed

    def export_dataset(self):
        if not self.video_processor:
            return

        total_items = len(self.annotations.items())
        if total_items == 0:
            QMessageBox.information(self, "Nothing to Export", "No annotations found.")
            return

        progress = QProgressDialog("Saving frames and annotations...", "Cancel", 0, total_items, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)

        step = 0
        for frame_idx, anns in self.annotations.items():
            progress.setValue(step)
            QApplication.processEvents()

            if progress.wasCanceled():
                break

            if not anns:
                step += 1
                continue

            frame = self.video_processor.get_frame(frame_idx)
            if frame is None:
                step += 1
                continue

            img_h, img_w = frame.shape[:2]

            # Convert annotations to YOLO format (normalized center x, center y, w, h)
            yolo_anns = []
            for ann in anns:
                x, y, w, h = ann['box']
                x_center = (x + w / 2) / img_w
                y_center = (y + h / 2) / img_h
                norm_w = w / img_w
                norm_h = h / img_h

                yolo_anns.append({
                    'class_id': ann['class_id'],
                    'x_center': x_center,
                    'y_center': y_center,
                    'width': norm_w,
                    'height': norm_h
                })

            img_name = f"frame_{frame_idx:06d}.jpg"
            self.project_manager.save_annotation(img_name, frame, yolo_anns)
            step += 1

        progress.setValue(total_items)
        QMessageBox.information(self, "Done", "Project dataset saved successfully.")

    def train_model(self):
        from training.yolo_trainer import YoloTrainer

        reply = QMessageBox.question(self, 'Export First?',
                                     'Do you want to save the latest annotations to the dataset before training?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.export_dataset()

        # Force a rewrite of data.yaml to ensure empty validation paths fallback safely
        self.project_manager._save_yaml()

        trainer = YoloTrainer(self.project_manager.project_path)

        epochs = QInputDialog.getInt(self, "Training Settings", "Number of Epochs to train:", value=10, min=1, max=1000)
        if not epochs[1]:
            return

        try:
            progress = QProgressDialog("Training YOLO Model...", "Cancel", 0, epochs[0], self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)

            def update_progress(current_epoch, total_epochs):
                progress.setValue(current_epoch)
                QApplication.processEvents()

            best_model = trainer.train(
                epochs=epochs[0],
                project_name=self.project_manager.get_project_name(),
                progress_callback=update_progress
            )

            # Invalidate cached model so next run uses freshly trained weights
            self.cached_yolo_model = None

            progress.setValue(epochs[0])
            QMessageBox.information(self, "Done", f"Training complete! Model saved to:\n{best_model}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Training failed:\n{str(e)}")
