import core.project
import core.track
import core.clip


# Minimal Qt-like signal, so core/ stays free of PySide6
class ModelSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        if not callable(callback):
            raise TypeError("model_signal.connect: callback must be callable")
        self.callbacks.append(callback)

    def disconnect(self, callback):
        if callback not in self.callbacks:
            raise ValueError("model_signal.disconnect: callback is not connected")
        self.callbacks.remove(callback)

    def emit(self):
        for callback in list(self.callbacks):
            callback()


# Operations on the project's tracks/clips; emits `changed` after each one so the UI can redraw
class TimelineModel:
    def __init__(self, project):
        if project is None:
            raise ValueError("timeline_model.__init__: project cannot be None")
        if not isinstance(project, core.project.Project):
            raise TypeError("timeline_model.__init__: project must be of type core.project.Project")
        self.project = project
        self.changed = ModelSignal()
        self._update_total_duration()

    def get_project(self):
        return self.project

    def set_project(self, project):
        if project is None:
            raise ValueError("timeline_model.set_project: project cannot be None")
        if not isinstance(project, core.project.Project):
            raise TypeError("timeline_model.set_project: project must be of type core.project.Project")
        self.project = project
        self._notify()

    def add_clip(self, track, clip):
        self._check_track_and_clip("add_clip", track, clip)
        if clip in track.get_clips():
            raise ValueError("timeline_model.add_clip: clip is already on this track")

        track.add_clip(clip)
        self._notify()

    def remove_clip(self, track, clip):
        self._check_track_and_clip("remove_clip", track, clip)
        if clip not in track.get_clips():
            raise ValueError("timeline_model.remove_clip: clip is not on this track")

        track.remove_clip(clip)
        self._notify()

    def move_clip(self, track, clip, position, target_track=None):
        self._check_track_and_clip("move_clip", track, clip)
        if clip not in track.get_clips():
            raise ValueError("timeline_model.move_clip: clip is not on this track")
        if position is None:
            raise ValueError("timeline_model.move_clip: position cannot be None")
        if not isinstance(position, (int, float)):
            raise TypeError("timeline_model.move_clip: position must be a number")
        if position < 0:
            raise ValueError("timeline_model.move_clip: position cannot be negative")
        if target_track is None:
            target_track = track
        if not isinstance(target_track, core.track.Track):
            raise TypeError("timeline_model.move_clip: target_track must be of type core.track.Track")
        if target_track not in self.project.get_tracks():
            raise ValueError("timeline_model.move_clip: target_track is not part of the project")

        clip.set_position(position)
        if target_track is not track:
            track.remove_clip(clip)
            target_track.add_clip(clip)
        self._notify()

    def trim_clip(self, track, clip, in_point, out_point):
        self._check_track_and_clip("trim_clip", track, clip)
        if clip not in track.get_clips():
            raise ValueError("timeline_model.trim_clip: clip is not on this track")

        old_in_point, old_out_point = clip.get_in_point(), clip.get_out_point()
        clip.trim(in_point, out_point)

        # Trimming the start shifts the clip so its end stays in place on the timeline
        position = clip.get_position() + (in_point - old_in_point)
        if position < 0:
            clip.trim(old_in_point, old_out_point)
            raise ValueError("timeline_model.trim_clip: the clip would start before 0")

        clip.set_position(position)
        self._notify()

    def _update_total_duration(self):
        end = 0
        for track in self.project.get_tracks():
            for clip in track.get_clips():
                end = max(end, clip.get_position() + clip.get_duration())
        self.project.set_total_duration(end)

    def _notify(self):
        self._update_total_duration()
        self.changed.emit()

    def _check_track_and_clip(self, method_name, track, clip):
        if track is None:
            raise ValueError(f"timeline_model.{method_name}: track cannot be None")
        if clip is None:
            raise ValueError(f"timeline_model.{method_name}: clip cannot be None")
        if not isinstance(clip, core.clip.Clip):
            raise TypeError(f"timeline_model.{method_name}: clip must be of type core.clip.Clip")
        if not isinstance(track, core.track.Track):
            raise TypeError(f"timeline_model.{method_name}: track must be of type core.track.Track")
        if track not in self.project.get_tracks():
            raise ValueError(f"timeline_model.{method_name}: track is not part of the project")
