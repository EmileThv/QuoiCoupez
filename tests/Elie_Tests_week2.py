# Manual test script of week 2


import sys

from PySide6.QtCore import QCoreApplication, QTimer

from workers.playback_worker import PlaybackWorker

DEFAULT_VIDEO = "assets/video.mp4"
DURATION_MS = 2000


def main():
    # A video path can be given on the command line, otherwise the test video is used.
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = DEFAULT_VIDEO
    app = QCoreApplication(sys.argv)

    worker = PlaybackWorker(video_path)
    received = []
    worker.frame_ready.connect(received.append)

    def print_frame(index):
        print(f"playback_worker: frame {index}")

    worker.position_changed.connect(print_frame)

    # This timer runs on the main thread: if the worker blocked it, no tick would be printed.
    ticks = []

    def on_tick():
        ticks.append(1)
        print(f"main thread alive (tick {len(ticks)})")

    ui_timer = QTimer()
    ui_timer.timeout.connect(on_tick)
    ui_timer.start(250)

    def finish():
        ui_timer.stop()
        worker.stop()
        app.quit()

    QTimer.singleShot(DURATION_MS, finish)
    print(f"Starting playback of '{video_path}' for {DURATION_MS / 1000}s...")
    worker.start()
    worker.play()
    app.exec()

    print(f"\nFrames received by the main thread: {len(received)}")
    if received:
        print(f"Frame size: {received[0].width()}x{received[0].height()}")
    print(f"Main thread ticks during playback: {len(ticks)}")
    if received and ticks:
        print("Week 2 objective OK: worker runs without blocking the UI.")
    else:
        print("Week 2 objective FAILED")


if __name__ == "__main__":
    main()
