from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGroupBox, QFormLayout,
                             QSpinBox)
from PyQt6.QtCore import Qt
import torch
import json
import os
from pathlib import Path

GLOBAL_CONFIG_PATH = Path.home() / ".yolo_annotator_config.json"

def load_global_settings():
    import multiprocessing
    default_workers = max(1, multiprocessing.cpu_count() // 2)

    best_device = 'cpu'
    if torch.cuda.is_available():
        best_device = 'cuda:0'
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        best_device = 'mps'

    defaults = {
        'train_device': best_device,
        'inference_device': best_device,
        'batch_size': 16,
        'workers': default_workers
    }

    if GLOBAL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_CONFIG_PATH, 'r') as f:
                user_settings = json.load(f)
                defaults.update(user_settings)
        except Exception:
            pass

    return defaults

def save_global_settings(settings):
    try:
        with open(GLOBAL_CONFIG_PATH, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(350)

        import multiprocessing
        self.default_workers = max(1, multiprocessing.cpu_count() // 2)

        # Default settings if none provided
        self.settings = current_settings or {
            'train_device': 'cpu',
            'inference_device': 'cpu',
            'batch_size': 16,
            'workers': self.default_workers
        }

        self.available_devices = self._discover_devices()

        self.init_ui()

    def _discover_devices(self):
        devices = [('CPU', 'cpu')]

        # Check for CUDA (Nvidia GPU)
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                devices.append((f"GPU: {name}", f"cuda:{i}"))

        # Check for MPS (Apple Silicon GPU)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            devices.append(("Apple Metal (MPS)", "mps"))

        return devices

    def init_ui(self):
        layout = QVBoxLayout()

        # Hardware Group
        hw_group = QGroupBox("Hardware Acceleration")
        hw_layout = QFormLayout()

        self.combo_train = QComboBox()
        self.combo_infer = QComboBox()

        for display_name, id_name in self.available_devices:
            self.combo_train.addItem(display_name, id_name)
            self.combo_infer.addItem(display_name, id_name)

        # Set to current selections
        train_idx = self.combo_train.findData(self.settings['train_device'])
        if train_idx != -1: self.combo_train.setCurrentIndex(train_idx)

        infer_idx = self.combo_infer.findData(self.settings['inference_device'])
        if infer_idx != -1: self.combo_infer.setCurrentIndex(infer_idx)

        hw_layout.addRow("Model Training Device:", self.combo_train)
        hw_layout.addRow("Live Playback (Inference) Device:", self.combo_infer)
        hw_group.setLayout(hw_layout)

        layout.addWidget(hw_group)

        # Training Resource Limits Group
        res_group = QGroupBox("Training Resource Limits")
        res_layout = QVBoxLayout()

        form_res = QFormLayout()
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 128)
        self.spin_batch.setValue(self.settings.get('batch_size', 16))

        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(0, 32)
        self.spin_workers.setValue(self.settings.get('workers', self.default_workers))

        form_res.addRow("Batch Size (GPU VRAM usage):", self.spin_batch)
        form_res.addRow("CPU Workers (CPU thread usage):", self.spin_workers)

        res_layout.addLayout(form_res)

        lbl_info = QLabel(
            "<b>Batch Size:</b> Controls how many images are loaded into GPU memory at once. "
            "Higher values (16, 32) train faster but require more GPU VRAM. Lower values (4, 8) prevent Out-Of-Memory crashes.<br><br>"
            f"<b>CPU Workers:</b> Controls background threads for loading images. "
            f"Recommended: {self.default_workers} (half your CPU cores). Set to 0 if training freezes or crashes."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: gray; font-size: 11px;")
        res_layout.addWidget(lbl_info)

        res_group.setLayout(res_layout)
        layout.addWidget(res_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_benchmark = QPushButton("Auto-Detect / Benchmark")
        btn_benchmark.clicked.connect(self.run_benchmark)

        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background-color: darkblue; color: white;")
        btn_save.clicked.connect(self.save_settings)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_benchmark)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def run_benchmark(self):
        import multiprocessing
        import psutil

        # Determine fastest device
        best_device = 'cpu'
        vram_gb = 0

        if torch.cuda.is_available():
            best_device = 'cuda:0'
            try:
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            except:
                vram_gb = 8
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            best_device = 'mps'
            # MPS uses unified memory. Estimate based on total system RAM.
            vram_gb = psutil.virtual_memory().total / (1024**3)

        # Determine Safe Batch Size based on VRAM/RAM
        if best_device == 'cpu':
            safe_batch = 8
        else:
            if vram_gb >= 16:
                safe_batch = 32
            elif vram_gb >= 8:
                safe_batch = 16
            else:
                safe_batch = 8

        # Determine Workers
        cores = multiprocessing.cpu_count()
        safe_workers = min(8, max(1, cores // 2))

        # Apply to UI
        train_idx = self.combo_train.findData(best_device)
        if train_idx != -1: self.combo_train.setCurrentIndex(train_idx)

        infer_idx = self.combo_infer.findData(best_device)
        if infer_idx != -1: self.combo_infer.setCurrentIndex(infer_idx)

        self.spin_batch.setValue(safe_batch)
        self.spin_workers.setValue(safe_workers)

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Auto-Detect Complete",
                                f"Detected System:\n"
                                f"Hardware: {best_device.upper()}\n"
                                f"Estimated Memory: {vram_gb:.1f} GB\n"
                                f"CPU Cores: {cores}\n\n"
                                f"Settings updated to safe maximums.")

    def save_settings(self):
        self.settings['train_device'] = self.combo_train.currentData()
        self.settings['inference_device'] = self.combo_infer.currentData()
        self.settings['batch_size'] = self.spin_batch.value()
        self.settings['workers'] = self.spin_workers.value()
        save_global_settings(self.settings)
        self.accept()
