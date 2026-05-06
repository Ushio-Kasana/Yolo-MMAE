import re

with open('src/ui/review.py', 'r') as f:
    content = f.read()

set_selected_old = """    def set_selected(self, state):
        self.is_selected = state
        if self.is_selected:
            self.setStyleSheet("CropWidget { border: 3px solid white; background-color: rgba(255, 255, 255, 50); }")
        else:
            self.setStyleSheet("CropWidget { border: 2px solid transparent; background-color: transparent; }")"""

set_selected_new = """    def set_selected(self, state):
        self.is_selected = state
        if self.is_selected:
            # Check if OS is in Light Mode or Dark Mode by comparing window text vs base color luminance
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QPalette
            palette = QApplication.palette()
            bg_color = palette.color(QPalette.ColorRole.Window).lightness()

            # If background is bright, it's light mode, use black border
            if bg_color > 128:
                self.setStyleSheet("CropWidget { border: 3px solid black; background-color: rgba(0, 0, 0, 50); }")
            else:
                self.setStyleSheet("CropWidget { border: 3px solid white; background-color: rgba(255, 255, 255, 50); }")
        else:
            self.setStyleSheet("CropWidget { border: 2px solid transparent; background-color: transparent; }")"""

content = content.replace(set_selected_old, set_selected_new)

with open('src/ui/review.py', 'w') as f:
    f.write(content)
