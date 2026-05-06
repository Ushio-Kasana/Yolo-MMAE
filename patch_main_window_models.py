import re

with open('src/ui/main_window.py', 'r') as f:
    content = f.read()

btn_load_video_old = """        self.btn_load_video = QPushButton("Load Video")
        self.btn_load_video.clicked.connect(self.load_video)
        toolbar.addWidget(self.btn_load_video)"""

btn_load_video_new = """        self.btn_load_video = QPushButton("Load Video")
        self.btn_load_video.clicked.connect(self.load_video)
        toolbar.addWidget(self.btn_load_video)

        self.btn_import_model = QPushButton("Import Model")
        self.btn_import_model.clicked.connect(self.import_external_model)
        self.btn_import_model.setStyleSheet("color: blue;")
        self.btn_import_model.setToolTip("Import a .pt model from another project to use with 'Play with Model'")
        toolbar.addWidget(self.btn_import_model)"""

content = content.replace(btn_load_video_old, btn_load_video_new)


train_model_old = """        reply_pretrained = QMessageBox.question(self, 'Training Base',
                                     'Do you want to use a pre-trained base model? (Recommended for speed and accuracy).\\n\\nSelect "No" to train completely from scratch.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        use_pretrained = (reply_pretrained == QMessageBox.StandardButton.Yes)"""

train_model_new = """        reply_pretrained = QMessageBox.question(self, 'Training Base',
                                     'Do you want to use a pre-trained base model? (Recommended for speed and accuracy).\\n\\nSelect "No" to train completely from scratch.\\nSelect "Cancel" to pick a specific .pt file to resume training from.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

        if reply_pretrained == QMessageBox.StandardButton.Cancel:
            path, _ = QFileDialog.getOpenFileName(self, "Select Model to Resume Training", "", "PyTorch Models (*.pt)")
            if not path:
                return # User cancelled file selection
            use_pretrained = path
        else:
            use_pretrained = (reply_pretrained == QMessageBox.StandardButton.Yes)"""

content = content.replace(train_model_old, train_model_new)


import_func = """
    def import_external_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import External Model", "", "PyTorch Models (*.pt)")
        if not path:
            return

        import shutil
        from pathlib import Path

        project_name = self.project_manager.get_project_name()
        weights_dir = self.project_manager.models_path / f"{project_name}_model" / "weights"
        weights_dir.mkdir(parents=True, exist_ok=True)

        dest_path = weights_dir / "best.pt"

        try:
            shutil.copy2(path, dest_path)
            self.cached_yolo_model = None # Invalidate cache so new model loads
            QMessageBox.information(self, "Success", "Model imported successfully. You can now use 'Play with Model'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import model: {e}")
"""

content = re.sub(r'(\s+def train_model\(self\):)', import_func + r'\n\1', content)

with open('src/ui/main_window.py', 'w') as f:
    f.write(content)
