# Week 5 manual test, run with: python -m tests.Elie_Tests_week5
# Writes assets/test_text.png, test_logo.png, test_logo_overlay.png and test_text_and_logo.png

import os

import cv2
import numpy as np

from effects.video_effects import TextOverlayEffect, ImageOverlayEffect

VIDEO_PATH = os.path.join("assets", "video.mp4")
LOGO_PATH = os.path.join("assets", "test_logo.png")


def save(name, image):
    path = os.path.join("assets", name)
    cv2.imencode(".png", image)[1].tofile(path)
    print(f"    saved {path}")


# A round logo on a transparent background, to check transparency is kept
def make_logo():
    logo = np.zeros((200, 200, 4), dtype=np.uint8)
    cv2.circle(logo, (100, 100), 95, (40, 120, 240, 255), -1)
    cv2.putText(logo, "QC", (38, 128), cv2.FONT_HERSHEY_SIMPLEX, 2.6, (255, 255, 255, 255), 8, cv2.LINE_AA)
    save("test_logo.png", logo)


def main():
    capture = cv2.VideoCapture(VIDEO_PATH)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise SystemExit(f"Cannot read a frame from {VIDEO_PATH}")
    original = frame.copy()
    print(f"Test frame: {frame.shape[1]}x{frame.shape[0]} from {VIDEO_PATH}")

    text_effect = TextOverlayEffect()
    image_effect = ImageOverlayEffect()

    print("Text overlay (with accents)")
    with_text = text_effect.apply(frame, {"text": "Été à Noël - QuoiCoupez", "x": 0.05, "y": 0.8, "color": "#FFD400"})
    save("test_text.png", with_text)

    print("Image/logo overlay (top right, 80% opacity)")
    make_logo()
    with_logo = image_effect.apply(frame, {"image_path": LOGO_PATH, "x": 0.85, "y": 0.05, "width": 0.12, "opacity": 0.8})
    save("test_logo_overlay.png", with_logo)

    print("Both effects chained")
    both = image_effect.apply(with_text, {"image_path": LOGO_PATH, "x": 0.85, "y": 0.05, "width": 0.12})
    save("test_text_and_logo.png", both)

    print("Invalid parameters are refused")
    invalid = [
        (text_effect, {"color": "red"}),
        (text_effect, {"x": 2.0}),
        (image_effect, {"image_path": "assets/missing.png"}),
    ]
    refused = 0
    for effect, params in invalid:
        try:
            effect.apply(frame, params)
        except (ValueError, TypeError, FileNotFoundError) as error:
            refused += 1
            print(f"    refused: {error}")

    unchanged = np.array_equal(frame, original)
    modified = not np.array_equal(with_text, frame) and not np.array_equal(with_logo, frame)
    print(f"\nOriginal frame unchanged: {unchanged}")
    print(f"Effects modified the frame: {modified}")
    print(f"Invalid parameters refused: {refused} / {len(invalid)}")
    ok = unchanged and modified and refused == len(invalid)
    print("Week 5 objective OK: text and image overlays work on a test image." if ok else "Week 5 objective FAILED")


if __name__ == "__main__":
    main()
