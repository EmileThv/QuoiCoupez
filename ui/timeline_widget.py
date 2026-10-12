from PySide6.QtCore import QRectF, Qt, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

CLIP_COLORS = ["#4f8ef7", "#f7a14f", "#6cc070", "#c76cf0", "#f06c8a"]


class TimelineWidget(QWidget):
    """Timeline statique : règle de temps, pistes et clips dessinés via paintEvent."""

    RULER_HEIGHT = 28
    HEADER_WIDTH = 80
    TRACK_HEIGHT = 60
    TRACK_SPACING = 4
    MIN_DURATION = 30  # secondes affichées au minimum

    def __init__(self, timeline_model, parent=None):
        super().__init__(parent)
        self.timeline_model = timeline_model
        self.pixels_per_second = 20
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
                x = self._time_to_x(clip.get_position())
                width = max(clip.get_duration() * self.pixels_per_second, 1)
                rect = QRectF(x, top + 3, width, self.TRACK_HEIGHT - 6)
                painter.setBrush(QColor(CLIP_COLORS[color_index % len(CLIP_COLORS)]))
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
