from PySide6.QtCore import QThread, Signal


# Raised to stop an export that the user has cancelled.
class ExportCancelled(Exception):
    pass


# ExportWorker: runs the export in a separate thread and sends its progress to the UI.
class ExportWorker(QThread):
    progress_changed = Signal(int)
    export_finished = Signal()
    export_failed = Signal(str)
    export_cancelled = Signal()

    # export_function does the export, and calls on_progress(percent) to report its progress.
    def __init__(self, export_function, parent=None):
        super().__init__(parent)
        if export_function is None:
            raise ValueError("export_worker.__init__: export_function cannot be None")
        if not callable(export_function):
            raise TypeError("export_worker.__init__: export_function must be callable")
        self.export_function = export_function
        self.last_percent = -1

    def run(self):
        try:
            self.export_function(self._report_progress)
        except ExportCancelled:
            self.export_cancelled.emit()
        # Any error is sent to the UI, otherwise it would stay hidden in this thread.
        except Exception as error:
            self.export_failed.emit(str(error))
        else:
            if self.last_percent != 100:
                self.progress_changed.emit(100)
            self.export_finished.emit()

    def cancel(self):
        self.requestInterruption()

    # Called by the export: stops it if the user cancelled, otherwise sends the progress.
    def _report_progress(self, percent):
        if self.isInterruptionRequested():
            raise ExportCancelled()

        percent = int(percent)
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100

        # Only sends a signal when the percentage changes, so the UI is not flooded.
        if percent != self.last_percent:
            self.last_percent = percent
            self.progress_changed.emit(percent)
