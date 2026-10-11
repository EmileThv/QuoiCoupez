import os
import cv2

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
        "fps": fps
    }