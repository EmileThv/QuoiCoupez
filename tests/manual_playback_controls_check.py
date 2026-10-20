import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication, QTimer

from workers.playback_worker import PlaybackWorker

# Manual verification script for the week 3 playback controls (play / pause / stop / seek).
# Run from the project root: python tests/manual_playback_controls_check.py

VIDEO_PATH = "assets/video.mp4"


def main():
    app = QCoreApplication(sys.argv)
    worker = PlaybackWorker(VIDEO_PATH)
    fps = worker.get_fps()
    print(f"Video: {worker.get_frame_count()} frames at {fps:.2f} fps")

    positions = []
    worker.position_changed.connect(positions.append)
    worker.playing_changed.connect(lambda playing: print(f"  playing_changed: {playing}"))

    results = []

    def check(description, condition):
        def run():
            ok = condition()
            results.append(ok)
            print(f"[{'OK' if ok else 'FAIL'}] {description} (last position: {positions[-1] if positions else None})")
        return run

    def mark_pause():
        positions.append("paused")

    # Sequence of (delay in ms since the previous step, action or check).
    # Seeking with OpenCV can take ~0.5s on a 1080p video, hence the longer delays after a seek.
    timeline = [
        (1000, check("first frame displayed on start, paused", lambda: positions == [0])),
        (0, worker.play),
        (1000, check("about 1s of frames played", lambda: abs(positions[-1] - fps) <= fps * 0.2)),
        (0, worker.pause),
        (0, mark_pause),
        (500, check("no frame emitted while paused", lambda: positions[-1] == "paused")),
        (0, lambda: worker.seek(100)),
        (800, check("seek while paused displays frame 100", lambda: positions[-1] == 100)),
        (0, worker.play),
        (500, check("playback resumes after frame 100", lambda: positions[-1] > 100)),
        (0, worker.stop_playback),
        (300, check("stop goes back to frame 0 and pauses",
                    lambda: positions[-1] == 0 and not worker.is_playing())),
        (0, lambda: worker.seek(worker.get_frame_count() - 5)),
        (0, worker.play),
        (1500, check("end of video reached, playback paused", lambda: not worker.is_playing())),
        (0, worker.play),
        (500, check("play at the end restarts from the beginning",
                    lambda: worker.is_playing() and 0 < positions[-1] < fps)),
    ]

    def run_step(i):
        if i == len(timeline):
            worker.stop()
            app.quit()
            return
        delay, action = timeline[i]

        def execute():
            action()
            run_step(i + 1)

        QTimer.singleShot(delay, execute)

    worker.start()
    run_step(0)
    app.exec()

    print("\nWeek 3 objective OK: play / pause / stop / seek work." if results and all(results)
          else "\nWeek 3 objective FAILED")


if __name__ == "__main__":
    main()
