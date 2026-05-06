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
import sys
from pathlib import Path
from ultralytics import YOLO

class YoloTrainer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dataset_path = self.project_path / "dataset"
        self.yaml_path = self.dataset_path / "data.yaml"
        self.models_path = self.project_path / "models"

        self.models_path.mkdir(parents=True, exist_ok=True)

    def train(self, epochs=10, imgsz=640, project_name="my_project", progress_callback=None, pretrained=True, device='cpu', batch_size=16, workers=8):
        """
        Trains YOLOv8 model on the saved dataset.
        Returns the path to the best trained model weights.
        """
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Dataset YAML not found at {self.yaml_path}")

        # Start from pretrained weights or from scratch (yaml config)
        model_target = 'yolov8n.pt' if pretrained else 'yolov8n.yaml'
        model = YOLO(model_target)

        # Inject custom callback if provided
        if progress_callback:
            def on_fit_epoch_end(trainer):
                progress_callback(trainer.epoch, trainer.epochs)
            model.add_callback("on_fit_epoch_end", on_fit_epoch_end)

        # Train
        results = model.train(
            data=str(self.yaml_path.absolute()),
            epochs=epochs,
            imgsz=imgsz,
            project=str(self.models_path.absolute()),
            name=f"{project_name}_model",
            device=device,
            batch=batch_size,
            workers=workers,
            exist_ok=True
        )

        # Path to best weights
        best_model_path = self.models_path / f"{project_name}_model" / "weights" / "best.pt"
        return str(best_model_path)
