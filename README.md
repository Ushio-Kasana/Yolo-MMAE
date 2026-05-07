# YOLO Video Annotator & Auto-Tracker
*Multi-Media Annotation Engine*

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

## 💻 Compatible Systems
* Tested on Mac OS Tahoe 26.4
* Windows not tested
* Tested on Ubuntu 24.04.4 LTS X86_64.

## 🛠 Installation

### macOS Automated Installation
For macOS users, we provide automated setup and startup scripts to simplify the installation process. The `Macos-Setup-Venv.sh` script creates a new `venv` folder in the current folder for a optional isolated environments.

**Option 1: Using Virtual Environment (Recommended)**
```bash
# Run the setup script to configure python and dependencies
bash Macos-Setup-Venv.sh

# Run the application
bash Macos-Start-Venv.sh
```

**Option 2: System-wide Installation**
```bash
# Run the setup script to configure python and dependencies system-wide
bash Macos-Setup-systemwide.sh

# Run the application
bash Macos-Start-Systemwide.sh
```

*Note for macOS users:* If you receive a `PermissionError` on startup regarding PyTorch, ensure your Terminal or IDE has "Full Disk Access" enabled in System Settings > Privacy & Security.

### Manual Installation / Windows / MacOS & Linux
If you are on Windows, Linux, or prefer to install manually, follow these steps:

**Prerequisites:**
* Python 3.10 or higher
* [PyTorch](https://pytorch.org/get-started/locally/) installed for your specific hardware (CUDA for Nvidia).

```bash
# Clone the repository
git clone https://github.com/Ushio-Kasana/Yolo-MMAE.git
cd Yolo-MMAE

# Install requirements
pip install -r src/requirements.txt

# Run the application
python src/main.py
```

## 📖 Usage Guide

### 1. Project Setup & Resuming Work
When launching the app, you will be prompted to create an empty folder for your project or select an existing one. The application will automatically construct a standard YOLO dataset directory (`dataset/images/train`, `dataset/labels/train`, and `data.yaml`) inside this folder.

**How to resume an existing project:**
If you close the application and want to continue editing where you left off:
1. Open the application and select your existing Project folder.
2. Click **Load Video** and select the *exact same* original video file you were working on.
3. Click the **Restore Images** button in the top toolbar.
4. Select your media source from the dropdown menu.
5. The application will ask if you want to overlay annotations on the current media. **Select Yes**.
6. All your previously drawn bounding boxes will be un-normalized from the YOLO `.txt` files and instantly placed back onto the video timeline as editable boxes!

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

---

## 📝 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)** - see the [LICENSE](LICENSE) file for details. 

This means you are free to use, modify, and distribute this software, provided that any derivative works are also open-source and licensed under the exact same GPLv3 license. You must also include the original copyright notice and attribute the original author (Ushio-kasana) in any copies or substantial uses of the work.

## 🗺️ Known Issues & Roadmap

The following features are currently being worked on or need to be addressed in future releases:
* **Restoring images from a specific category:** Currently, restoration loads all categories. Future updates will allow precise filtering.
* **UI Performance:** Fix some spikes in menus and application freezing or stuttering during heavy OpenCV or PyTorch background tasks.
* **Auto-Benchmarking:** Fix the auto benchmarking utility to work correctly and yield more reliable heuristics across varied hardware.
* **Cross-Platform Compatibility:** Fully test and guarantee support for Windows and Linux environments.
* **Light Mode vs Dark Mode Support:** Fix Python ui and some of the visual elements for Light Mode users. Currently, when using Light Mode, the white outlines on the Review Group menu blend into the background, making it difficult to see boxes and selected objects.
* **Add support to allow existing models:** add implementation to allow already existing models to be further trained and expanded on.
* **Fix "Auto Scan (Motion)" Button:** After selecting the images to add to a model in most cases it wont acully add them into the project or dataset.
* **Add Reminder/Warning to save:** Add a Warning/Reminder for users to save there current state and work instead of just closing.
* **Fix Auto Scaling button:** Currently dosent work at all.
* **New Implimentation of Load full video:** currently ticking Load full video uses heaps of ram so add a new option that loads around 120 by default but will promt the user for the amount of frames of the video tehy would like to laod at a time to reduce load times and RAM usage for slower machines with less memory.