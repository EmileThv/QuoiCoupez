import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from ui.media_library import MediaLibraryWidget
from core.media import VideoMedia
from video.thumbnail import generate_thumbnail


def main():
    app = QApplication(sys.argv)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(project_root, "assets", "video.mp4")
    thumbnail_path = os.path.join(project_root, "assets", "test_thumbnail.jpg")

    generate_thumbnail(video_path, thumbnail_path)

    library = MediaLibraryWidget()
    test_media = VideoMedia(
        video_path, "Ma vidéo test",
        duration=30.0, resolution=(1920, 1080), fps=30.0,
        thumbnail_path=thumbnail_path
    )
    library.add_media(test_media)
    library.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()