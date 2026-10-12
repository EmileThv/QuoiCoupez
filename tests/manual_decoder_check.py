import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.decoder import get_video_metadata
from video.thumbnail import generate_thumbnail

# Manual verification script for video/decoder.py and video/thumbnail.py.
# Run from the project root: python tests/manual_decoder_check.py

VIDEO_PATH = "assets/video.mp4"
THUMBNAIL_OUTPUT = "assets/test_thumbnail.jpg"


def main():
    print(f"Reading metadata from '{VIDEO_PATH}'...")
    metadata = get_video_metadata(VIDEO_PATH)

    print("Metadata:")
    print(f"  duration   : {metadata['duration']:.2f} seconds")
    print(f"  resolution : {metadata['resolution']}")
    print(f"  fps        : {metadata['fps']:.2f}")

    print(f"\nGenerating thumbnail to '{THUMBNAIL_OUTPUT}'...")
    output_path = generate_thumbnail(VIDEO_PATH, THUMBNAIL_OUTPUT)

    if os.path.isfile(output_path):
        print(f"Thumbnail saved successfully at '{output_path}'")
    else:
        print("Thumbnail generation reported success but file not found!")


if __name__ == "__main__":
    main()