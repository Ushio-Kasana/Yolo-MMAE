import re

with open('src/ui/main_window.py', 'r') as f:
    content = f.read()

cb_load_full_old = """        self.cb_load_full = QCheckBox("Load Full Video")
        toolbar.addWidget(self.cb_load_full)"""

cb_load_full_new = """        self.cb_load_full = QCheckBox("Load Full Video")
        toolbar.addWidget(self.cb_load_full)

        self.cb_load_buffered = QCheckBox("Load Buffered")
        self.cb_load_buffered.setChecked(True) # default
        toolbar.addWidget(self.cb_load_buffered)

        # Make them mutually exclusive
        self.cb_load_full.toggled.connect(lambda checked: self.cb_load_buffered.setChecked(False) if checked else None)
        self.cb_load_buffered.toggled.connect(lambda checked: self.cb_load_full.setChecked(False) if checked else None)"""

content = content.replace(cb_load_full_old, cb_load_full_new)

load_video_old = """            self.video_processor = VideoProcessor(path, self.cb_load_full.isChecked())"""

load_video_new = """            if self.cb_load_full.isChecked():
                load_mode = 'full'
            elif self.cb_load_buffered.isChecked():
                load_mode = 'buffered'
            else:
                load_mode = 'ondemand'

            buffer_size = 120
            if load_mode == 'buffered':
                val, ok = QInputDialog.getInt(self, "Buffer Size", "Frames to load at a time:", 120, 10, 1000)
                if ok:
                    buffer_size = val
                else:
                    return # user cancelled

            self.video_processor = VideoProcessor(path, load_mode, buffer_size)"""

content = content.replace(load_video_old, load_video_new)

with open('src/ui/main_window.py', 'w') as f:
    f.write(content)
