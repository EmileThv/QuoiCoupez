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

    success, encoded_image = cv2.imencode(".jpg", frame)
    if not success:
        raise ValueError("thumbnail.generate_thumbnail: could not encode frame")
    with open(output_path, "wb") as f:
        f.write(encoded_image.tobytes())

    return output_path


# Extracts `count` frames evenly spread over the video (BGR images resized to `height` pixels high).
# Used to display several thumbnails on a clip of the timeline.
def generate_keyframes(file_path, count=10, height=54):
    if not isinstance(file_path, str):
        raise TypeError("generate_keyframes: file_path must be of type str")
    if not isinstance(count, int) or count <= 0:
        raise ValueError("generate_keyframes: count must be a positive int")
    if not isinstance(height, int) or height <= 0:
        raise ValueError("generate_keyframes: height must be a positive int")
    if not os.path.isfile(file_path):
        raise FileNotFoundError("generate_keyframes: file_path does not exist")

    capture = cv2.VideoCapture(file_path)
    if not capture.isOpened():
        capture.release()
        raise ValueError("generate_keyframes: file_path is not a valid video file")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    keyframes = []
    for i in range(count):
        # Middle of each of the `count` equal segments of the video.
        frame_index = int((i + 0.5) * frame_count / count)
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        success, frame = capture.read()
        if not success:
            # Reuses the previous keyframe so the list keeps `count` items.
            if keyframes:
                keyframes.append(keyframes[-1])
            continue
        width = max(1, int(frame.shape[1] * height / frame.shape[0]))
        keyframes.append(cv2.resize(frame, (width, height)))
    capture.release()

    if not keyframes:
        raise ValueError("generate_keyframes: could not read any frame")
    return keyframes
