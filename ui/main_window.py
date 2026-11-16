import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QScrollArea, QVBoxLayout, QWidget,
)

from core.media import VideoMedia
from core.project import Project
from core.timeline_model import TimelineModel
from core.track import Track
from ui.controls_widget import ControlsWidget
from ui.effects_panel import EffectsPanel
from ui.export_dialog import ExportDialog
from ui.icons import load_icon
from ui.media_library import MediaLibraryWidget
from ui.preview_widget import PreviewWidget
from ui.timeline_widget import TimelineWidget
from video.decoder import get_video_metadata
from video.exporter import VideoExporter
from video.thumbnail import generate_thumbnail
from workers.playback_worker import PlaybackWorker

THUMBNAIL_DIR = os.path.join(tempfile.gettempdir(), "quoicoupez_thumbnails")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoiCoupez")
        self.resize(1280, 720)

        self.timeline_model = TimelineModel(self._build_project())

        self.library = MediaLibraryWidget()
        self.library.setMinimumWidth(260)
        self.library.list_widget.itemDoubleClicked.connect(self._preview_item)
        self.preview = PreviewWidget()
        self.controls = ControlsWidget(self)
        self.timeline = TimelineWidget(self.timeline_model)
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setMinimumHeight(200)
        self.effects_panel = EffectsPanel()
        self.effects_panel.setMinimumWidth(280)
        self.timeline.clip_selected.connect(self._on_clip_selected)
        self.effects_panel.effects_changed.connect(self._on_effects_changed)

        top = QHBoxLayout()
        top.addWidget(self.library, 1)
        top.addWidget(self.preview, 3)
        top.addWidget(self.effects_panel, 1)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addLayout(top, 3)
        layout.addWidget(self.controls)
        layout.addWidget(timeline_scroll, 1)
        self.setCentralWidget(central)

        self.playback_worker = None
        self.playback_path = None
        self.controls.setEnabled(False)

        file_menu = self.menuBar().addMenu("Fichier")
        import_action = QAction(load_icon("import"), "Importer un média…", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_media)
        file_menu.addAction(import_action)
        export_action = QAction(load_icon("export"), "Exporter…", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.open_export_dialog)
        file_menu.addAction(export_action)

        # Espace : lecture / pause (un champ de texte qui a le focus garde la touche pour lui)
        play_pause = QShortcut(QKeySequence(Qt.Key_Space), self)
        play_pause.activated.connect(self._toggle_playback)

    def _toggle_playback(self):
        if self.playback_worker is None:
            return
        if self.playback_worker.is_playing():
            self.playback_worker.pause()
        else:
            self.playback_worker.play()

    def open_export_dialog(self):
        ExportDialog(self._make_export, self).exec()

    # Prépare l'export du montage (copie du projet faite ici, dans le thread de l'interface)
    def _make_export(self, output_path):
        try:
            exporter = VideoExporter(self.timeline_model.get_project(), output_path)
        except ValueError as error:
            # Timeline vide... : l'erreur est affichée par la boîte de dialogue comme un échec d'export.
            def failed_export(on_progress, message=str(error)):
                raise ValueError(message)
            return failed_export
        return exporter.export

    # Projet vide avec deux pistes : les clips viennent du glisser-déposer depuis la bibliothèque.
    def _build_project(self):
        project = Project("Nouveau projet")
        project.add_track(Track())
        project.add_track(Track())
        return project

    # Demande des fichiers vidéo à l'utilisateur et les ajoute au projet et à la bibliothèque
    def import_media(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Importer des médias", "assets", "Vidéos (*.mp4 *.avi *.mov *.mkv);;Tous les fichiers (*)"
        )
        for path in paths:
            try:
                self.add_media_file(path)
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Import impossible", f"{os.path.basename(path)} : {error}")

    # Lit les métadonnées, génère la miniature, puis enregistre le média (retourne le VideoMedia)
    def add_media_file(self, path):
        project = self.timeline_model.get_project()
        path = os.path.abspath(path)
        for media in project.get_media():
            if media.get_file_path() == path:
                return media

        metadata = get_video_metadata(path)
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{abs(hash(path))}.jpg")
        generate_thumbnail(path, thumbnail_path)

        media = VideoMedia(
            path, os.path.basename(path), metadata["duration"],
            metadata["resolution"], metadata["fps"], thumbnail_path,
        )
        project.add_media(media)
        self.library.add_media(media)
        return media

    # Double-clic sur un média de la bibliothèque : l'affiche dans l'aperçu, sans effets
    def _preview_item(self, item):
        self.timeline.select_clip(None)
        self._start_playback_worker(item.data(Qt.UserRole).get_file_path())

    # Clip sélectionné sur la timeline : l'aperçu lit sa source à partir de son point d'entrée,
    # avec ses effets, et le panneau d'effets affiche ses effets.
    def _on_clip_selected(self, clip):
        self.effects_panel.set_clip(clip)
        if clip is None:
            if self.playback_worker is not None:
                self.playback_worker.set_effects([])
            return

        path = clip.get_source().get_file_path()
        if self.playback_worker is None or self.playback_path != path:
            self._start_playback_worker(path)
        if self.playback_worker is None:
            return
        self.playback_worker.set_effects(clip.get_effects())
        self.playback_worker.seek(int(clip.get_in_point() * self.playback_worker.get_fps()))

    # Effets modifiés dans le panneau : l'aperçu est mis à jour immédiatement
    def _on_effects_changed(self, clip):
        if self.playback_worker is not None and clip is self.timeline.selected_clip:
            self.playback_worker.set_effects(clip.get_effects())
        self.timeline.refresh()

    # Crée (ou remplace) le worker de lecture et le connecte à l'aperçu et aux contrôles
    def _start_playback_worker(self, path):
        self._stop_playback_worker()
        if not os.path.isfile(path):
            self.controls.setEnabled(False)
            return

        worker = PlaybackWorker(path, self)
        self.playback_path = path
        worker.frame_ready.connect(self.preview.set_image)
        worker.effect_failed.connect(lambda message: self.statusBar().showMessage(f"Effet ignoré : {message}", 5000))
        worker.position_changed.connect(self.controls.set_position)
        self.controls.set_maximum(max(worker.get_frame_count() - 1, 0))
        self.controls.set_position(0)

        self.controls.play_clicked.connect(worker.play)
        self.controls.pause_clicked.connect(worker.pause)
        self.controls.stop_clicked.connect(worker.stop_playback)
        self.controls.seek_requested.connect(worker.seek)

        self.controls.setEnabled(True)
        self.playback_worker = worker
        worker.start()

    def _stop_playback_worker(self):
        if self.playback_worker is None:
            return
        for signal in (self.controls.play_clicked, self.controls.pause_clicked,
                       self.controls.stop_clicked, self.controls.seek_requested):
            signal.disconnect()
        self.playback_worker.stop()
        self.playback_worker = None
        self.playback_path = None

    # Arrête proprement le thread de lecture avant de fermer la fenêtre
    def closeEvent(self, event):
        self._stop_playback_worker()
        self.timeline.stop_workers()
        super().closeEvent(event)
