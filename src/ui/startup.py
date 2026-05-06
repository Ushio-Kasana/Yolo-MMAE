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
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                             QFileDialog, QHBoxLayout, QMessageBox)

class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Video Annotator")
        self.setMinimumWidth(400)

        self.project_path = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Video Object Tracking & Annotation")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Create a new project or open an existing one to begin.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_layout = QHBoxLayout()

        new_btn = QPushButton("Create New Project")
        new_btn.clicked.connect(self.create_project)

        open_btn = QPushButton("Open Existing Project")
        open_btn.clicked.connect(self.open_project)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def create_project(self):
        path = QFileDialog.getExistingDirectory(self, "Select Empty Directory for New Project")
        if path:
            # Check if directory is mostly empty
            if os.listdir(path):
                reply = QMessageBox.question(self, "Directory Not Empty",
                                             "The selected directory is not empty. Continue anyway?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
            self.project_path = path
            self.accept()

    def open_project(self):
        path = QFileDialog.getExistingDirectory(self, "Select Existing Project Directory")
        if path:
            self.project_path = path
            self.accept()
