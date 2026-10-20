from PySide6.QtCore import QRectF, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from core.clip import Clip

CLIP_COLORS = ["#4f8ef7", "#f7a14f", "#6cc070", "#c76cf0", "#f06c8a"]


class TimelineWidget(QWidget):
    """Timeline : règle de temps, pistes et clips dessinés via paintEvent.

    Souris : clic gauche sélectionne un clip, glisser le déplace dans le temps sur sa piste.
    """

    clip_selected = Signal(object)  # Clip sélectionné (None si la sélection est effacée)
    clip_moved = Signal(object)  # Clip dont la position vient de changer

    RULER_HEIGHT = 28
    HEADER_WIDTH = 80
    TRACK_HEIGHT = 60
    TRACK_SPACING = 4
    MIN_DURATION = 30  # secondes affichées au minimum

    def __init__(self, timeline_model, parent=None):
        super().__init__(parent)
        self.timeline_model = timeline_model
        self.pixels_per_second = 20
        self.setAcceptDrops(True)
        self.selected_clip = None
        self._drag_clip = None
        self._drag_offset = 0  # secondes entre le début du clip et le point saisi
        self.setMouseTracking(True)
        self._update_size()

    # Redessine la timeline (slot prévu pour les futurs signaux du modèle)
    @Slot()
    def refresh(self):
        self._update_size()
        self.update()

    def set_pixels_per_second(self, pixels_per_second):
        if not isinstance(pixels_per_second, (int, float)) or pixels_per_second <= 0:
            raise ValueError("timeline_widget.set_pixels_per_second: must be a positive number")
        self.pixels_per_second = pixels_per_second
        self.refresh()

    # Durée affichée : fin du dernier clip (au moins MIN_DURATION)
    def _displayed_duration(self):
        end = 0
        for track in self.timeline_model.get_project().get_tracks():
            for clip in track.get_clips():
                end = max(end, clip.get_position() + clip.get_duration())
        return max(end + 5, self.MIN_DURATION)

    def _update_size(self):
        nb_tracks = len(self.timeline_model.get_project().get_tracks())
        width = self.HEADER_WIDTH + int(self._displayed_duration() * self.pixels_per_second)
        height = self.RULER_HEIGHT + nb_tracks * (self.TRACK_HEIGHT + self.TRACK_SPACING) + self.TRACK_SPACING
        self.setMinimumSize(width, height)

    def _font(self, point_size):
        font = QFont(self.font())
        font.setPointSize(point_size)
        return font

    def _time_to_x(self, seconds):
        return self.HEADER_WIDTH + seconds * self.pixels_per_second

    def _track_top(self, index):
        return self.RULER_HEIGHT + self.TRACK_SPACING + index * (self.TRACK_HEIGHT + self.TRACK_SPACING)

    def _clip_rect(self, track_index, clip):
        x = self._time_to_x(clip.get_position())
        width = max(clip.get_duration() * self.pixels_per_second, 1)
        return QRectF(x, self._track_top(track_index) + 3, width, self.TRACK_HEIGHT - 6)

    # Retourne le clip sous le point donné (celui dessiné au-dessus en cas de chevauchement), ou None
    def _clip_at(self, point):
        tracks = self.timeline_model.get_project().get_tracks()
        for index, track in enumerate(tracks):
            for clip in reversed(track.get_clips()):
                if self._clip_rect(index, clip).contains(point):
                    return clip
        return None

    def select_clip(self, clip):
        if clip is not self.selected_clip:
            self.selected_clip = clip
            self.clip_selected.emit(clip)
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        clip = self._clip_at(event.position())
        self.select_clip(clip)
        if clip is not None:
            self._drag_clip = clip
            self._drag_offset = (event.position().x() - self._time_to_x(clip.get_position())) / self.pixels_per_second
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_clip is None:
            self.setCursor(Qt.OpenHandCursor if self._clip_at(event.position()) else Qt.ArrowCursor)
            return
        time = (event.position().x() - self.HEADER_WIDTH) / self.pixels_per_second - self._drag_offset
        new_position = max(0, round(time, 2))
        if new_position != self._drag_clip.get_position():
            self._drag_clip.set_position(new_position)
            self.clip_moved.emit(self._drag_clip)
            self.refresh()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_clip is not None:
            self._drag_clip = None
            self.setCursor(Qt.OpenHandCursor if self._clip_at(event.position()) else Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        self._draw_tracks(painter)
        self._draw_ruler(painter)
        painter.end()

    def _draw_ruler(self, painter):
        painter.fillRect(0, 0, self.width(), self.RULER_HEIGHT, QColor("#1e1e1e"))
        painter.setPen(QColor("#bbbbbb"))
        painter.setFont(self._font(8))

        # Pas des graduations adapté à l'échelle (au moins ~60 px entre deux libellés)
        step = 1
        for candidate in (1, 2, 5, 10, 30, 60):
            step = candidate
            if candidate * self.pixels_per_second >= 60:
                break

        duration = int(self._displayed_duration())
        for second in range(0, duration + 1):
            x = int(self._time_to_x(second))
            if second % step == 0:
                painter.drawLine(x, self.RULER_HEIGHT - 12, x, self.RULER_HEIGHT)
                painter.drawText(x + 3, self.RULER_HEIGHT - 14, f"{second // 60:02d}:{second % 60:02d}")
            elif self.pixels_per_second >= 8:
                painter.drawLine(x, self.RULER_HEIGHT - 5, x, self.RULER_HEIGHT)

    def _draw_tracks(self, painter):
        tracks = self.timeline_model.get_project().get_tracks()
        color_index = 0
        for index, track in enumerate(tracks):
            top = self._track_top(index)

            # Fond de la piste + en-tête
            painter.fillRect(0, top, self.width(), self.TRACK_HEIGHT, QColor("#363636"))
            painter.fillRect(0, top, self.HEADER_WIDTH, self.TRACK_HEIGHT, QColor("#252525"))
            painter.setPen(QColor("#dddddd"))
            painter.setFont(self._font(9))
            painter.drawText(
                QRectF(0, top, self.HEADER_WIDTH, self.TRACK_HEIGHT),
                Qt.AlignCenter,
                f"Piste {index + 1}",
            )

            # Clips
            for clip in track.get_clips():
                rect = self._clip_rect(index, clip)
                painter.setBrush(QColor(CLIP_COLORS[color_index % len(CLIP_COLORS)]))
                if clip is self.selected_clip:
                    painter.setPen(QPen(QColor("#ffd400"), 3))
                else:
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                painter.drawRoundedRect(rect, 4, 4)
                painter.setPen(QColor("#ffffff"))
                painter.setFont(self._font(8))
                painter.drawText(
                    rect.adjusted(6, 0, -6, 0),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    painter.fontMetrics().elidedText(
                        self._clip_label(clip), Qt.ElideRight, max(int(rect.width()) - 12, 0)
                    ),
                )
                color_index += 1

    @staticmethod
    def _clip_label(clip):
        source = clip.get_source()
        return source.get_name() if source is not None else "Clip"

    MEDIA_MIME = "application/x-quoicoupez-media"

    def _x_to_time(self, x):
        return max((x - self.HEADER_WIDTH) / self.pixels_per_second, 0)

    def _y_to_track_index(self, y):
        tracks = self.timeline_model.get_project().get_tracks()
        for index in range(len(tracks)):
            top = self._track_top(index)
            if top <= y < top + self.TRACK_HEIGHT:
                return index
        return None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MEDIA_MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MEDIA_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if not mime.hasFormat(self.MEDIA_MIME):
            return

        file_path = bytes(mime.data(self.MEDIA_MIME)).decode("utf-8")
        point = event.position().toPoint()

        project = self.timeline_model.get_project()
        media = next((m for m in project.get_media() if m.get_file_path() == file_path), None)
        if media is None:
            return

        track_index = self._y_to_track_index(point.y())
        if track_index is None:
            return
        track = project.get_tracks()[track_index]

        clip = Clip(media, 0, media.get_duration(), self._x_to_time(point.x()))
        self.timeline_model.add_clip(track, clip)

        self.refresh()
        event.acceptProposedAction()