from PySide6.QtCore import QRectF, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from core.clip import Clip
from workers.keyframe_worker import KeyframeWorker

CLIP_COLORS = ["#4f8ef7", "#f7a14f", "#6cc070", "#c76cf0", "#f06c8a"]


class TimelineWidget(QWidget):
    """Timeline : règle de temps, pistes et clips dessinés via paintEvent.

    Souris : clic gauche sélectionne un clip, glisser le déplace dans le temps et d'une piste à
    l'autre, glisser l'un de ses bords le raccourcit (trim). Ctrl + molette zoome, Suppr supprime
    le clip sélectionné. Chaque clip affiche des vignettes de sa source.
    """

    clip_selected = Signal(object)  # Clip sélectionné (None si la sélection est effacée)
    clip_moved = Signal(object)  # Clip dont la position vient de changer
    clip_trimmed = Signal(object)  # Clip dont les points in/out viennent de changer

    RULER_HEIGHT = 28
    HEADER_WIDTH = 80
    TRACK_HEIGHT = 60
    TRACK_SPACING = 4
    MIN_DURATION = 30  # secondes affichées au minimum
    HANDLE_WIDTH = 6  # largeur (px) de la zone de saisie des bords d'un clip
    MIN_CLIP_DURATION = 0.1  # durée minimale (s) d'un clip après trim
    KEYFRAME_COUNT = 20  # nombre de vignettes extraites par média

    def __init__(self, timeline_model, parent=None):
        super().__init__(parent)
        self.timeline_model = timeline_model
        self.pixels_per_second = 20
        self.setAcceptDrops(True)
        self.selected_clip = None
        self._drag_clip = None
        self._drag_offset = 0  # secondes entre le début du clip et le point saisi
        self._trim_clip = None
        self._trim_edge = None  # "left" ou "right"
        self._keyframes = {}  # chemin du média -> liste de QImage (vide si illisible ou pas encore prête)
        self._keyframe_workers = []  # threads d'extraction en cours
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.ClickFocus)  # nécessaire pour recevoir la touche Suppr
        self.timeline_model.changed.connect(self.refresh)
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

    # Retourne "left" ou "right" si le point est sur un bord du clip, sinon None
    def _edge_at(self, clip, point):
        rect = self._clip_rect(self._track_index_of(clip), clip)
        if point.x() <= rect.left() + self.HANDLE_WIDTH:
            return "left"
        if point.x() >= rect.right() - self.HANDLE_WIDTH:
            return "right"
        return None

    def _track_index_of(self, clip):
        for index, track in enumerate(self.timeline_model.get_project().get_tracks()):
            if clip in track.get_clips():
                return index
        return None

    def _cursor_at(self, point):
        clip = self._clip_at(point)
        if clip is None:
            return Qt.ArrowCursor
        return Qt.SizeHorCursor if self._edge_at(clip, point) else Qt.OpenHandCursor

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        clip = self._clip_at(event.position())
        self.select_clip(clip)
        if clip is None:
            return
        edge = self._edge_at(clip, event.position())
        if edge is not None:
            self._trim_clip = clip
            self._trim_edge = edge
            self.setCursor(Qt.SizeHorCursor)
            return
        self._drag_clip = clip
        self._drag_offset = (event.position().x() - self._time_to_x(clip.get_position())) / self.pixels_per_second
        self.setCursor(Qt.ClosedHandCursor)

    # Déplace le bord saisi du clip à la position x (le clip reste dans les limites de sa source)
    def _trim_to(self, x):
        clip = self._trim_clip
        time = (x - self.HEADER_WIDTH) / self.pixels_per_second
        in_point, out_point = clip.get_in_point(), clip.get_out_point()

        if self._trim_edge == "left":
            # Le bord gauche suit la souris : l'in_point change du même décalage que la position.
            delta = time - clip.get_position()
            delta = max(-in_point, -clip.get_position(), min(delta, clip.get_duration() - self.MIN_CLIP_DURATION))
            in_point = round(in_point + delta, 2)
        else:
            out_point = round(time - clip.get_position() + in_point, 2)
            out_point = max(in_point + self.MIN_CLIP_DURATION, out_point)
            source = clip.get_source()
            if hasattr(source, "get_duration"):
                out_point = min(out_point, source.get_duration())

        if in_point == clip.get_in_point() and out_point == clip.get_out_point():
            return
        track = self.timeline_model.get_project().get_tracks()[self._track_index_of(clip)]
        try:
            self.timeline_model.trim_clip(track, clip, in_point, out_point)
        except ValueError:
            return  # trim refusé : le clip reste inchangé
        self.clip_trimmed.emit(clip)
        self.refresh()

    def mouseMoveEvent(self, event):
        if self._trim_clip is not None:
            self._trim_to(event.position().x())
            return
        if self._drag_clip is None:
            self.setCursor(self._cursor_at(event.position()))
            return
        time = (event.position().x() - self.HEADER_WIDTH) / self.pixels_per_second - self._drag_offset
        new_position = max(0, round(time, 2))
        tracks = self.timeline_model.get_project().get_tracks()
        track = tracks[self._track_index_of(self._drag_clip)]
        # Le clip change de piste quand la souris passe sur une autre piste (sinon il reste sur la sienne).
        target_index = self._y_to_track_index(event.position().y())
        target = tracks[target_index] if target_index is not None else track
        if new_position != self._drag_clip.get_position() or target is not track:
            # Passe par le modèle : la durée totale est recalculée et la timeline se redessine.
            self.timeline_model.move_clip(track, self._drag_clip, new_position, target)
            self.clip_moved.emit(self._drag_clip)

    # Suppr / Retour arrière : supprime le clip sélectionné
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.selected_clip is not None:
            clip = self.selected_clip
            track_index = self._track_index_of(clip)
            self.select_clip(None)
            if track_index is not None:
                track = self.timeline_model.get_project().get_tracks()[track_index]
                self.timeline_model.remove_clip(track, clip)
            return
        super().keyPressEvent(event)

    # Ctrl + molette : zoom avant / arrière (la molette seule fait défiler la timeline)
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            self.set_pixels_per_second(min(max(self.pixels_per_second * factor, 2), 400))
            event.accept()
            return
        super().wheelEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and (self._drag_clip is not None or self._trim_clip is not None):
            self._drag_clip = None
            self._trim_clip = None
            self._trim_edge = None
            self.setCursor(self._cursor_at(event.position()))

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
                self._draw_thumbnails(painter, clip, rect)
                # Nom du clip dans un bandeau sombre, lisible quelle que soit la vignette dessous
                label_rect = QRectF(rect.left() + 2, rect.bottom() - 17, max(rect.width() - 4, 0), 15)
                painter.fillRect(label_rect, QColor(0, 0, 0, 150))
                painter.setPen(QColor("#ffffff"))
                painter.setFont(self._font(8))
                painter.drawText(
                    label_rect.adjusted(4, 0, -4, 0),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    painter.fontMetrics().elidedText(
                        self._clip_label(clip), Qt.ElideRight, max(int(label_rect.width()) - 8, 0)
                    ),
                )
                color_index += 1

    # Vignettes de la source, extraites une seule fois par média dans un thread séparé.
    # Retourne une liste vide tant qu'elles ne sont pas prêtes (ou si la source est illisible).
    def _get_keyframes(self, media):
        path = media.get_file_path()
        if path not in self._keyframes:
            self._keyframes[path] = []
            worker = KeyframeWorker(path, self.KEYFRAME_COUNT, self.TRACK_HEIGHT - 6, self)
            worker.keyframes_ready.connect(self._on_keyframes_ready)
            worker.finished.connect(lambda: self._keyframe_workers.remove(worker))
            self._keyframe_workers.append(worker)
            worker.start()
        return self._keyframes[path]

    @Slot(str, list)
    def _on_keyframes_ready(self, path, images):
        self._keyframes[path] = images
        self.update()

    # Attend la fin des extractions en cours (à appeler avant de fermer l'application)
    def stop_workers(self):
        for worker in list(self._keyframe_workers):
            worker.wait()

    # Remplit le clip de vignettes : chacune montre l'image de la source au temps correspondant
    def _draw_thumbnails(self, painter, clip, rect):
        source = clip.get_source()
        if source is None or not hasattr(source, "get_duration") or source.get_duration() <= 0:
            return
        keyframes = self._get_keyframes(source)
        if not keyframes:
            return

        tile_width = max(keyframes[0].width(), 1)
        painter.save()
        painter.setClipRect(rect)
        x = rect.left()
        while x < rect.right():
            source_time = clip.get_in_point() + (x + tile_width / 2 - rect.left()) / self.pixels_per_second
            ratio = min(max(source_time / source.get_duration(), 0), 0.999)
            image = keyframes[int(ratio * len(keyframes))]
            painter.drawImage(QRectF(x, rect.top(), tile_width, rect.height()), image)
            x += tile_width
        painter.restore()

        # Le cadre est redessiné par-dessus les vignettes qui masquent le contour du clip
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#ffd400"), 3) if clip is self.selected_clip else QPen(QColor("#ffffff"), 1))
        painter.drawRoundedRect(rect, 4, 4)

    @staticmethod
    def _clip_label(clip):
        source = clip.get_source()
        label = source.get_name() if source is not None else "Clip"
        nb_effects = len(clip.get_effects())
        if nb_effects > 0:
            label += f"  [fx {nb_effects}]"
        return label

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