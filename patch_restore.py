import re

with open('src/ui/main_window.py', 'r') as f:
    content = f.read()

restore_func_old = """    def restore_project_images(self):
        train_path = self.project_manager.train_images_path
        if not train_path.exists():
            QMessageBox.information(self, "No Images", "No exported images found in the dataset to restore.")
            return

        # Discover subfolders representing media sources
        media_folders = [d.name for d in train_path.iterdir() if d.is_dir()]
        if not media_folders:
            # Fallback if no subfolders exist (legacy projects)
            if list(train_path.glob("*.jpg")):
                media_folders = ["(Root Directory)"]
            else:
                QMessageBox.information(self, "No Images", "No exported images found in the dataset to restore.")
                return

        # Ask user which media source to restore
        media_choice, ok = QInputDialog.getItem(self, "Select Media Source", "Choose the media source to restore:", media_folders, 0, False)
        if not ok:
            return

        target_img_dir = train_path if media_choice == "(Root Directory)" else train_path / media_choice
        target_lbl_dir = self.project_manager.train_labels_path if media_choice == "(Root Directory)" else self.project_manager.train_labels_path / media_choice

        # Ask overlay vs sequence
        reply_mode = QMessageBox.question(self, 'Restoration Mode',
                                     'Do you want to import these annotations back over the CURRENT loaded media? (Select Yes)\\n\\n'
                                     'Select No to just load the saved image crops as a standalone sequence.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        is_overlay = (reply_mode == QMessageBox.StandardButton.Yes)

        if is_overlay and not self.video_processor:
            QMessageBox.warning(self, "Error", "You must load a video/media file first before you can import annotations over it.")
            return

        valid_image_paths = sorted(target_img_dir.glob("*.jpg"))
        if not valid_image_paths:
            QMessageBox.information(self, "No Matches", "No images found in that source folder.")
            return

        if not is_overlay:
            from video.processor import ImageSequenceProcessor
            self.unload_media()
            self.video_processor = ImageSequenceProcessor(valid_image_paths)
            self.slider.setMaximum(self.video_processor.total_frames - 1)
            self.current_media_name = media_choice if media_choice != "(Root Directory)" else None

        # Repopulate annotations by reading .txt files and un-normalizing
        for idx, img_path in enumerate(valid_image_paths):
            label_file = target_lbl_dir / (img_path.stem + ".txt")

            # Determine the target frame index
            if is_overlay:
                try:
                    # Extract frame number from 'frame_000142.jpg'
                    target_idx = int(img_path.stem.split('_')[-1])
                except ValueError:
                    target_idx = idx
            else:
                target_idx = idx

            if label_file.exists():
                # We need image dimensions to un-normalize.
                # If overlaying, getting the actual frame is best.
                img_h, img_w = 640, 640 # safe fallback
                if is_overlay:
                    frame = self.video_processor.get_frame(target_idx)
                    if frame is not None:
                        img_h, img_w = frame.shape[:2]
                else:
                    import cv2
                    img = cv2.imread(str(img_path))
                    if img is not None:
                        img_h, img_w = img.shape[:2]

                self.annotations[target_idx] = []
                with open(label_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            x_c, y_c, nw, nh = map(float, parts[1:5])

                            w = nw * img_w
                            h = nh * img_h
                            x = (x_c * img_w) - (w / 2)
                            y = (y_c * img_h) - (h / 2)

                            self.annotations[target_idx].append({
                                'box': (int(x), int(y), int(w), int(h)),
                                'class_id': cls_id
                            })

        if is_overlay:
            self.show_frame()
            QMessageBox.information(self, "Success", "Annotations successfully overlaid onto the current media.")
        else:
            self.show_frame()
            QMessageBox.information(self, "Success", "Image sequence loaded with annotations.")"""


CategorySelectorDialog_code = """
class CategorySelectorDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Categories to Restore")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("Select which categories you want to restore:"))

        self.checkboxes = {}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)

        # Add "All" option
        self.cb_all = QCheckBox("Select All")
        self.cb_all.setChecked(True)
        self.cb_all.stateChanged.connect(self.toggle_all)
        scroll_layout.addWidget(self.cb_all)

        for cat_id, cat_name in categories.items():
            cb = QCheckBox(f"{cat_name} (ID: {cat_id})")
            cb.setChecked(True)
            self.checkboxes[cat_id] = cb
            scroll_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        self.layout.addLayout(btn_layout)

    def toggle_all(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        for cb in self.checkboxes.values():
            cb.setChecked(is_checked)

    def get_selected_ids(self):
        return [cat_id for cat_id, cb in self.checkboxes.items() if cb.isChecked()]
"""

