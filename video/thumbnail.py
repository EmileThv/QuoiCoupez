import os
import cv2

def generate_thumbnail(file_path, output_path, frame_index=0):
    if not isinstance(file_path, str):
        raise TypeError("generate_thumbnail: file_path must be of type str")
    if not isinstance(output_path, str):
        raise TypeError("generate_thumbnail: output_path must be of type str")
    if not os.path.isfile(file_path):
        raise FileNotFoundError("generate_thumbnail: file_path does not exist")

    capture = cv2.VideoCapture(file_path)

    if not capture.isOpened():
        capture.release()
        raise ValueError("generate_thumbnail: file_path is not a valid video file")

    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    success, frame = capture.read()
    capture.release()

    if not success:
        raise ValueError("generate_thumbnail: could not read frame")

    written = cv2.imwrite(output_path, frame)
    if not written:
        raise ValueError("generate_thumbnail: could not write thumbnail")

    return output_path