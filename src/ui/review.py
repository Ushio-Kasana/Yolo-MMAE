from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QScrollArea, QWidget,
                             QGridLayout, QLabel, QPushButton, QHBoxLayout,
                             QComboBox)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import cv2

class ReviewDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Detected Objects")
        self.resize(800, 600)

        self.main_window = main_window
        self.annotations = main_window.annotations
        self.video_processor = main_window.video_processor
        self.project_manager = main_window.project_manager

        # Build dataset of crops
        # items will be list of dicts: {'frame_idx': int, 'ann_idx': int, 'crop': cv2_image, 'class_id': int}
        self.items = []
        self._extract_crops()

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
        for i, name in sorted(self.project_manager.categories.items()):
            self.combo_category.addItem(name, i)

        btn_apply = QPushButton("Apply to Selected")
        btn_apply.clicked.connect(self.apply_to_selected)

        controls_layout.addWidget(lbl)
        controls_layout.addWidget(self.combo_category)
        controls_layout.addWidget(btn_apply)
        controls_layout.addStretch()
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
            w = CropWidget(item, self)
            self.grid.addWidget(w, row, col)

    def apply_to_selected(self):
        new_class_id = self.combo_category.currentData()
        if new_class_id is None:
            return

        # Find all selected CropWidgets
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if isinstance(widget, CropWidget) and widget.is_selected:
                item = widget.item
                item['class_id'] = new_class_id
                self.main_window.annotations[item['frame_idx']][item['ann_idx']]['class_id'] = new_class_id

        # Repopulate to reflect changes
        self.populate_grid()

class CropWidget(QWidget):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self.is_selected = False

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selected = not self.is_selected
            if self.is_selected:
                self.setStyleSheet("CropWidget { border: 2px solid blue; background-color: lightblue; }")
            else:
                self.setStyleSheet("CropWidget { border: 2px solid transparent; background-color: transparent; }")
        super().mousePressEvent(event)