restore_func_new = """    def restore_project_images(self):
        train_path = self.project_manager.train_images_path
        if not train_path.exists():
            QMessageBox.information(self, "No Images", "No exported images found in the dataset to restore.")
            return

        # Discover subfolders representing media sources
        media_folders = [d.name for d in train_path.iterdir() if d.is_dir()]
        if not media_folders:
            # Fallback if no subfolders exist (legacy projects)
            if list(train_path.glob("*.jpg")):
                media_folders = ["(Root Directory)"]
            else:
                QMessageBox.information(self, "No Images", "No exported images found in the dataset to restore.")
                return

        # Ask user which media source to restore
        media_choice, ok = QInputDialog.getItem(self, "Select Media Source", "Choose the media source to restore:", media_folders, 0, False)
        if not ok:
            return

        target_img_dir = train_path if media_choice == "(Root Directory)" else train_path / media_choice
        target_lbl_dir = self.project_manager.train_labels_path if media_choice == "(Root Directory)" else self.project_manager.train_labels_path / media_choice

        # Ask overlay vs sequence
        reply_mode = QMessageBox.question(self, 'Restoration Mode',
                                     'Do you want to import these annotations back over the CURRENT loaded media? (Select Yes)\\n\\n'
                                     'Select No to just load the saved image crops as a standalone sequence.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        is_overlay = (reply_mode == QMessageBox.StandardButton.Yes)

        if is_overlay and not self.video_processor:
            QMessageBox.warning(self, "Error", "You must load a video/media file first before you can import annotations over it.")
            return

        valid_image_paths = sorted(target_img_dir.glob("*.jpg"))
        if not valid_image_paths:
            QMessageBox.information(self, "No Matches", "No images found in that source folder.")
            return

        # Ask user which categories to restore
        dialog = CategorySelectorDialog(self.project_manager.categories, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected_cat_ids = dialog.get_selected_ids()
        if not selected_cat_ids:
            QMessageBox.information(self, "No Categories", "No categories selected for restoration.")
            return

        if not is_overlay:
            from video.processor import ImageSequenceProcessor
            self.unload_media()
            self.video_processor = ImageSequenceProcessor(valid_image_paths)
            self.slider.setMaximum(self.video_processor.total_frames - 1)
            self.current_media_name = media_choice if media_choice != "(Root Directory)" else None

        # Repopulate annotations by reading .txt files and un-normalizing
        for idx, img_path in enumerate(valid_image_paths):
            label_file = target_lbl_dir / (img_path.stem + ".txt")

            # Determine the target frame index
            if is_overlay:
                try:
                    # Extract frame number from 'frame_000142.jpg'
                    target_idx = int(img_path.stem.split('_')[-1])
                except ValueError:
                    target_idx = idx
            else:
                target_idx = idx

            if label_file.exists():
                # We need image dimensions to un-normalize.
                # If overlaying, getting the actual frame is best.
                img_h, img_w = 640, 640 # safe fallback
                if is_overlay:
                    frame = self.video_processor.get_frame(target_idx)
                    if frame is not None:
                        img_h, img_w = frame.shape[:2]
                else:
                    import cv2
                    img = cv2.imread(str(img_path))
                    if img is not None:
                        img_h, img_w = img.shape[:2]

                if target_idx not in self.annotations:
                    self.annotations[target_idx] = []

                with open(label_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])

                            # Only restore selected categories
                            if cls_id not in selected_cat_ids:
                                continue

                            x_c, y_c, nw, nh = map(float, parts[1:5])

                            w = nw * img_w
                            h = nh * img_h
                            x = (x_c * img_w) - (w / 2)
                            y = (y_c * img_h) - (h / 2)

                            self.annotations[target_idx].append({
                                'box': (int(x), int(y), int(w), int(h)),
                                'class_id': cls_id
                            })

        if is_overlay:
            self.show_frame()
            QMessageBox.information(self, "Success", "Annotations successfully overlaid onto the current media.")
        else:
            self.show_frame()
            QMessageBox.information(self, "Success", "Image sequence loaded with annotations.")"""

if restore_func_old in content:
    content = content.replace(restore_func_old, restore_func_new)
    content = content + "\n\n" + CategorySelectorDialog_code + "\n"
    with open('src/ui/main_window.py', 'w') as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find restore_func_old in content")
