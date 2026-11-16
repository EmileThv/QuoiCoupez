import sys
from PySide6.QtWidgets import QApplication
from ui.icons import load_icon, load_style
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("QuoiCoupez")
    app.setWindowIcon(load_icon("app"))
    app.setStyleSheet(load_style())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
