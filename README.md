# YOLO Video Annotator & Auto-Tracker

A powerful, hardware-accelerated desktop application built with Python, PyQt6, and OpenCV designed to streamline the creation of YOLO object detection datasets. Instead of manually annotating thousands of frames by hand, this tool leverages OpenCV tracking, motion detection, and Live YOLO Inference to automate the labeling process.

## 🚀 Key Features

* **Multi-Format Media Support**: Load `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, and more. Organize multiple videos seamlessly into a single project.
* **Smart Auto-Tracking**: Draw a bounding box on frame 1, and the built-in OpenCV CSRT tracker will follow the object through the rest of the video.
* **Look-Ahead Auto-Fix**: If the tracker drifts, simply adjust the bounding box on a later frame. The engine will instantly use your correction as ground truth and re-propagate the tracking forward.
* **Live YOLO Model Playback**: Train a YOLOv8 model directly inside the app, then click "Play with Model" to watch your AI dynamically detect and categorize objects in real-time. Use the **Auto-Confirm** toggle to build your dataset instantly while the video plays.
* **Advanced Drawing Tools**: Standard Rectangle, point-by-point Polygon bounding boxes, and an "Auto-Scale" floodfill tool that snaps to object edges automatically.
* **Bulk Actions & Review Screen**: Search through hundreds of frames to bulk-delete or bulk-move categories. Use the Review Menu with **Shift-Click multi-selection** to rapidly categorize grouped image crops.
* **Auto-Save & Project Restoration**: Every drawn box is instantly saved to disk as a YOLO-formatted `.txt` file. Close the app and hit "Restore Images" later to overlay your annotations directly back onto the original video timeline.
* **Hardware Benchmarking**: Includes a built-in Settings menu to explicitly target CPU, Nvidia CUDA, or Apple Metal (MPS). Run the **Live Benchmark** to automatically determine the safest Batch Size and Worker thread limits for your specific hardware.
* **Model Exporter**: Convert your trained `.pt` PyTorch model into `ONNX`, `TF.js`, `CoreML`, and more with a single click.

## 🛠 Installation

### Prerequisites
* Python 3.10 or higher
* [PyTorch](https://pytorch.org/get-started/locally/) installed for your specific hardware (CUDA for Nvidia, MPS for Apple Silicon).

```bash
# Clone the repository
git clone https://github.com/your-username/yolo-video-annotator.git
cd yolo-video-annotator

# Install requirements
pip install PyQt6 opencv-python numpy pyyaml ultralytics psutil

# Run the application
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/main.py
```

*Note for macOS users:* If you receive a `PermissionError` on startup regarding PyTorch, ensure your Terminal or IDE has "Full Disk Access" enabled in System Settings > Privacy & Security.

## 📖 Usage Guide

### 1. Project Setup
When launching the app, you will be prompted to create an empty folder for your project or select an existing one. The application will automatically construct a standard YOLO dataset directory (`dataset/images/train`, `dataset/labels/train`, and `data.yaml`) inside this folder.

### 2. Annotation & Drawing
Load a video using the top toolbar. On the right panel, click **Add Category** to create classes (e.g., "Car", "Pedestrian").
Select a category from the list, choose a drawing tool from the left toolbar, and click and drag on the video canvas.
* **Resize:** Click a drawn box to select it (it will turn yellow). Click and drag its edges to resize.
* **Undo:** Press `Ctrl+Z` to undo your last drawn box.

### 3. Smart Auto-Tracking
Instead of drawing every frame, draw boxes on your targets, select the **Auto Track** button in the top toolbar, pick the categories you want to track, and the OpenCV engine will propagate the boxes through the rest of the video.

### 4. Training the Model
Once you have annotated a sufficient number of frames, click **Train YOLO Model**. The application will read your hardware settings, prompt you for the number of epochs, and train a YOLOv8 network on your local GPU/CPU. A progress bar will track the epochs, and the weights (`best.pt`) will be saved in your project's `models/` directory along with a `labels.json` map.

### 5. Play with Model
Once the model is trained, click **Play with Model**. The application will stream the video while running live inference, overlaying your trained AI's predictions (cyan dashed boxes). If you check **Auto-Confirm Suggestions**, these live predictions will be permanently saved to your dataset as actual labels.

## ⚙️ Hardware Acceleration
Click the **⚙ Settings** button in the top right. Click **Run Live Benchmark** to have the application stress-test your CPU and GPU to find the fastest compute device and the maximum stable VRAM batch size to prevent Out-Of-Memory crashes during training.
