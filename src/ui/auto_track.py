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
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QRadioButton, QButtonGroup,
                             QScrollArea, QWidget, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt

class AutoTrackDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auto-Track Settings")
        self.setMinimumWidth(300)
        self.categories = categories
        self.selected_categories = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel("Select categories to track:")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)

        # Radio buttons
        self.btn_grp = QButtonGroup(self)
        self.rad_all = QRadioButton("All Categories")
        self.rad_all.setChecked(True)
        self.rad_custom = QRadioButton("Custom Selection")

        self.btn_grp.addButton(self.rad_all)
        self.btn_grp.addButton(self.rad_custom)

        layout.addWidget(self.rad_all)
        layout.addWidget(self.rad_custom)

        # Checkboxes for custom selection
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()

        self.checkboxes = {}
        for class_id, name in sorted(self.categories.items()):
            cb = QCheckBox(f"{class_id}: {name}")
            cb.setEnabled(False) # Disabled by default since "All" is selected
            self.checkboxes[class_id] = cb
            self.scroll_layout.addWidget(cb)

        self.scroll_layout.addStretch()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_widget)

        layout.addWidget(self.scroll)

        # Toggle checkbox state based on radio button
        self.rad_all.toggled.connect(self._toggle_custom)
        self.rad_custom.toggled.connect(self._toggle_custom)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_start = QPushButton("Start Tracking")
        btn_start.setStyleSheet("background-color: darkblue; color: white;")
        btn_start.clicked.connect(self.accept_selection)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_start)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _toggle_custom(self):
        is_custom = self.rad_custom.isChecked()
        for cb in self.checkboxes.values():
            cb.setEnabled(is_custom)

    def accept_selection(self):
        if self.rad_all.isChecked():
            self.selected_categories = list(self.categories.keys())
        else:
            self.selected_categories = [cls_id for cls_id, cb in self.checkboxes.items() if cb.isChecked()]
            if not self.selected_categories:
                QMessageBox.warning(self, "No Selection", "Please select at least one category to track.")
                return

        self.accept()
