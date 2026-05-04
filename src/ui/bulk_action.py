from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt

class BulkActionDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Actions")
        self.setMinimumWidth(300)
        self.main_window = main_window
        self.project_manager = main_window.project_manager

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Frame Range
        range_layout = QHBoxLayout()
        self.spin_from = QSpinBox()
        self.spin_from.setRange(0, self.main_window.video_processor.total_frames - 1 if self.main_window.video_processor else 0)
        self.spin_to = QSpinBox()
        self.spin_to.setRange(0, self.main_window.video_processor.total_frames - 1 if self.main_window.video_processor else 0)
        self.spin_to.setValue(self.spin_to.maximum())

        range_layout.addWidget(QLabel("From Frame:"))
        range_layout.addWidget(self.spin_from)
        range_layout.addWidget(QLabel("To Frame:"))
        range_layout.addWidget(self.spin_to)
        layout.addLayout(range_layout)

        # Target Category (What to find)
        target_layout = QHBoxLayout()
        self.combo_target_cat = QComboBox()
        self.combo_target_cat.addItem("Any/All", -1)
        for i, name in sorted(self.project_manager.categories.items()):
            self.combo_target_cat.addItem(name, i)
        target_layout.addWidget(QLabel("Find boxes with Category:"))
        target_layout.addWidget(self.combo_target_cat)
        layout.addLayout(target_layout)

        layout.addWidget(QLabel("<hr>"))

        # Action: Move to Category
        move_layout = QHBoxLayout()
        self.combo_move_cat = QComboBox()
        for i, name in sorted(self.project_manager.categories.items()):
            self.combo_move_cat.addItem(name, i)
        btn_move = QPushButton("Move to Category")
        btn_move.clicked.connect(self.move_action)
        move_layout.addWidget(self.combo_move_cat)
        move_layout.addWidget(btn_move)
        layout.addLayout(move_layout)

        # Action: Delete
        btn_delete = QPushButton("Delete Matched Boxes")
        btn_delete.setStyleSheet("background-color: darkred; color: white;")
        btn_delete.clicked.connect(self.delete_action)
        layout.addWidget(btn_delete)

        self.setLayout(layout)

    def _get_matches(self):
        start = self.spin_from.value()
        end = self.spin_to.value()
        target_cat = self.combo_target_cat.currentData()

        matches = [] # List of tuples (frame_idx, box_idx)
        for frame_idx in range(start, end + 1):
            if frame_idx in self.main_window.annotations:
                for i, ann in enumerate(self.main_window.annotations[frame_idx]):
                    if target_cat == -1 or ann.get('class_id') == target_cat:
                        matches.append((frame_idx, i))
        return matches

    def move_action(self):
        matches = self._get_matches()
        if not matches:
            QMessageBox.information(self, "No Matches", "No boxes found matching criteria.")
            return

        new_cat = self.combo_move_cat.currentData()
        for frame_idx, box_idx in matches:
            self.main_window.annotations[frame_idx][box_idx]['class_id'] = new_cat

        QMessageBox.information(self, "Success", f"Moved {len(matches)} boxes to new category.")
        self.accept()

    def delete_action(self):
        matches = self._get_matches()
        if not matches:
            QMessageBox.information(self, "No Matches", "No boxes found matching criteria.")
            return

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to delete {len(matches)} boxes?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Delete in reverse order to not mess up indices
            # Group by frame first
            frame_deletes = {}
            for f_idx, b_idx in matches:
                if f_idx not in frame_deletes:
                    frame_deletes[f_idx] = []
                frame_deletes[f_idx].append(b_idx)

            for f_idx, b_indices in frame_deletes.items():
                b_indices.sort(reverse=True)
                for b_idx in b_indices:
                    self.main_window.annotations[f_idx].pop(b_idx)

            QMessageBox.information(self, "Deleted", f"Deleted {len(matches)} boxes.")
            self.accept()
