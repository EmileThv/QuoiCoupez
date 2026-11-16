import copy
import math
import os
import subprocess
import tempfile

import cv2
import ffmpeg
import numpy as np

from core.media import VideoMedia
from core.project import Project

SAMPLE_RATE = 48000
CHANNELS = 2
# Part of the progress bar used by the audio mix; the rest is used by the frames.
AUDIO_PROGRESS = 10
# On Windows, stops a console window from opening for each FFmpeg process.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# VideoExporter: builds the final video of a project with FFmpeg.
#
# - Image: for each frame, the clip of the highest track in the timeline (Piste 1 above Piste 2)
#   is shown with its video effects, resized to the output size; black where there is no clip.
# - Sound: the sound of every clip, with its audio effects, is mixed at its position.
#
# The project is copied when the exporter is created, so the user can keep editing the
# timeline while export() runs in another thread (workers/export_worker.py).
class VideoExporter:
    def __init__(self, project, output_path, fps=None, resolution=None):
        if project is None:
            raise ValueError("video_exporter.__init__: project cannot be None")
        if not isinstance(project, Project):
            raise TypeError("video_exporter.__init__: project must be of type core.project.Project")
        if not isinstance(output_path, str) or output_path == "":
            raise ValueError("video_exporter.__init__: output_path must be a non-empty str")

        self.output_path = output_path
        self.segments = _snapshot(project)
        if not self.segments:
            raise ValueError("la timeline est vide, il n'y a rien à exporter")

        video_segments = [s for s in self.segments if s["video"]]
        first = min(video_segments, key=lambda s: (s["position"], s["track"])) if video_segments else None

        if fps is None:
            fps = first["fps"] if first is not None else 30
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0:
            raise ValueError("video_exporter.__init__: fps must be a positive number")
        if resolution is None:
            resolution = first["resolution"] if first is not None else (1280, 720)
        if (not isinstance(resolution, tuple) or len(resolution) != 2
                or not all(isinstance(v, int) and v > 0 for v in resolution)):
            raise ValueError("video_exporter.__init__: resolution must be a (width, height) tuple of positive ints")

        self.fps = fps
        # H.264 in yuv420p needs an even width and height.
        self.width = resolution[0] - resolution[0] % 2 or 2
        self.height = resolution[1] - resolution[1] % 2 or 2
        self.duration = max(s["position"] + s["duration"] for s in self.segments)
        self.frame_count = max(1, math.ceil(self.duration * self.fps - 1e-9))

    # Builds the file. on_progress(percent) is called regularly; if it raises an exception
    # (ExportCancelled), the export stops and the unfinished file is deleted.
    def export(self, on_progress=None):
        if on_progress is None:
            on_progress = lambda percent: None

        audio_path = None
        process = None
        error_log = tempfile.TemporaryFile()
        finished = False
        try:
            audio = self._mix_audio(on_progress)
            if audio is not None:
                audio_file = tempfile.NamedTemporaryFile(suffix=".f32", delete=False)
                audio_path = audio_file.name
                audio_file.write(audio.T.astype("<f4").tobytes())
                audio_file.close()

            process = subprocess.Popen(
                self._ffmpeg_command(audio_path), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=error_log, creationflags=_NO_WINDOW,
            )
            self._write_frames(process, error_log, on_progress)

            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError(f"FFmpeg a échoué : {_read_log(error_log)}")
            finished = True
            on_progress(100)
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            error_log.close()
            if audio_path is not None and os.path.exists(audio_path):
                os.remove(audio_path)
            if not finished and os.path.exists(self.output_path):
                os.remove(self.output_path)

    # Command line built with ffmpeg-python: raw frames on stdin (+ the mixed sound) -> H.264/AAC.
    def _ffmpeg_command(self, audio_path):
        video_input = ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="bgr24", s=f"{self.width}x{self.height}", framerate=self.fps,
        )
        streams = [video_input]
        options = {"vcodec": "libx264", "pix_fmt": "yuv420p", "preset": "veryfast", "crf": 20,
                   "movflags": "+faststart"}
        if audio_path is not None:
            streams.append(ffmpeg.input(audio_path, format="f32le", ar=SAMPLE_RATE, ac=CHANNELS))
            options.update({"acodec": "aac", "audio_bitrate": "192k"})
        output = ffmpeg.output(*streams, self.output_path, **options)
        return output.overwrite_output().global_args("-loglevel", "error").compile()

    # Mixes the sound of all the clips. Returns None if no clip has sound.
    def _mix_audio(self, on_progress):
        total = round(self.duration * SAMPLE_RATE)
        mix = np.zeros((CHANNELS, total), dtype=np.float32)
        has_audio = False
        audio_cache = {}

        for number, segment in enumerate(self.segments, start=1):
            path = segment["path"]
            if path not in audio_cache:
                audio_cache[path] = _has_audio_stream(path)
            if audio_cache[path]:
                samples = _read_audio(path, segment["in_point"], segment["duration"])
                for effect in segment["audio_effects"]:
                    try:
                        samples = effect.apply(samples, sample_rate=SAMPLE_RATE)
                    except Exception as error:
                        raise RuntimeError(f"effet « {effect.get_name()} » : {error}") from error
                start = round(segment["position"] * SAMPLE_RATE)
                end = min(start + samples.shape[1], total)
                mix[:, start:end] += samples[:, :end - start]
                has_audio = True
            on_progress(AUDIO_PROGRESS * number / len(self.segments))

        if not has_audio:
            return None
        # Several clips at the same time can go above the maximum: the sum is cut at -1 / 1.
        return np.clip(mix, -1.0, 1.0)

    def _write_frames(self, process, error_log, on_progress):
        readers = {}
        black = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Top track first: the first segment that covers a time is the one shown.
        ordered = sorted((s for s in self.segments if s["video"]), key=lambda s: s["track"])
        try:
            for index in range(self.frame_count):
                time = index / self.fps
                segment = next((s for s in ordered if s["position"] <= time < s["position"] + s["duration"]), None)
                frame = black
                if segment is not None:
                    reader = readers.setdefault(id(segment), _ClipReader(segment["path"]))
                    source_time = segment["in_point"] + time - segment["position"]
                    frame = reader.frame_at(round(source_time * segment["fps"]))
                    frame = black if frame is None else self._fit(frame)
                    for effect in segment["video_effects"]:
                        try:
                            frame = effect.apply(frame)
                        except Exception as error:
                            raise RuntimeError(f"effet « {effect.get_name()} » : {error}") from error

                try:
                    process.stdin.write(np.ascontiguousarray(frame).tobytes())
                except OSError:
                    process.wait()
                    raise RuntimeError(f"FFmpeg s'est arrêté : {_read_log(error_log)}")
                # 100 % is only reached once FFmpeg has finished writing the file.
                on_progress(min(99, AUDIO_PROGRESS + (100 - AUDIO_PROGRESS) * (index + 1) / self.frame_count))
        finally:
            for reader in readers.values():
                reader.close()

    # Resizes the frame to the output size, keeping its proportions (black bars around it).
    def _fit(self, frame):
        frame_height, frame_width = frame.shape[:2]
        if (frame_width, frame_height) == (self.width, self.height):
            return frame
        scale = min(self.width / frame_width, self.height / frame_height)
        width = max(1, round(frame_width * scale))
        height = max(1, round(frame_height * scale))
        resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        left = (self.width - width) // 2
        top = (self.height - height) // 2
        canvas[top:top + height, left:left + width] = resized
        return canvas


