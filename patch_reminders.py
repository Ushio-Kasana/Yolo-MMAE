import re

with open('src/ui/main_window.py', 'r') as f:
    content = f.read()

# Add closeEvent
close_event_code = """
    def closeEvent(self, event):
        if self.annotations and len(self.annotations) > 0:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have annotations in memory that may not be exported to the dataset yet.\\n\\nDo you want to export your dataset before closing?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Yes:
                self.export_dataset()
                event.accept()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
"""

# Insert closeEvent before toggle_play
content = re.sub(r'(\s+def toggle_play\(self\):)', close_event_code + r'\1', content)

# Modify unload_media
unload_media_old = """    def unload_media(self):
        if self.video_processor:
            self.video_processor.release()
            self.video_processor = None
        self.canvas.clear_boxes()
        self.canvas.set_image(None)
        self.annotations = {}
        self.current_frame_idx = 0
        self.lbl_frame.setText("Frame: 0 / 0")
        self.slider.setMaximum(0)
        self.slider.setValue(0)"""

unload_media_new = """    def unload_media(self):
        if self.annotations and len(self.annotations) > 0:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have annotations in memory that may not be exported to the dataset yet.\\n\\nDo you want to export your dataset before unloading media?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.export_dataset()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        if self.video_processor:
            self.video_processor.release()
            self.video_processor = None
        self.canvas.clear_boxes()
        self.canvas.set_image(None)
        self.annotations = {}
        self.current_frame_idx = 0
        self.lbl_frame.setText("Frame: 0 / 0")
        self.slider.setMaximum(0)
        self.slider.setValue(0)"""

content = content.replace(unload_media_old, unload_media_new)

with open('src/ui/main_window.py', 'w') as f:
    f.write(content)
