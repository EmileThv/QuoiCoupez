import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QScrollArea, QSplitter

from core.clip import Clip
from core.media import VideoMedia
from core.project import Project
from core.timeline_model import TimelineModel
from core.track import Track
from ui.preview_widget import PreviewWidget
from ui.timeline_widget import TimelineWidget

TEST_VIDEO_PATH = os.path.join("assets", "video.mp4")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoiCoupez")
        self.resize(1280, 720)

        self.timeline_model = TimelineModel(self._build_demo_project())

        self.preview = PreviewWidget()
        self.timeline = TimelineWidget(self.timeline_model)
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setMinimumHeight(200)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.preview)
        splitter.addWidget(timeline_scroll)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 220])
        self.setCentralWidget(splitter)

        self._show_first_frame(TEST_VIDEO_PATH)

    # Provisoire : projet de démonstration (2 pistes, clips statiques) en attendant l'import de médias.
    def _build_demo_project(self):
        project = Project("Démo")
        model = TimelineModel(project)
        media = VideoMedia(TEST_VIDEO_PATH, "video.mp4", 20, (1920, 1080), 30, "")
        for clips in ([(0, 0, 8), (10, 0, 6)], [(2, 0, 5), (9, 0, 9)]):
            track = Track()
            project.add_track(track)
            for position, in_point, out_point in clips:
                model.add_clip(track, Clip(media, in_point, out_point, position))
        return project

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
