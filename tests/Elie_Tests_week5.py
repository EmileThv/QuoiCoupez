# Manual test script of week 5

import os

import cv2
import numpy as np

from effects.video_effects import TextOverlayEffect, ImageOverlayEffect

VIDEO_PATH = os.path.join("assets", "video.mp4")
LOGO_PATH = os.path.join("assets", "test_logo.png")


def save(name, image):
    path = os.path.join("assets", name)
    # cv2.imwrite fails on Windows when the path has accents, so numpy writes the file instead.
    _, encoded = cv2.imencode(".png", image)
    encoded.tofile(path)
    print(f"    saved {path}")


# Creates a round logo on a transparent background, to check that the transparency is kept.
def make_logo():
    logo = np.zeros((200, 200, 4), dtype=np.uint8)
    orange = (40, 120, 240, 255)
    white = (255, 255, 255, 255)
    cv2.circle(logo, (100, 100), 95, orange, -1)
    cv2.putText(logo, "QC", (38, 128), cv2.FONT_HERSHEY_SIMPLEX, 2.6, white, 8, cv2.LINE_AA)
    save("test_logo.png", logo)


def main():
    capture = cv2.VideoCapture(VIDEO_PATH)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise SystemExit(f"Cannot read a frame from {VIDEO_PATH}")
    original = frame.copy()
    height, width = frame.shape[:2]
    print(f"Test frame: {width}x{height} from {VIDEO_PATH}")

    text_effect = TextOverlayEffect()
    image_effect = ImageOverlayEffect()

    print("Text overlay (with accents)")
    text_params = {
        "text": "Été à Noël - QuoiCoupez",
        "x": 0.05,
        "y": 0.8,
        "color": "#FFD400",
    }
    with_text = text_effect.apply(frame, text_params)
    save("test_text.png", with_text)

    print("Image/logo overlay (top right, 80% opacity)")
    make_logo()
    logo_params = {
        "image_path": LOGO_PATH,
        "x": 0.85,
        "y": 0.05,
        "width": 0.12,
        "opacity": 0.8,
    }
    with_logo = image_effect.apply(frame, logo_params)
    save("test_logo_overlay.png", with_logo)

    print("Both effects chained")
    logo_params["opacity"] = 1.0
    both = image_effect.apply(with_text, logo_params)
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
    text_drawn = not np.array_equal(with_text, frame)
    logo_drawn = not np.array_equal(with_logo, frame)
    modified = text_drawn and logo_drawn
    print(f"\nOriginal frame unchanged: {unchanged}")
    print(f"Effects modified the frame: {modified}")
    print(f"Invalid parameters refused: {refused} / {len(invalid)}")
    if unchanged and modified and refused == len(invalid):
        print("Week 5 objective OK: text and image overlays work on a test image.")
    else:
        print("Week 5 objective FAILED")


if __name__ == "__main__":
    main()
