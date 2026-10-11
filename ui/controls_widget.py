from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider
from PySide6.QtCore import Qt, Signal


# ControlsWidget : play/pause/stop buttons and a progress slider.
class ControlsWidget(QWidget):
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    seek_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_button = QPushButton("Play", self)
        self.pause_button = QPushButton("Pause", self)
        self.stop_button = QPushButton("Stop", self)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 0)

        self.play_button.clicked.connect(self.play_clicked.emit)
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.slider.sliderMoved.connect(self.seek_requested.emit)

        layout = QHBoxLayout(self)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.slider, 1)
        self.setLayout(layout)

    # Sets the maximum slider value (total number of frames)
    def set_maximum(self, maximum):
        if not isinstance(maximum, int):
            raise TypeError("controls_widget.set_maximum: maximum must be of type int")
        self.slider.setRange(0, maximum)

    # Moves the slider, unless the user is dragging it
    def set_position(self, value):
        if not isinstance(value, int):
            raise TypeError("controls_widget.set_position: value must be of type int")
        if not self.slider.isSliderDown():
            self.slider.setValue(value)