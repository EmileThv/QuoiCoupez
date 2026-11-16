from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from video.thumbnail import generate_keyframes


# KeyframeWorker: extracts the thumbnails of a video in a separate thread, because reading
# frames spread over a whole video takes several seconds and would freeze the UI.
class KeyframeWorker(QThread):
    # (video path, list of QImage); the list is empty if the video could not be read
    keyframes_ready = Signal(str, list)

    def __init__(self, video_path, count, height, parent=None):
        super().__init__(parent)
        if not isinstance(video_path, str):
            raise TypeError("keyframe_worker.__init__: video_path must be of type str")
        self.video_path = video_path
        self.count = count
        self.height = height

    def run(self):
        try:
            frames = generate_keyframes(self.video_path, self.count, self.height)
        except (OSError, ValueError, TypeError):
            self.keyframes_ready.emit(self.video_path, [])
            return
        images = [
            QImage(f.data, f.shape[1], f.shape[0], f.strides[0], QImage.Format_BGR888).copy()
            for f in frames
        ]
        self.keyframes_ready.emit(self.video_path, images)
