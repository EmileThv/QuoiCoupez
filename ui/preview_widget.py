from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy


class PreviewWidget(QLabel):
    """Affiche l'image courante de la vidéo (QLabel + QImage)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: black; color: gray;")
        self.clear_frame()

    @Slot(QImage)
    def set_image(self, image):
        """Affiche un QImage (ex : signal Signal(QImage) du playback_worker)."""
        if not isinstance(image, QImage):
            raise TypeError("PreviewWidget.set_image: image must be of type QImage")
        if image.isNull():
            self.clear_frame()
            return
        self._pixmap = QPixmap.fromImage(image)
        self._update_display()

    def set_frame(self, frame):
        """Affiche une frame BGR (numpy uint8, shape (h, w, 3)) telle que fournie par OpenCV."""
        if not hasattr(frame, "shape") or len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError("PreviewWidget.set_frame: frame must be a BGR array of shape (h, w, 3)")
        height, width, _ = frame.shape
        # .copy() : le QImage ne possède pas le buffer numpy, on évite qu'il soit libéré
        image = QImage(frame.data, width, height, 3 * width, QImage.Format_BGR888).copy()
        self.set_image(image)

    def clear_frame(self):
        self._pixmap = None
        self.setPixmap(QPixmap())
        self.setText("Aucune vidéo")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def _update_display(self):
        if self._pixmap is None:
            return
        self.setPixmap(
            self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
