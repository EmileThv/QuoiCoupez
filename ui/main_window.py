import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from ui.controls_widget import ControlsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoiCoupez")
        self.resize(1280, 720)

        central = QWidget(self)
        layout = QVBoxLayout(central)

        self.controls = ControlsWidget(self)
        layout.addStretch(1) # Espace pour le widget de preview (à ajouter plus tard)
        layout.addWidget(self.controls)

        self.setCentralWidget(central)