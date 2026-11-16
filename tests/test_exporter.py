import shutil
import subprocess

import cv2
import ffmpeg
import numpy as np
import pytest

from core.clip import Clip
from core.media import VideoMedia
from core.project import Project
from core.track import Track
from effects.audio_effects import GainEffect
from effects.video_effects import ColorCorrectionEffect
from video.exporter import VideoExporter

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg n'est pas installé")

FPS = 25
SIZE = (160, 120)


# Creates a small video of one color, with a 440 Hz sound or without sound.
def make_video(path, color, seconds=2, with_audio=True):
    command = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "lavfi", "-i", f"color=c={color}:s={SIZE[0]}x{SIZE[1]}:r={FPS}:d={seconds}"]
    if with_audio:
        command += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(command, check=True)
    return VideoMedia(str(path), path.name, float(seconds), SIZE, float(FPS), "")


def make_project(*tracks):
    project = Project("Test")
    for clips in tracks:
        track = Track()
        project.add_track(track)
        for clip in clips:
            track.add_clip(clip)
    return project


def frame_at(path, seconds):
    capture = cv2.VideoCapture(str(path))
    capture.set(cv2.CAP_PROP_POS_FRAMES, round(seconds * FPS))
    success, frame = capture.read()
    capture.release()
    assert success
    return frame


def audio_rms(path):
    output, _ = (
        ffmpeg.input(str(path)).output("pipe:", format="f32le", ac=1, ar=48000)
        .global_args("-loglevel", "error").run(capture_stdout=True)
    )
    samples = np.frombuffer(output, dtype="<f4")
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


@pytest.fixture
def red(tmp_path):
    return make_video(tmp_path / "red.mp4", "red")


@pytest.fixture
def blue(tmp_path):
    return make_video(tmp_path / "blue.mp4", "blue")


def test_export_produces_video_and_sound(tmp_path, red, blue):
    output = tmp_path / "out.mp4"
    project = make_project([Clip(red, 0, 1, 0)], [Clip(blue, 0, 2, 0.5)])
    progress = []
    VideoExporter(project, str(output)).export(progress.append)

    info = ffmpeg.probe(str(output))
    streams = {s["codec_type"]: s for s in info["streams"]}
    assert streams["video"]["codec_name"] == "h264"
    assert (streams["video"]["width"], streams["video"]["height"]) == SIZE
    assert streams["audio"]["codec_name"] == "aac"
    assert float(info["format"]["duration"]) == pytest.approx(2.5, abs=0.1)
    assert progress[-1] == 100
    assert progress == sorted(progress)


def test_top_track_wins_and_gaps_are_black(tmp_path, red, blue):
    output = tmp_path / "out.mp4"
    # Piste 1: red from 1 s to 2 s. Piste 2: blue from 0.5 s to 2.5 s.
    project = make_project([Clip(red, 0, 1, 1)], [Clip(blue, 0, 2, 0.5)])
    VideoExporter(project, str(output)).export()

    assert frame_at(output, 0.2).mean() < 10  # nothing: black
    assert frame_at(output, 0.7)[60, 80].argmax() == 0  # blue only (BGR: index 0 = blue)
    assert frame_at(output, 1.5)[60, 80].argmax() == 2  # red is on the top track


def test_video_effects_are_applied(tmp_path, blue):
    plain = tmp_path / "plain.mp4"
    brighter = tmp_path / "brighter.mp4"
    VideoExporter(make_project([Clip(blue, 0, 1, 0)]), str(plain)).export()
    clip = Clip(blue, 0, 1, 0)
    clip.add_effect(ColorCorrectionEffect({"brightness": 80}))
    VideoExporter(make_project([clip]), str(brighter)).export()
    assert frame_at(brighter, 0.5).mean() > frame_at(plain, 0.5).mean() + 40


def test_audio_effects_are_applied(tmp_path, red):
    plain = tmp_path / "plain.mp4"
    quiet = tmp_path / "quiet.mp4"
    VideoExporter(make_project([Clip(red, 0, 2, 0)]), str(plain)).export()
    clip = Clip(red, 0, 2, 0)
    clip.add_effect(GainEffect({"gain_db": -20.0}))
    VideoExporter(make_project([clip]), str(quiet)).export()
    assert audio_rms(quiet) / audio_rms(plain) == pytest.approx(0.1, rel=0.15)


def test_trimmed_clip_sound_starts_at_its_in_point(tmp_path, tmp_path_factory):
    source = make_video(tmp_path / "src.mp4", "green", seconds=2, with_audio=True)
    output = tmp_path / "out.mp4"
    VideoExporter(make_project([Clip(source, 1.5, 2, 0)]), str(output)).export()
    assert float(ffmpeg.probe(str(output))["format"]["duration"]) == pytest.approx(0.5, abs=0.1)


def test_silent_sources_give_a_file_without_sound(tmp_path):
    silent = make_video(tmp_path / "silent.mp4", "white", with_audio=False)
    output = tmp_path / "out.mp4"
    VideoExporter(make_project([Clip(silent, 0, 1, 0)]), str(output)).export()
    types = [s["codec_type"] for s in ffmpeg.probe(str(output))["streams"]]
    assert types == ["video"]


def test_cancel_deletes_the_unfinished_file(tmp_path, red):
    output = tmp_path / "out.mp4"

    class Cancelled(Exception):
        pass

    def on_progress(percent):
        if percent > 50:
            raise Cancelled()

    with pytest.raises(Cancelled):
        VideoExporter(make_project([Clip(red, 0, 2, 0)]), str(output)).export(on_progress)
    assert not output.exists()


def test_broken_effect_fails_with_its_name(tmp_path, red):
    from effects.video_effects import ImageOverlayEffect
    clip = Clip(red, 0, 1, 0)
    clip.add_effect(ImageOverlayEffect({"image_path": str(tmp_path / "missing.png")}))
    output = tmp_path / "out.mp4"
    with pytest.raises(RuntimeError, match="Image / logo"):
        VideoExporter(make_project([clip]), str(output)).export()
    assert not output.exists()


def test_project_is_copied_when_the_exporter_is_created(tmp_path, red):
    clip = Clip(red, 0, 1, 0)
    exporter = VideoExporter(make_project([clip]), str(tmp_path / "out.mp4"))
    clip.set_position(10)
    clip.add_effect(ColorCorrectionEffect())
    assert exporter.duration == 1
    assert exporter.segments[0]["video_effects"] == []


def test_bad_arguments(tmp_path, red):
    with pytest.raises(ValueError):
        VideoExporter(make_project([]), str(tmp_path / "out.mp4"))
    with pytest.raises(TypeError):
        VideoExporter("projet", str(tmp_path / "out.mp4"))
    with pytest.raises(ValueError):
        VideoExporter(make_project([Clip(red, 0, 1, 0)]), "")
    with pytest.raises(ValueError):
        VideoExporter(make_project([Clip(red, 0, 1, 0)]), str(tmp_path / "o.mp4"), fps=0)
