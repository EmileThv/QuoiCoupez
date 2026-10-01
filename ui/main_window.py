import os

from PySide6.QtWidgets import QMainWindow

from ui.preview_widget import PreviewWidget

TEST_VIDEO_PATH = os.path.join("assets", "video.mp4")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoiCoupez")
        self.resize(1280, 720)

        self.preview = PreviewWidget()
        self.setCentralWidget(self.preview)

        self._show_first_frame(TEST_VIDEO_PATH)

    def _show_first_frame(self, path):
        # Provisoire : à remplacer par le décodeur itérable (video/decoder.py) une fois finalisé.
        if not os.path.isfile(path):
            return
        import cv2

        capture = cv2.VideoCapture(path)
        ok, frame = capture.read()
        capture.release()
        if ok:
            self.preview.set_frame(frame)
