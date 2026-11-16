# Manual test script of week 6

import os
import sys
import time

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from ui.export_dialog import ExportDialog

OUTPUT_PATH = os.path.abspath(os.path.join("assets", "test_export.mp4"))
SCREENSHOT_PATH = os.path.join("assets", "test_export_dialog.png")


# A fake export that takes about 2 seconds.
def slow_export(on_progress):
    for percent in range(0, 101, 2):
        time.sleep(0.04)
        on_progress(percent)


# A fake export that crashes at 30 %.
def failing_export(on_progress):
    for percent in range(0, 31, 2):
        time.sleep(0.02)
        on_progress(percent)
    raise RuntimeError("disque plein")


# Opens the dialog, clicks "Exporter" and waits for the end of the export.
def run_scenario(name, export_function, cancel_after_ms=None):
    print(name)

    def make_export(path):
        return export_function

    dialog = ExportDialog(make_export)
    dialog.path_edit.setText(OUTPUT_PATH)
    dialog.show()

    # This timer runs on the main thread: if the export blocked it, ticks would stop.
    ticks = []

    def on_tick():
        ticks.append(1)

    ui_timer = QTimer()
    ui_timer.timeout.connect(on_tick)
    ui_timer.start(50)

    progress = []

    def on_progress(percent):
        progress.append(percent)
        if percent == 50 and cancel_after_ms is None:
            dialog.grab().save(SCREENSHOT_PATH)

    dialog.export_button.click()
    dialog.worker.progress_changed.connect(on_progress)

    # Waits here until the export ends, whatever the way it ends.
    loop = QEventLoop()
    dialog.worker.export_finished.connect(loop.quit)
    dialog.worker.export_failed.connect(loop.quit)
    dialog.worker.export_cancelled.connect(loop.quit)
    if cancel_after_ms is not None:
        QTimer.singleShot(cancel_after_ms, dialog.close_button.click)
    loop.exec()
    QApplication.processEvents()
    ui_timer.stop()

    steps_of_10 = []
    for percent in progress:
        if percent % 10 == 0:
            steps_of_10.append(str(percent))

    result = {
        "progress": progress,
        "bar": dialog.progress_bar.value(),
        "status": dialog.status_label.text(),
        "ticks": len(ticks),
    }
    print(f"    progress: {' '.join(steps_of_10)}")
    print(f"    bar: {result['bar']} %, status: {result['status']}")
    print(f"    main thread ticks during export: {result['ticks']}")
    dialog.close()
    return result


def main():
    app = QApplication(sys.argv)

    success = run_scenario("Successful export", slow_export)
    always_increasing = success["progress"] == sorted(success["progress"])
    reached_100 = success["bar"] == 100
    finished = success["status"].startswith("Export terminé")
    ui_not_blocked = success["ticks"] > 10
    success_ok = always_increasing and reached_100 and finished and ui_not_blocked

    cancel = run_scenario("Export cancelled after 0.5s", slow_export, cancel_after_ms=500)
    cancel_ok = cancel["bar"] < 100 and cancel["status"] == "Export annulé."

    failure = run_scenario("Export that fails", failing_export)
    failure_ok = failure["status"] == "Échec de l'export : disque plein"

    print(f"\nScreenshot at 50 %: {SCREENSHOT_PATH}")
    print(f"Success: {success_ok}, cancel: {cancel_ok}, failure: {failure_ok}")
    if success_ok and cancel_ok and failure_ok:
        print("Week 6 objective OK: the export progress is shown in real time.")
    else:
        print("Week 6 objective FAILED")
    app.quit()


if __name__ == "__main__":
    main()
