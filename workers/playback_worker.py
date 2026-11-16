import os
import time

import cv2
from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal
from PySide6.QtGui import QImage

from video.decoder import VideoDecoder


# PlaybackWorker: QThread that reads a video frame by frame at its fps and emits each frame
# as a QImage, without blocking the UI thread. Controlled from the UI with play(), pause(),
# stop_playback() and seek(); stop() ends the thread.
# The effects given to set_effects() are applied to every frame before it is emitted.
class PlaybackWorker(QThread):
    frame_ready = Signal(QImage)
    position_changed = Signal(int)
    playing_changed = Signal(bool)
    playback_finished = Signal()
    effect_failed = Signal(str)

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
        self._effects = []
        self._refresh = False  # True when the effects changed: the paused frame is drawn again
        self._last_error = None  # last effect error sent to the UI (only used by the worker thread)


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

    # Sets the effects applied to each frame (also redraws the current frame when paused)
    def set_effects(self, effects):
        if effects is None:
            raise ValueError("playback_worker.set_effects: effects cannot be None")
        if not isinstance(effects, list):
            raise TypeError("playback_worker.set_effects: effects must be a list")
        self._mutex.lock()
        self._effects = list(effects)
        self._refresh = True
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
        # Last frame shown (before effects), drawn again when the effects change during a pause
        last_frame = None

        while not self.isInterruptionRequested():
            self._mutex.lock()
            # Interruption checked under the lock so that a stop() cannot happen just before the wait
            if (self._seek_target is None and not self._playing and not self._refresh
                    and not self.isInterruptionRequested()):
                self._wake_up.wait(self._mutex)
                self._mutex.unlock()
                resync_clock = True
                continue
            seek_target = self._seek_target
            self._seek_target = None
            refresh = self._refresh
            self._refresh = False
            playing = self._playing
            self._mutex.unlock()

            # Effects changed while paused: the same frame is shown again with the new effects
            if refresh and seek_target is None and not playing:
                if last_frame is not None:
                    self.frame_ready.emit(self._process(last_frame))
                continue

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

            last_frame = frame
            self.frame_ready.emit(self._process(frame))
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

    # Applies the effects to an RGB frame (from VideoDecoder) and converts it to a QImage
    def _process(self, frame):
        self._mutex.lock()
        effects = list(self._effects)
        self._mutex.unlock()
        if not effects:
            return self._to_qimage(frame, QImage.Format_RGB888)

        # The effects work on OpenCV's blue-green-red order.
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        error = None
        for effect in effects:
            try:
                frame = effect.apply(frame)
            # A broken effect (missing image file...) is skipped instead of stopping the playback.
            except Exception as exception:
                error = f"{effect.get_name()} : {exception}"
        # The UI is told once per new error, not on every frame.
        if error != self._last_error:
            self._last_error = error
            if error is not None:
                self.effect_failed.emit(error)
        return self._to_qimage(frame, QImage.Format_BGR888)

    @staticmethod
    def _to_qimage(frame, image_format):
        height, width, _ = frame.shape
        return QImage(frame.data, width, height, frame.strides[0], image_format).copy()
