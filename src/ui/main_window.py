import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QToolBar,
                             QDockWidget, QListWidget, QInputDialog, QMessageBox,
                             QCheckBox, QSlider, QDialog)
from PyQt6.QtCore import Qt, QTimer
import cv2

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

        # Top Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.btn_load_video = QPushButton("Load Video")
        self.btn_load_video.clicked.connect(self.load_video)
        toolbar.addWidget(self.btn_load_video)

        self.cb_load_full = QCheckBox("Load Full Video")
        toolbar.addWidget(self.cb_load_full)

        toolbar.addSeparator()

        self.btn_auto_scan = QPushButton("Auto Scan (Motion)")
        self.btn_auto_scan.clicked.connect(self.auto_scan_motion)
        toolbar.addWidget(self.btn_auto_scan)

        self.btn_auto_track = QPushButton("Auto Track (Propagate)")
        self.btn_auto_track.clicked.connect(self.auto_track)
        toolbar.addWidget(self.btn_auto_track)

        toolbar.addSeparator()

        self.btn_train = QPushButton("Train YOLO Model")
        self.btn_train.clicked.connect(self.train_model)
        toolbar.addWidget(self.btn_train)

        self.btn_review = QPushButton("Review Groups")
        self.btn_review.clicked.connect(self.open_review_window)
        toolbar.addWidget(self.btn_review)

        # Bottom Frame Controls
        frame_dock = QDockWidget("Frame Controls", self)
        frame_widget = QWidget()
        frame_layout = QHBoxLayout()

        self.btn_prev = QPushButton("<< Prev Frame")
        self.btn_prev.clicked.connect(self.prev_frame)
        self.lbl_frame = QLabel("Frame: 0 / 0")
        self.btn_next = QPushButton("Next Frame >>")
        self.btn_next.clicked.connect(self.next_frame)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.slider_moved)

        frame_layout.addWidget(self.btn_prev)
        frame_layout.addWidget(self.slider)
        frame_layout.addWidget(self.lbl_frame)
        frame_layout.addWidget(self.btn_next)
        frame_widget.setLayout(frame_layout)
        frame_dock.setWidget(frame_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, frame_dock)

        # Right Sidebar - Categories
        cat_dock = QDockWidget("Categories", self)
        cat_widget = QWidget()
        cat_layout = QVBoxLayout()

        self.list_categories = QListWidget()
        self.btn_add_cat = QPushButton("Add Category")
        self.btn_add_cat.clicked.connect(self.add_category)

        self.btn_delete_box = QPushButton("Delete Selected Box")
        self.btn_delete_box.clicked.connect(self.delete_box)

        cat_layout.addWidget(self.list_categories)
        cat_layout.addWidget(self.btn_add_cat)
        cat_layout.addWidget(self.btn_delete_box)
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

            # Draw existing annotations for this frame
            boxes = [ann['box'] for ann in self.annotations.get(self.current_frame_idx, [])]
            self.canvas.draw_boxes(boxes)

            self.lbl_frame.setText(f"Frame: {self.current_frame_idx} / {self.video_processor.total_frames - 1}")
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_frame_idx)
            self.slider.blockSignals(False)

    def next_frame(self):
        if self.video_processor and self.current_frame_idx < self.video_processor.total_frames - 1:
            self.current_frame_idx += 1
            self.show_frame()

    def prev_frame(self):
        if self.video_processor and self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.show_frame()

    def slider_moved(self, value):
        self.current_frame_idx = value
        self.show_frame()

    def get_selected_class_id(self):
        selected = self.list_categories.currentItem()
        if selected:
            text = selected.text()
            return int(text.split(":")[0])
        return 0 # Default to 0 if none selected

    def on_box_drawn(self, box):
        class_id = self.get_selected_class_id()
        if self.current_frame_idx not in self.annotations:
            self.annotations[self.current_frame_idx] = []
        self.annotations[self.current_frame_idx].append({'box': box, 'class_id': class_id})

    def delete_box(self):
        # For simplicity, if we had tracking of selected box, we'd remove it.
        # This basic implementation clears all boxes on current frame
        if self.current_frame_idx in self.annotations:
            self.annotations[self.current_frame_idx] = []
            self.canvas.clear_boxes()

    def auto_scan_motion(self):
        if not self.video_processor:
            return

        QMessageBox.information(self, "Auto Scan", "Scanning for motion. This may take a moment.")

        for i in range(self.video_processor.total_frames):
            frame = self.video_processor.get_frame(i)
            if frame is None:
                continue

            boxes = self.video_processor.detect_motion(frame)
            if boxes:
                if i not in self.annotations:
                    self.annotations[i] = []
                for b in boxes:
                    self.annotations[i].append({'box': b, 'class_id': 0}) # default class

        self.show_frame()
        QMessageBox.information(self, "Done", "Auto scan complete. Please review and assign categories.")

    def auto_track(self):
        if not self.video_processor or self.current_frame_idx not in self.annotations:
            return

        current_anns = self.annotations[self.current_frame_idx]
        if not current_anns:
            return

        boxes = [ann['box'] for ann in current_anns]
        class_ids = [ann['class_id'] for ann in current_anns]

        self.tracker.init_trackers(self.current_frame_data, boxes)

        QMessageBox.information(self, "Tracking", "Tracking objects through remaining frames...")

        for i in range(self.current_frame_idx + 1, self.video_processor.total_frames):
            frame = self.video_processor.get_frame(i)
            if frame is None:
                break

            new_boxes = self.tracker.update(frame)

            if i not in self.annotations:
                self.annotations[i] = []

            for idx, box in enumerate(new_boxes):
                if box is not None:
                    self.annotations[i].append({'box': box, 'class_id': class_ids[idx]})

        self.show_frame()
        QMessageBox.information(self, "Done", "Tracking complete.")

    def open_review_window(self):
        from ui.review import ReviewDialog
        dialog = ReviewDialog(self, self)
        dialog.exec()
        self.show_frame() # Refresh in case classes changed

    def export_dataset(self):
        if not self.video_processor:
            return

        QMessageBox.information(self, "Exporting", "Saving frames and annotations to dataset...")

        for frame_idx, anns in self.annotations.items():
            if not anns:
                continue

            frame = self.video_processor.get_frame(frame_idx)
            if frame is None:
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

        QMessageBox.information(self, "Done", "Dataset exported successfully.")

    def train_model(self):
        from training.yolo_trainer import YoloTrainer

        reply = QMessageBox.question(self, 'Export First?',
                                     'Do you want to export current annotations to the dataset before training?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.export_dataset()

        trainer = YoloTrainer(self.project_manager.project_path)
        try:
            QMessageBox.information(self, "Training", "Training started. Check console for progress.")
            # Note: Training blocks the UI in this basic implementation.
            # For a production app, this should run in a QThread.
            best_model = trainer.train(epochs=5, project_name=self.project_manager.get_project_name())
            QMessageBox.information(self, "Done", f"Training complete! Model saved to:\n{best_model}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Training failed:\n{str(e)}")
