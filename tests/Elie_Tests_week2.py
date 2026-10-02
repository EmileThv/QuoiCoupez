# Manual test script of week 2: runs PlaybackWorker for a few seconds
# and checks the main (UI) thread is never blocked meanwhile.
#
#   python -m tests.Elie_Tests_week2 [video_path]

import sys

from PySide6.QtCore import QCoreApplication, QTimer

from workers.playback_worker import PlaybackWorker

DEFAULT_VIDEO = "assets/video.mp4"
DURATION_MS = 2000


def main():
    video_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO
    app = QCoreApplication(sys.argv)

    worker = PlaybackWorker(video_path)
    received = []
    worker.frame_ready.connect(received.append)

    # Ticks on the main thread: if the worker blocked it, these would not print
    ticks = []
    ui_timer = QTimer()
    ui_timer.timeout.connect(lambda: (ticks.append(1), print(f"main thread alive (tick {len(ticks)})")))
    ui_timer.start(250)

    def finish():
        ui_timer.stop()
        worker.stop()
        app.quit()

    QTimer.singleShot(DURATION_MS, finish)
    print(f"Starting playback of '{video_path}' for {DURATION_MS / 1000}s...")
    worker.start()
    app.exec()

    print(f"\nFrames received by the main thread: {len(received)}")
    if received:
        print(f"Frame size: {received[0].width()}x{received[0].height()}")
    print(f"Main thread ticks during playback: {len(ticks)}")
    print("Week 2 objective OK: worker runs without blocking the UI." if received and ticks else "Week 2 objective FAILED")


if __name__ == "__main__":
    main()
