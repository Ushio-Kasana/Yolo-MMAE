import re

with open('src/training/yolo_trainer.py', 'r') as f:
    content = f.read()

train_old = """    def train(self, epochs=10, imgsz=640, project_name="my_project", progress_callback=None, pretrained=True, device='cpu', batch_size=16, workers=8):
        \"\"\"
        Trains YOLOv8 model on the saved dataset.
        Returns the path to the best trained model weights.
        \"\"\"
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Dataset YAML not found at {self.yaml_path}")

        # Start from pretrained weights or from scratch (yaml config)
        model_target = 'yolov8n.pt' if pretrained else 'yolov8n.yaml'
        model = YOLO(model_target)"""

train_new = """    def train(self, epochs=10, imgsz=640, project_name="my_project", progress_callback=None, pretrained=True, device='cpu', batch_size=16, workers=8):
        \"\"\"
        Trains YOLOv8 model on the saved dataset.
        Returns the path to the best trained model weights.
        \"\"\"
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Dataset YAML not found at {self.yaml_path}")

        # Start from pretrained weights or from scratch (yaml config)
        if isinstance(pretrained, str):
            # User provided a custom path
            model_target = pretrained
        else:
            model_target = 'yolov8n.pt' if pretrained else 'yolov8n.yaml'

        model = YOLO(model_target)"""

content = content.replace(train_old, train_new)

with open('src/training/yolo_trainer.py', 'w') as f:
    f.write(content)
