from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.media import Media

# Gallery of imported media.
class MediaLibraryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.list_widget = QListWidget(self)
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(120, 68))        # Taille de l'icône modifiable si besoin
        self.list_widget.setResizeMode(QListWidget.Adjust)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    # Adds a media to the library and displays it with its thumbnail
    def add_media(self, media):
        if media is None:
            raise ValueError("media_library.add_media: media cannot be None")
        if not isinstance(media, Media):
            raise TypeError("media_library.add_media: media must be of type core.media.Media")

        item = QListWidgetItem(media.get_name())

        thumbnail_path = media.get_thumbnail_path()
        if thumbnail_path and os.path.isfile(thumbnail_path):
            item.setIcon(QIcon(thumbnail_path))

        item.setData(Qt.UserRole, media)
        self.list_widget.addItem(item)

    # Removes all media from the library
    def clear(self):
        self.list_widget.clear()

    # Returns the Media object currently selected, or None if nothing is selected
    def get_selected_media(self):
        current_item = self.list_widget.currentItem()
        if current_item is None:
            return None
        return current_item.data(Qt.UserRole)