# Reads the frames of one video in order, and only seeks when it has to (seeking is slow).
class _ClipReader:
    def __init__(self, path):
        self.capture = cv2.VideoCapture(path)
        if not self.capture.isOpened():
            raise RuntimeError(f"impossible d'ouvrir {path}")
        self.frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.next_index = 0
        self.last_frame = None

    # Returns the frame (BGR) at the given index; at the end of the file, the last frame read.
    def frame_at(self, index):
        index = max(0, min(index, self.frame_count - 1))
        if self.last_frame is not None and index == self.next_index - 1:
            return self.last_frame
        if index < self.next_index or index - self.next_index > 30:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            self.next_index = index
        while self.next_index < index:
            self.capture.grab()
            self.next_index += 1
        success, frame = self.capture.read()
        if success:
            self.last_frame = frame
            self.next_index += 1
        return self.last_frame

    def close(self):
        self.capture.release()


# Copies what the export needs from the project: the timeline can change during the export.
def _snapshot(project):
    segments = []
    for track_index, track in enumerate(project.get_tracks()):
        for clip in track.get_clips():
            source = clip.get_source()
            if not hasattr(source, "get_duration"):
                continue  # an image clip has no sound and no frames to read with OpenCV
            effects = copy.deepcopy(clip.get_effects())
            is_video = isinstance(source, VideoMedia)
            segments.append({
                "track": track_index,
                "path": source.get_file_path(),
                "position": clip.get_position(),
                "in_point": clip.get_in_point(),
                "duration": clip.get_duration(),
                "video": is_video,
                "fps": source.get_fps() if is_video else None,
                "resolution": tuple(int(v) for v in source.get_resolution()) if is_video else None,
                "video_effects": [e for e in effects if getattr(e, "KIND", None) == "video"],
                "audio_effects": [e for e in effects if getattr(e, "KIND", None) == "audio"],
            })
    return segments


def _has_audio_stream(path):
    try:
        info = ffmpeg.probe(path)
    except ffmpeg.Error as error:
        raise RuntimeError(f"impossible de lire {path} : {error.stderr.decode(errors='replace')}") from error
    return any(stream.get("codec_type") == "audio" for stream in info.get("streams", []))


# Decodes [in_point, in_point + duration] of the sound of a file as float32 samples
# of shape (CHANNELS, duration * SAMPLE_RATE); silence is added if the sound is shorter.
def _read_audio(path, in_point, duration):
    command = (
        ffmpeg.input(path, ss=in_point, t=duration)
        .output("pipe:", format="f32le", acodec="pcm_f32le", ac=CHANNELS, ar=SAMPLE_RATE)
        .global_args("-loglevel", "error")
        .compile()
    )
    result = subprocess.run(command, capture_output=True, creationflags=_NO_WINDOW)
    if result.returncode != 0:
        raise RuntimeError(f"impossible de lire le son de {path} : {result.stderr.decode(errors='replace')}")

    samples = np.frombuffer(result.stdout, dtype="<f4").reshape(-1, CHANNELS).T
    length = round(duration * SAMPLE_RATE)
    padded = np.zeros((CHANNELS, length), dtype=np.float32)
    padded[:, :min(length, samples.shape[1])] = samples[:, :length]
    return padded


def _read_log(error_log):
    error_log.seek(0)
    text = error_log.read().decode(errors="replace").strip()
    return text[-500:] if text else "erreur inconnue"
