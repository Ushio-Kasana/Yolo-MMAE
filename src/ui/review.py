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

        btn_apply = QPushButton("Apply to All")
        btn_apply.clicked.connect(self.apply_to_all)

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
            w = QWidget()
            l = QVBoxLayout()
            w.setLayout(l)

            # Convert crop to QPixmap
            crop = item['crop']
            h, wid, ch = crop.shape
            bytes_per_line = ch * wid
            q_img = QImage(crop.data.tobytes(), wid, h, bytes_per_line, QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)

            img_lbl = QLabel()
            img_lbl.setPixmap(pixmap)
            l.addWidget(img_lbl)

            # Label info
            class_name = self.project_manager.categories.get(item['class_id'], "Unknown")
            info_lbl = QLabel(f"Frame {item['frame_idx']} - {class_name}")
            l.addWidget(info_lbl)

            self.grid.addWidget(w, row, col)

    def apply_to_all(self):
        new_class_id = self.combo_category.currentData()
        if new_class_id is None:
            return

        for item in self.items:
            # Update local memory
            item['class_id'] = new_class_id

            # Update main window annotations
            self.main_window.annotations[item['frame_idx']][item['ann_idx']]['class_id'] = new_class_id

        self.populate_grid()
