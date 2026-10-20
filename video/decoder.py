import os
import cv2
import time

# Opens a video file and returns its metadata (duration, resolution, fps)
def get_video_metadata(file_path):
    if not isinstance(file_path, str):
        raise TypeError("get_video_metadata: file_path must be of type str")
    if not os.path.isfile(file_path):
        raise FileNotFoundError("get_video_metadata: file_path is not a file")

    capture = cv2.VideoCapture(file_path)

    if not capture.isOpened():
        capture.release()
        raise ValueError("get_video_metadata: file_path is not a valid video file")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    capture.release()

    if fps is None or fps <= 0:
        raise ValueError("get_video_metadata: fps is not valid")

    duration = frame_count / fps

    return {
        "duration": duration,
        "resolution": (width, height),
        "fps": fps,
        "frame_count": int(frame_count)
    }
    
    
class VideoDecoder:
    """Décodeur vidéo itérable à la cadence du fps (ou plus rapide avec realtime = False) ."""

    def __init__(self, file_path, realtime=True):
        meta = get_video_metadata(file_path)  # valide aussi le fichier
        self.file_path = file_path
        self.fps = meta["fps"]
        self.duration = meta["duration"]
        self.resolution = meta["resolution"]
        self.frame_count = meta["frame_count"]
        self.realtime = realtime

        self._capture = cv2.VideoCapture(file_path)
        self._frame_index = 0

    def read_frame(self):
        """Frame suivante (RGB, numpy array) ou None en fin de vidéo."""
        ok, frame = self._capture.read()
        if not ok:
            return None
        self._frame_index += 1
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Returns the index of the next frame that read_frame() will return
    def get_frame_index(self):
        return self._frame_index

    # Moves to the given frame: the next read_frame() returns this frame
    def seek(self, frame_index):
        if not isinstance(frame_index, int):
            raise TypeError("video_decoder.seek: frame_index must be of type int")
        if frame_index < 0 or frame_index >= self.frame_count:
            raise ValueError("video_decoder.seek: frame_index is out of range")
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self._frame_index = frame_index

    def __iter__(self):
        start_time = time.perf_counter()
        start_index = self._frame_index
        while True:
            index = self._frame_index
            frame = self.read_frame()
            if frame is None:
                return
            if self.realtime:
                delay = start_time + (index - start_index) / self.fps - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
            yield index, index / self.fps, frame

    def close(self):
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
