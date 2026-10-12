import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QMainWindow, QScrollArea, QVBoxLayout, QWidget

from core.clip import Clip
from core.media import VideoMedia
from core.project import Project
from core.timeline_model import TimelineModel
from core.track import Track
from ui.controls_widget import ControlsWidget
from ui.preview_widget import PreviewWidget
from ui.timeline_widget import TimelineWidget
from workers.playback_worker import PlaybackWorker

TEST_VIDEO_PATH = os.path.join("assets", "video.mp4")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoiCoupez")
        self.resize(1280, 720)

        self.timeline_model = TimelineModel(self._build_demo_project())

        self.preview = PreviewWidget()
        self.controls = ControlsWidget(self)
        self.timeline = TimelineWidget(self.timeline_model)
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setMinimumHeight(200)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addWidget(self.preview, 3)
        layout.addWidget(self.controls)
        layout.addWidget(timeline_scroll, 1)
        self.setCentralWidget(central)

        self.playback_worker = None
        self._start_playback_worker(TEST_VIDEO_PATH)

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

    # Crée le worker de lecture et le connecte à l'aperçu et aux contrôles
    def _start_playback_worker(self, path):
        if not os.path.isfile(path):
            self.controls.setEnabled(False)
            return

        worker = PlaybackWorker(path, self)
        worker.frame_ready.connect(self.preview.set_image)
        worker.position_changed.connect(self.controls.set_position)
        self.controls.set_maximum(worker.get_frame_count() - 1)

        self.controls.play_clicked.connect(worker.play)
        self.controls.pause_clicked.connect(worker.pause)
        self.controls.stop_clicked.connect(worker.stop_playback)
        self.controls.seek_requested.connect(worker.seek)

        self.playback_worker = worker
        worker.start()

    # Arrête proprement le thread de lecture avant de fermer la fenêtre
    def closeEvent(self, event):
        if self.playback_worker is not None:
            self.playback_worker.stop()
        super().closeEvent(event)
