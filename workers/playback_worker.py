import os

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


# PlaybackWorker: QThread that reads a video frame by frame in a loop
# and emits each frame as a QImage, without blocking the UI thread.
class PlaybackWorker(QThread):
    frame_ready = Signal(QImage)

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        if video_path is None:
            raise ValueError("playback_worker.__init__: video_path cannot be None")
        if not isinstance(video_path, str):
            raise TypeError("playback_worker.__init__: video_path must be of type str")
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"playback_worker.__init__: no file at {video_path}")

        # Checked here so the error reaches the caller, not the worker thread
        capture = cv2.VideoCapture(video_path)
        is_video = capture.isOpened()
        capture.release()
        if not is_video:
            raise ValueError(f"playback_worker.__init__: {video_path} is not a valid video file")

        self.video_path = video_path

    # Thread loop: read, emit, wait 1/fps, restart at the end
    def run(self):
        capture = cv2.VideoCapture(self.video_path)
        if not capture.isOpened():
            raise ValueError(f"playback_worker.run: cannot open video {self.video_path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 30
        delay_ms = int(1000 / fps)
        frame_number = 0

        while not self.isInterruptionRequested():
            ok, frame = capture.read()
            if not ok:
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_number = 0
                continue

            self.frame_ready.emit(self._to_qimage(frame))
            print(f"playback_worker: frame {frame_number}")
            frame_number += 1
            self.msleep(delay_ms)

        capture.release()

    # Stops the loop and waits for the thread to finish
    def stop(self):
        self.requestInterruption()
        self.wait()

    # Converts a BGR OpenCV frame to a QImage
    @staticmethod
    def _to_qimage(frame):
        height, width, _ = frame.shape
        return QImage(frame.data, width, height, 3 * width, QImage.Format_BGR888).copy()
