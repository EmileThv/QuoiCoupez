import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(ROOT, "resources", "icons")
STYLE_PATH = os.path.join(ROOT, "resources", "style.qss")

_cache = {}


# Returns the icon resources/icons/icon_<name>.svg (an empty icon if the file is missing).
# The SVG is drawn here with QSvgRenderer: QIcon("x.svg") only works when Qt's SVG library
# has already been loaded, which depends on the import order.
def load_icon(name):
    if name in _cache:
        return _cache[name]
    path = os.path.join(ICONS_DIR, f"icon_{name}.svg")
    icon = QIcon()
    renderer = QSvgRenderer(path)
    if renderer.isValid():
        for size in (16, 24, 32, 48, 64):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            icon.addPixmap(pixmap)
    _cache[name] = icon
    return icon


# Returns the content of resources/style.qss ("" if the file is missing, the default Qt look is kept).
def load_style():
    try:
        with open(STYLE_PATH, encoding="utf-8") as file:
            return file.read()
    except OSError:
        return ""
