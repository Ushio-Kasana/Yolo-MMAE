import os
import yaml
import shutil
from pathlib import Path

class ProjectManager:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dataset_path = self.project_path / "dataset"
        self.models_path = self.project_path / "models"

        self.images_path = self.dataset_path / "images"
        self.labels_path = self.dataset_path / "labels"

        self.train_images_path = self.images_path / "train"
        self.train_labels_path = self.labels_path / "train"
        self.val_images_path = self.images_path / "val"
        self.val_labels_path = self.labels_path / "val"

        self.yaml_path = self.dataset_path / "data.yaml"

        # Categories mapping: class_id -> class_name
        self.categories = {}

        self._ensure_structure()
        self.load_categories()

    def _ensure_structure(self):
        """Creates the required YOLO folder structure if it doesn't exist."""
        directories = [
            self.project_path,
            self.dataset_path,
            self.models_path,
            self.images_path,
            self.labels_path,
            self.train_images_path,
            self.train_labels_path,
            self.val_images_path,
            self.val_labels_path
        ]

        for d in directories:
            d.mkdir(parents=True, exist_ok=True)

        if not self.yaml_path.exists():
            self._save_yaml()

    def _save_yaml(self):
        """Saves the data.yaml file required by YOLO."""
        # Fix YOLO class ID out-of-bounds error when categories are deleted.
        # Ensure 'names' map aligns strictly with keys as indices.
        max_idx = max(self.categories.keys(), default=-1)
        names_list = []
        for i in range(max_idx + 1):
            names_list.append(self.categories.get(i, f"deleted_class_{i}"))

        # Check if validation images actually exist; if not, fallback to training images
        # to prevent YOLO from crashing due to an empty dataset split.
        # Ignore hidden files like .DS_Store
        val_path = str(self.val_images_path.absolute())
        has_val_images = any(f.is_file() and not f.name.startswith('.') for f in self.val_images_path.iterdir())

        if not has_val_images:
            val_path = str(self.train_images_path.absolute())

        data = {
            'train': str(self.train_images_path.absolute()),
            'val': val_path,
            'nc': len(names_list),
            'names': names_list
        }

        with open(self.yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def load_categories(self):
        """Loads categories from data.yaml."""
        if self.yaml_path.exists():
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                if data and 'names' in data:
                    self.categories = {i: name for i, name in enumerate(data['names'])}

    def add_category(self, name: str) -> int:
        """Adds a new category and updates data.yaml. Returns the class ID."""
        if name in self.categories.values():
            # Return existing ID
            for k, v in self.categories.items():
                if v == name:
                    return k

        new_id = max(self.categories.keys(), default=-1) + 1
        self.categories[new_id] = name
        self._save_yaml()
        return new_id

    def get_category_id(self, name: str) -> int:
        """Gets ID for category name, returns -1 if not found."""
        for k, v in self.categories.items():
            if v == name:
                return k
        return -1

    def save_annotation(self, image_name: str, image_data, annotations: list):
        """
        Saves image and its YOLO annotations.
        image_name: base name (e.g., 'frame_001.jpg')
        image_data: numpy array from OpenCV
        annotations: list of dicts {'class_id': int, 'x_center': float, 'y_center': float, 'width': float, 'height': float}
        """
        import cv2

        # Save image (defaulting to train split for now)
        img_file = self.train_images_path / image_name
        cv2.imwrite(str(img_file), image_data)

        # Save label
        txt_name = image_name.rsplit('.', 1)[0] + '.txt'
        label_file = self.train_labels_path / txt_name

        with open(label_file, 'w') as f:
            for ann in annotations:
                f.write(f"{ann['class_id']} {ann['x_center']} {ann['y_center']} {ann['width']} {ann['height']}\n")

    def delete_exported_data_for_class(self, class_id: int):
        """Removes all annotations matching class_id from existing .txt files on disk."""
        if not self.train_labels_path.exists():
            return

        for label_file in self.train_labels_path.glob("*.txt"):
            lines = []
            with open(label_file, 'r') as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if parts and int(parts[0]) != class_id:
                    new_lines.append(line)

            with open(label_file, 'w') as f:
                f.writelines(new_lines)

    def get_project_name(self):
        return self.project_path.name
