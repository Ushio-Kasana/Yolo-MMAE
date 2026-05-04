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

    def train(self, epochs=10, imgsz=640, project_name="my_project", progress_callback=None):
        """
        Trains YOLOv8n model on the saved dataset.
        Returns the path to the best trained model weights.
        """
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Dataset YAML not found at {self.yaml_path}")

        model = YOLO('yolov8n.pt') # Start from pretrained weights

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
            exist_ok=True
        )

        # Path to best weights
        best_model_path = self.models_path / f"{project_name}_model" / "weights" / "best.pt"
        return str(best_model_path)
