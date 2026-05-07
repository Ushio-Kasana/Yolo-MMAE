# YOLO-MMAE - Video Annotator & Auto-Tracker
# Copyright (C) 2026  Ushio-Kasana
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QScrollArea, QWidget,
                             QGridLayout, QLabel, QPushButton, QHBoxLayout,
                             QComboBox, QInputDialog)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import cv2

class ReviewDialog(QDialog):
    def __init__(self, main_window, custom_annotations=None, title="Review Detected Objects", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        self.main_window = main_window
        self.custom_annotations = custom_annotations
        self.annotations = custom_annotations if custom_annotations is not None else main_window.annotations
        self.video_processor = main_window.video_processor
        self.project_manager = main_window.project_manager

        # Build dataset of crops
        # items will be list of dicts: {'frame_idx': int, 'ann_idx': int, 'crop': cv2_image, 'class_id': int, 'delete': False}
        self.items = []
        self._extract_crops()

        self.last_selected_index = None

        self.init_ui()

    def _extract_crops(self):
        if not self.video_processor:
            return

        for frame_idx, anns in self.annotations.items():
            if not anns:
                continue

            frame = self.video_processor.get_frame(frame_idx)
            if frame is None:
                continue

            for i, ann in enumerate(anns):
                x, y, w, h = ann['box']
                # Ensure bounds
                x, y = max(0, x), max(0, y)
                img_h, img_w = frame.shape[:2]
                x2, y2 = min(img_w, x + w), min(img_h, y + h)

                if x2 > x and y2 > y:
                    crop = frame[y:y2, x:x2]
                    self.items.append({
                        'frame_idx': frame_idx,
                        'ann_idx': i,
                        'crop': crop,
                        'class_id': ann['class_id']
                    })

    def init_ui(self):
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()
        lbl = QLabel("Assign selected to:")
        self.combo_category = QComboBox()

        # Add an "Unknown" option for auto scan flexibility
        self.combo_category.addItem("Unknown / Pending", -1)
        for i, name in sorted(self.project_manager.categories.items()):
            self.combo_category.addItem(name, i)

        self.btn_new_cat = QPushButton("+ New")
        self.btn_new_cat.clicked.connect(self.add_new_category)

        btn_apply = QPushButton("Apply to Selected")
        btn_apply.clicked.connect(self.apply_to_selected)

        btn_delete = QPushButton("Delete Selected")
        btn_delete.setStyleSheet("background-color: darkred; color: white;")
        btn_delete.clicked.connect(self.delete_selected)

        controls_layout.addWidget(lbl)
        controls_layout.addWidget(self.combo_category)
        controls_layout.addWidget(self.btn_new_cat)
        controls_layout.addWidget(btn_apply)
        controls_layout.addWidget(btn_delete)
        controls_layout.addStretch()

        if self.custom_annotations is not None:
            btn_finish = QPushButton("Commit Scan to Project")
            btn_finish.setStyleSheet("background-color: darkgreen; color: white;")
            btn_finish.clicked.connect(self.accept)
            controls_layout.addWidget(btn_finish)

        layout.addLayout(controls_layout)

        # Scroll Area for Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_widget = QWidget()
        self.grid = QGridLayout()
        grid_widget.setLayout(self.grid)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        self.populate_grid()
        self.setLayout(layout)

    def populate_grid(self):
        # Clear existing
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        cols = 4
        for idx, item in enumerate(self.items):
            row = idx // cols
            col = idx % cols

            # Create a small widget for each crop
            w = CropWidget(item, idx, self)
            self.grid.addWidget(w, row, col)

    def handle_widget_click(self, clicked_idx, shift_pressed):
        if shift_pressed and self.last_selected_index is not None:
            # Select range
            start = min(self.last_selected_index, clicked_idx)
            end = max(self.last_selected_index, clicked_idx)

            # Find the state we are trying to set (based on the widget just clicked)
            # Actually, standard behavior is to just set everything in range to True
            for i in range(self.grid.count()):
                widget = self.grid.itemAt(i).widget()
                if isinstance(widget, CropWidget):
                    if start <= widget.grid_index <= end:
                        widget.set_selected(True)
        else:
            # Normal click was already handled by the widget itself, just update last index
            self.last_selected_index = clicked_idx

    def add_new_category(self):
        name, ok = QInputDialog.getText(self, "New Category", "Category Name:")
        if ok and name:
            new_id = self.project_manager.add_category(name)
            # Add to combobox and select it
            self.combo_category.addItem(name, new_id)
            index = self.combo_category.findData(new_id)
            if index != -1:
                self.combo_category.setCurrentIndex(index)
            # Update main window list
            self.main_window.update_category_list()

    def delete_selected(self):
        frames_to_save = set()
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if isinstance(widget, CropWidget) and widget.is_selected:
                widget.item['delete'] = True
                item = widget.item
                # If we're working on the main annotations, remove it from there directly
                if self.custom_annotations is None:
                    # Mark the annotation in the main dictionary with a class_id of -1 so we can pop it safely
                    self.annotations[item['frame_idx']][item['ann_idx']]['class_id'] = -1
                    frames_to_save.add(item['frame_idx'])
                else:
                    # In custom/temp annotations (auto scan), just keep it as -1 so it's ignored on commit
                    self.annotations[item['frame_idx']][item['ann_idx']]['class_id'] = -1

        # Remove items flagged for deletion from UI
        self.items = [item for item in self.items if not item.get('delete', False)]

        # Cleanup main annotations if applicable
        if self.custom_annotations is None:
            for frame_idx in frames_to_save:
                self.annotations[frame_idx] = [a for a in self.annotations[frame_idx] if a['class_id'] != -1]

                # Autosave
                orig_idx = self.main_window.current_frame_idx
                self.main_window.current_frame_idx = frame_idx
                self.main_window.current_frame_data = self.video_processor.get_frame(frame_idx)
                self.main_window._save_current_frame_to_dataset()
                self.main_window.current_frame_idx = orig_idx
                self.main_window.current_frame_data = self.video_processor.get_frame(orig_idx)

        # Re-index remaining items so ann_idx stays accurate for future apply/delete ops
        for frame_idx in frames_to_save:
            frame_items = [item for item in self.items if item['frame_idx'] == frame_idx]
            # Since self.annotations[frame_idx] was filtered, we just match the new index sequentially
            for new_idx, item in enumerate(frame_items):
                item['ann_idx'] = new_idx

        self.populate_grid()

    def apply_to_selected(self):
        new_class_id = self.combo_category.currentData()
        if new_class_id is None:
            return

        # Find all selected CropWidgets
        frames_to_save = set()
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if isinstance(widget, CropWidget) and widget.is_selected:
                item = widget.item
                item['class_id'] = new_class_id
                self.annotations[item['frame_idx']][item['ann_idx']]['class_id'] = new_class_id
                frames_to_save.add(item['frame_idx'])
                widget.is_selected = False

        # Trigger autosave for modified frames only if working on main annotations
        if self.custom_annotations is None:
            for frame_idx in frames_to_save:
                orig_idx = self.main_window.current_frame_idx
                self.main_window.current_frame_idx = frame_idx
                self.main_window.current_frame_data = self.video_processor.get_frame(frame_idx)
                self.main_window._save_current_frame_to_dataset()
                self.main_window.current_frame_idx = orig_idx
                self.main_window.current_frame_data = self.video_processor.get_frame(orig_idx)

        # Repopulate to reflect changes
        self.populate_grid()

class CropWidget(QWidget):
    def __init__(self, item, grid_index, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.item = item
        self.grid_index = grid_index
        self.is_selected = False

        # Required for QWidget subclasses to paint custom CSS backgrounds/borders
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Style
        self.setStyleSheet("CropWidget { border: 2px solid transparent; }")

        # Convert crop to QPixmap
        crop = item['crop']
        h, wid, ch = crop.shape
        bytes_per_line = ch * wid
        q_img = QImage(crop.data.tobytes(), wid, h, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)

        self.img_lbl = QLabel()
        self.img_lbl.setPixmap(pixmap)
        self.layout.addWidget(self.img_lbl)

        # Label info
        # Assuming parent is ReviewDialog and has project_manager
        pm = parent.project_manager if hasattr(parent, 'project_manager') else None
        class_name = pm.categories.get(item['class_id'], "Unknown") if pm else "Unknown"
        self.info_lbl = QLabel(f"F{item['frame_idx']} - {class_name}")
        self.layout.addWidget(self.info_lbl)

    def set_selected(self, state):
        self.is_selected = state
        if self.is_selected:
            # Check if OS is in Light Mode or Dark Mode by comparing window text vs base color luminance
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QPalette
            palette = QApplication.palette()
            bg_color = palette.color(QPalette.ColorRole.Window).lightness()

            # If background is bright, it's light mode, use black border
            if bg_color > 128:
                self.setStyleSheet("CropWidget { border: 3px solid black; background-color: rgba(0, 0, 0, 50); }")
            else:
                self.setStyleSheet("CropWidget { border: 3px solid white; background-color: rgba(255, 255, 255, 50); }")
        else:
            self.setStyleSheet("CropWidget { border: 2px solid transparent; background-color: transparent; }")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            shift_pressed = (event.modifiers() == Qt.KeyboardModifier.ShiftModifier)

            if not shift_pressed:
                self.set_selected(not self.is_selected)

            if self.parent_dialog and hasattr(self.parent_dialog, 'handle_widget_click'):
                self.parent_dialog.handle_widget_click(self.grid_index, shift_pressed)

        super().mousePressEvent(event)
