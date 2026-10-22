import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from effects.video_effects import BlurEffect, ColorCorrectionEffect
from video.thumbnail import generate_thumbnail


def save_image(path, image):
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise ValueError("could not encode " + path)
    with open(path, "wb") as f:
        f.write(encoded.tobytes())


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(root, "assets", "video.mp4")
    source_path = os.path.join(root, "assets", "test_thumbnail.jpg")
    generate_thumbnail(video_path, source_path)

    # Read through numpy to avoid cv2.imread problems with accented paths
    frame = cv2.imdecode(np.fromfile(source_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    blurred = BlurEffect().apply(frame, {"intensity": 10})
    corrected = ColorCorrectionEffect().apply(frame, {"brightness": 40, "contrast": 1.3})

    save_image(os.path.join(root, "assets", "test_blur.jpg"), blurred)
    save_image(os.path.join(root, "assets", "test_color.jpg"), corrected)
    print("Original unchanged:", frame is not blurred and frame is not corrected)
    print("Done: compare assets/test_thumbnail.jpg, test_blur.jpg and test_color.jpg")


if __name__ == "__main__":
    main()