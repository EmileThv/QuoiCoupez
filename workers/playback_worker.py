import os
import time

from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal
from PySide6.QtGui import QImage

from video.decoder import VideoDecoder


# PlaybackWorker: QThread that reads a video frame by frame at its fps and emits each frame
# as a QImage, without blocking the UI thread. Controlled from the UI with play(), pause(),
# stop_playback() and seek(); stop() ends the thread.
class PlaybackWorker(QThread):
    frame_ready = Signal(QImage)
    position_changed = Signal(int)
    playing_changed = Signal(bool)
    playback_finished = Signal()

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        if video_path is None:
            raise ValueError("playback_worker.__init__: video_path cannot be None")
        if not isinstance(video_path, str):
            raise TypeError("playback_worker.__init__: video_path must be of type str")
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"playback_worker.__init__: no file at {video_path}")

        # Opened here so an invalid file raises in the caller, not in the worker thread
        decoder = VideoDecoder(video_path, realtime=False)
        self.fps = decoder.fps
        self.frame_count = decoder.frame_count
        decoder.close()

        self.video_path = video_path

        # Shared state between the UI thread and the worker thread, protected by _mutex.
        # _wake_up interrupts the worker when it is paused or waiting for the next frame.
        self._mutex = QMutex()
        self._wake_up = QWaitCondition()
        self._playing = False
        self._at_end = False
        self._seek_target = 0  # displays the first frame as soon as the thread starts


    # Getters

    # Returns the number of frames of the video
    def get_frame_count(self):
        return self.frame_count

    # Returns the frame rate of the video
    def get_fps(self):
        return self.fps

    # Returns True if the video is playing
    def is_playing(self):
        self._mutex.lock()
        playing = self._playing
        self._mutex.unlock()
        return playing


    # Controls (called from the UI thread)

    # Starts or resumes playback (from the beginning if the end was reached)
    def play(self):
        self._mutex.lock()
        if self._at_end:
            self._at_end = False
            self._seek_target = 0
        self._mutex.unlock()
        self._set_playing(True)

    # Pauses playback on the current frame
    def pause(self):
        self._set_playing(False)

    # Stops playback and goes back to the first frame
    def stop_playback(self):
        self._set_playing(False)
        self.seek(0)

    # Moves to the given frame (displayed even when paused)
    def seek(self, frame_index):
        if frame_index is None:
            raise ValueError("playback_worker.seek: frame_index cannot be None")
        if not isinstance(frame_index, int):
            raise TypeError("playback_worker.seek: frame_index must be of type int")
        frame_index = max(0, min(frame_index, self.frame_count - 1))

        self._mutex.lock()
        self._seek_target = frame_index
        self._at_end = False
        self._wake_up.wakeAll()
        self._mutex.unlock()

    # Ends the thread and waits for it to finish
    def stop(self):
        self.requestInterruption()
        self._mutex.lock()
        self._wake_up.wakeAll()
        self._mutex.unlock()
        self.wait()


    # Thread loop: waits while paused, applies seeks, emits frames at the video's fps
    def run(self):
        decoder = VideoDecoder(self.video_path, realtime=False)
        # Time reference: frame `clock_index` is due at `clock_start`, then one frame every 1/fps.
        # It is reset after each pause or seek.
        clock_start = 0
        clock_index = 0
        resync_clock = True
        # Frame decoded while a pause was requested: displayed on the next play instead of skipped
        pending_frame = None

        while not self.isInterruptionRequested():
            self._mutex.lock()
            # Interruption checked under the lock so that a stop() cannot happen just before the wait
            if self._seek_target is None and not self._playing and not self.isInterruptionRequested():
                self._wake_up.wait(self._mutex)
                self._mutex.unlock()
                resync_clock = True
                continue
            seek_target = self._seek_target
            self._seek_target = None
            self._mutex.unlock()

            if seek_target is not None:
                decoder.seek(seek_target)
                pending_frame = None
                resync_clock = True

            index = decoder.get_frame_index() if pending_frame is None else pending_frame[0]
            if resync_clock:
                clock_start = time.perf_counter()
                clock_index = index
                resync_clock = False

            # Waits for the time of this frame; a pause, seek or stop() interrupts the wait
            delay_ms = int((clock_start + (index - clock_index) / self.fps - time.perf_counter()) * 1000)
            if seek_target is None and delay_ms > 0:
                self._mutex.lock()
                interrupted = self._wake_up.wait(self._mutex, delay_ms)
                self._mutex.unlock()
                if interrupted:
                    continue

            if pending_frame is None:
                frame = decoder.read_frame()
            else:
                frame = pending_frame[1]
                pending_frame = None
            if frame is None:
                self._mutex.lock()
                self._at_end = True
                self._mutex.unlock()
                self._set_playing(False)
                self.playback_finished.emit()
                continue

            # A pause requested during decoding: keeps the frame instead of showing it after the pause
            self._mutex.lock()
            paused = not self._playing and self._seek_target is None
            self._mutex.unlock()
            if paused and seek_target is None:
                pending_frame = (index, frame)
                continue

            self.frame_ready.emit(self._to_qimage(frame))
            self.position_changed.emit(index)

        decoder.close()

    # Changes the playing state and wakes the worker thread up
    def _set_playing(self, playing):
        self._mutex.lock()
        changed = self._playing != playing
        self._playing = playing
        self._wake_up.wakeAll()
        self._mutex.unlock()
        if changed:
            self.playing_changed.emit(playing)

    # Converts an RGB frame (from VideoDecoder) to a QImage
    @staticmethod
    def _to_qimage(frame):
        height, width, _ = frame.shape
        return QImage(frame.data, width, height, 3 * width, QImage.Format_RGB888).copy()
