from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGroupBox, QFormLayout)
import torch

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(350)

        # Default settings if none provided
        self.settings = current_settings or {
            'train_device': 'cpu',
            'inference_device': 'cpu'
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

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background-color: darkblue; color: white;")
        btn_save.clicked.connect(self.save_settings)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_settings(self):
        self.settings['train_device'] = self.combo_train.currentData()
        self.settings['inference_device'] = self.combo_infer.currentData()
        self.accept()
