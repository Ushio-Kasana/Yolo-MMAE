import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    # Require user to select or create project before showing main window
    window.start_project()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
