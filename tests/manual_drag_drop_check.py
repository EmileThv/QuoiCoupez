import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from core.project import Project
from core.track import Track
from core.media import VideoMedia
from core.timeline_model import TimelineModel
from ui.media_library import MediaLibraryWidget
from ui.timeline_widget import TimelineWidget
from video.thumbnail import generate_thumbnail


def main():
    app = QApplication(sys.argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(root, "assets", "video.mp4")
    thumb_path = os.path.join(root, "assets", "test_thumbnail.jpg")
    generate_thumbnail(video_path, thumb_path)

    media = VideoMedia(video_path, "Ma vidéo test", 30.0, (1920, 1080), 30.0, thumb_path)

    project = Project("Test")
    project.add_media(media)
    project.add_track(Track())
    project.add_track(Track())
    model = TimelineModel(project)

    library = MediaLibraryWidget()
    library.add_media(media)
    timeline = TimelineWidget(model)

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(library)
    layout.addWidget(timeline)
    window.resize(1000, 500)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()