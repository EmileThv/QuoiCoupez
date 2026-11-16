import shutil
import subprocess
import time

import cv2
import pytest

from video.decoder import VideoDecoder, get_video_metadata
from video.thumbnail import generate_keyframes, generate_thumbnail

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg n'est pas installé")

FPS = 25
SECONDS = 2
WIDTH, HEIGHT = 160, 90


# A 2 s video, red during the first second then blue (to check which frame is read).
@pytest.fixture(scope="module")
def video(tmp_path_factory):
    path = tmp_path_factory.mktemp("video") / "rouge_bleu.mp4"
    color = f"s={WIDTH}x{HEIGHT}:r={FPS}:d=1"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=red:{color}", "-f", "lavfi", "-i", f"color=c=blue:{color}",
        "-filter_complex", "[0][1]concat=n=2:v=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ], check=True)
    return str(path)


@pytest.fixture
def not_a_video(tmp_path):
    path = tmp_path / "faux.mp4"
    path.write_text("ceci n'est pas une vidéo")
    return str(path)


# --- Metadata ------------------------------------------------------------------------------

def test_metadata(video):
    meta = get_video_metadata(video)
    assert meta["fps"] == pytest.approx(FPS)
    assert meta["resolution"] == (WIDTH, HEIGHT)
    assert meta["frame_count"] == FPS * SECONDS
    assert meta["duration"] == pytest.approx(SECONDS)


def test_metadata_errors(tmp_path, not_a_video):
    with pytest.raises(TypeError):
        get_video_metadata(42)
    with pytest.raises(FileNotFoundError):
        get_video_metadata(str(tmp_path / "absent.mp4"))
    with pytest.raises(ValueError):
        get_video_metadata(not_a_video)


# --- Decoder -------------------------------------------------------------------------------

def test_frames_are_read_in_order_as_rgb(video):
    with VideoDecoder(video, realtime=False) as decoder:
        frames = list(decoder)
    assert len(frames) == FPS * SECONDS
    assert [index for index, _, _ in frames] == list(range(FPS * SECONDS))
    assert frames[FPS][1] == pytest.approx(1.0)  # time of the frame, in seconds
    red, green, blue = frames[0][2][45, 80]
    assert red > 200 and blue < 50  # RGB order (OpenCV reads BGR)
    red, green, blue = frames[-1][2][45, 80]
    assert blue > 200 and red < 50


def test_seek(video):
    with VideoDecoder(video, realtime=False) as decoder:
        decoder.seek(FPS + 5)
        assert decoder.get_frame_index() == FPS + 5
        frame = decoder.read_frame()
        assert decoder.get_frame_index() == FPS + 6
        assert frame[45, 80, 2] > 200  # blue part
        decoder.seek(0)
        assert decoder.read_frame()[45, 80, 0] > 200  # back to red


def test_seek_errors(video):
    with VideoDecoder(video, realtime=False) as decoder:
        with pytest.raises(TypeError):
            decoder.seek(1.5)
        with pytest.raises(ValueError):
            decoder.seek(-1)
        with pytest.raises(ValueError):
            decoder.seek(FPS * SECONDS)


def test_read_after_the_end_returns_none(video):
    with VideoDecoder(video, realtime=False) as decoder:
        decoder.seek(FPS * SECONDS - 1)
        assert decoder.read_frame() is not None
        assert decoder.read_frame() is None


def test_realtime_respects_the_fps(video):
    with VideoDecoder(video, realtime=True) as decoder:
        decoder.seek(FPS * SECONDS - 10)
        start = time.perf_counter()
        count = sum(1 for _ in decoder)
        elapsed = time.perf_counter() - start
    assert count == 10
    assert elapsed >= 9 / FPS - 0.01


def test_close_twice_is_allowed(video):
    decoder = VideoDecoder(video)
    decoder.close()
    decoder.close()


# --- Thumbnails ----------------------------------------------------------------------------

def test_thumbnail(tmp_path, video):
    output = str(tmp_path / "miniature.jpg")
    assert generate_thumbnail(video, output, frame_index=FPS + 2) == output
    image = cv2.imread(output)
    assert image.shape == (HEIGHT, WIDTH, 3)
    assert image[45, 80, 0] > 200  # BGR: frame of the blue part


def test_thumbnail_errors(tmp_path, video, not_a_video):
    output = str(tmp_path / "miniature.jpg")
    with pytest.raises(TypeError):
        generate_thumbnail(None, output)
    with pytest.raises(TypeError):
        generate_thumbnail(video, 3)
    with pytest.raises(FileNotFoundError):
        generate_thumbnail(str(tmp_path / "absent.mp4"), output)
    with pytest.raises(ValueError):
        generate_thumbnail(not_a_video, output)
    with pytest.raises(ValueError):
        generate_thumbnail(video, output, frame_index=10_000)


def test_keyframes_are_spread_over_the_video(video):
    keyframes = generate_keyframes(video, count=4, height=30)
    assert len(keyframes) == 4
    for frame in keyframes:
        assert frame.shape == (30, round(WIDTH * 30 / HEIGHT), 3)
    # The first two are in the red second, the last two in the blue one (BGR).
    assert [frame[15, 20].argmax() for frame in keyframes] == [2, 2, 0, 0]


def test_keyframes_errors(tmp_path, video, not_a_video):
    with pytest.raises(TypeError):
        generate_keyframes(None)
    with pytest.raises(ValueError):
        generate_keyframes(video, count=0)
    with pytest.raises(ValueError):
        generate_keyframes(video, height=-1)
    with pytest.raises(FileNotFoundError):
        generate_keyframes(str(tmp_path / "absent.mp4"))
    with pytest.raises(ValueError):
        generate_keyframes(not_a_video)
