import os

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QVBoxLayout,
)

from workers.export_worker import ExportWorker


# ExportDialog: window where the user picks the output file and follows the export progress.
class ExportDialog(QDialog):
    # make_export(output_path) gives back the function that does the export.
    def __init__(self, make_export, parent=None):
        super().__init__(parent)
        if make_export is None:
            raise ValueError("export_dialog.__init__: make_export cannot be None")
        if not callable(make_export):
            raise TypeError("export_dialog.__init__: make_export must be callable")
        self.make_export = make_export
        self.worker = None
        self.output_path = None

        self.setWindowTitle("Exporter la vidéo")
        self.setMinimumWidth(480)

        self.path_edit = QLineEdit(os.path.abspath("export.mp4"))
        self.browse_button = QPushButton("Parcourir…")
        self.browse_button.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.browse_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Choisissez le fichier de sortie puis cliquez sur Exporter.")
        self.status_label.setWordWrap(True)

        self.buttons = QDialogButtonBox()
        self.export_button = self.buttons.addButton("Exporter", QDialogButtonBox.AcceptRole)
        self.close_button = self.buttons.addButton("Fermer", QDialogButtonBox.RejectRole)
        self.export_button.clicked.connect(self.start_export)
        self.close_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fichier de sortie :"))
        layout.addLayout(path_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.buttons)

    def is_exporting(self):
        return self.worker is not None and self.worker.isRunning()

    def start_export(self):
        path = self.path_edit.text().strip()
        if path == "":
            self.status_label.setText("Indiquez un fichier de sortie.")
            return

        extension = os.path.splitext(path)[1]
        if extension == "":
            path += ".mp4"
            self.path_edit.setText(path)

        folder = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(folder):
            self.status_label.setText(f"Le dossier {folder} n'existe pas.")
            return

        self.output_path = path
        export_function = self.make_export(path)
        self.worker = ExportWorker(export_function, self)
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.export_finished.connect(self._on_finished)
        self.worker.export_failed.connect(self._on_failed)
        self.worker.export_cancelled.connect(self._on_cancelled)

        self.progress_bar.setValue(0)
        self.status_label.setText("Export en cours…")
        self._set_exporting(True)
        self.worker.start()

    # The "Annuler" button cancels the export if one is running, otherwise it closes the window.
    def reject(self):
        if self.is_exporting():
            self.status_label.setText("Annulation…")
            self.worker.cancel()
            return
        super().reject()

    def closeEvent(self, event):
        if self.is_exporting():
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la vidéo",
            self.path_edit.text(),
            "Vidéo MP4 (*.mp4)",
        )
        if path:
            self.path_edit.setText(path)

    def _on_progress(self, percent):
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Export en cours… {percent} %")

    def _on_finished(self):
        self._end_export(f"Export terminé : {self.output_path}")

    def _on_failed(self, message):
        self._end_export(f"Échec de l'export : {message}")

    def _on_cancelled(self):
        self._end_export("Export annulé.")

    def _end_export(self, message):
        self.status_label.setText(message)
        self._set_exporting(False)

    # Locks the fields during the export, and turns the "Fermer" button into "Annuler".
    def _set_exporting(self, exporting):
        self.path_edit.setEnabled(not exporting)
        self.browse_button.setEnabled(not exporting)
        self.export_button.setEnabled(not exporting)
        if exporting:
            self.close_button.setText("Annuler")
        else:
            self.close_button.setText("Fermer")
