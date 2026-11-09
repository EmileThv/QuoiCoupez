# Unit tests for core/, run them with: python -m pytest

import pytest

from core.clip import Clip
from core.media import AudioMedia, ImageMedia, Media, VideoMedia
from core.project import Project
from core.timeline_model import ModelSignal, TimelineModel
from core.track import Track


@pytest.fixture
def video():
    return VideoMedia("assets/video.mp4", "video", 20.0, (1920, 1080), 30, "")


@pytest.fixture
def image():
    return ImageMedia("assets/logo.png", "logo", (200, 200), "")


@pytest.fixture
def project():
    return Project("Test project")


# A track that is already part of the project.
@pytest.fixture
def track(project):
    track = Track()
    project.add_track(track)
    return track


@pytest.fixture
def model(project):
    return TimelineModel(project)


# Counts how many times the model sends its `changed` signal.
@pytest.fixture
def signals(model):
    received = []

    def on_changed():
        received.append(1)

    model.changed.connect(on_changed)
    return received


class TestMedia:
    def test_video_media_keeps_its_values(self, video):
        assert video.get_file_path() == "assets/video.mp4"
        assert video.get_name() == "video"
        assert video.get_duration() == 20.0
        assert video.get_resolution() == (1920, 1080)
        assert video.get_fps() == 30
        assert video.get_thumbnail_path() == ""

    def test_audio_media_keeps_its_duration(self):
        audio = AudioMedia("assets/music.mp3", "music", 180.0, "")
        assert audio.get_duration() == 180.0

    def test_image_media_keeps_its_resolution(self, image):
        assert image.get_resolution() == (200, 200)

    def test_media_cannot_be_created_directly(self):
        with pytest.raises(TypeError):
            Media("file.mp4", "file", "")

    @pytest.mark.parametrize("duration, resolution, fps, error", [
        (None, (1920, 1080), 30, ValueError),
        (20.0, None, 30, ValueError),
        (20.0, (1920, 1080), None, ValueError),
        ("20", (1920, 1080), 30, TypeError),
        (20.0, [1920, 1080], 30, TypeError),
        (20.0, (1920, 1080), "30", TypeError),
    ])
    def test_video_media_refuses_bad_values(self, duration, resolution, fps, error):
        with pytest.raises(error):
            VideoMedia("video.mp4", "video", duration, resolution, fps, "")

    @pytest.mark.parametrize("file_path, name, thumbnail_path, error", [
        (None, "video", "", ValueError),
        ("video.mp4", None, "", ValueError),
        ("video.mp4", "video", None, ValueError),
        (42, "video", "", TypeError),
        ("video.mp4", 42, "", TypeError),
        ("video.mp4", "video", 42, TypeError),
    ])
    def test_media_refuses_bad_paths_and_names(self, file_path, name, thumbnail_path, error):
        with pytest.raises(error):
            VideoMedia(file_path, name, 20.0, (1920, 1080), 30, thumbnail_path)

    def test_audio_and_image_media_refuse_bad_values(self):
        with pytest.raises(ValueError):
            AudioMedia("music.mp3", "music", None, "")
        with pytest.raises(TypeError):
            AudioMedia("music.mp3", "music", "180", "")
        with pytest.raises(ValueError):
            ImageMedia("logo.png", "logo", None, "")
        with pytest.raises(TypeError):
            ImageMedia("logo.png", "logo", [200, 200], "")

    def test_media_setters_change_the_values(self, video):
        video.set_file_path("other.mp4")
        video.set_name("other")
        video.set_thumbnail_path("other.png")
        video.set_duration(5)
        video.set_resolution((1280, 720))
        video.set_fps(25)
        assert video.get_file_path() == "other.mp4"
        assert video.get_name() == "other"
        assert video.get_thumbnail_path() == "other.png"
        assert video.get_duration() == 5
        assert video.get_resolution() == (1280, 720)
        assert video.get_fps() == 25

    @pytest.mark.parametrize("setter_name, bad_value, error", [
        ("set_file_path", None, ValueError),
        ("set_file_path", 42, TypeError),
        ("set_name", None, ValueError),
        ("set_name", 42, TypeError),
        ("set_thumbnail_path", None, ValueError),
        ("set_thumbnail_path", 42, TypeError),
        ("set_duration", None, ValueError),
        ("set_duration", "5", TypeError),
        ("set_resolution", None, ValueError),
        ("set_resolution", "1280x720", TypeError),
        ("set_fps", None, ValueError),
        ("set_fps", "25", TypeError),
    ])
    def test_video_media_setters_refuse_bad_values(self, video, setter_name, bad_value, error):
        setter = getattr(video, setter_name)
        with pytest.raises(error):
            setter(bad_value)

    def test_audio_and_image_media_setters(self, image):
        audio = AudioMedia("music.mp3", "music", 180.0, "")
        audio.set_duration(90)
        image.set_resolution((100, 50))
        assert audio.get_duration() == 90
        assert image.get_resolution() == (100, 50)

        with pytest.raises(ValueError):
            audio.set_duration(None)
        with pytest.raises(TypeError):
            audio.set_duration("90")
        with pytest.raises(ValueError):
            image.set_resolution(None)
        with pytest.raises(TypeError):
            image.set_resolution("100x50")


class TestProject:
    def test_new_project_is_empty(self, project):
        assert project.get_name() == "Test project"
        assert project.get_tracks() == []
        assert project.get_media() == []
        assert project.get_total_duration() == 0
        assert project.get_save_path() is None

    def test_add_and_remove_track(self, project):
        track = Track()
        project.add_track(track)
        assert project.get_tracks() == [track]

        project.remove_track(track)
        assert project.get_tracks() == []

    def test_add_and_remove_media(self, project, video):
        project.add_media(video)
        assert project.get_media() == [video]

        project.remove_media(video)
        assert project.get_media() == []

    # The getters give a copy, so changing that copy must not change the project.
    def test_returned_lists_are_copies(self, project, track, video):
        project.add_media(video)

        project.get_tracks().clear()
        project.get_media().clear()

        assert project.get_tracks() == [track]
        assert project.get_media() == [video]

    @pytest.mark.parametrize("method_name", ["add_track", "remove_track", "add_media", "remove_media"])
    def test_add_and_remove_refuse_none(self, project, method_name):
        method = getattr(project, method_name)
        with pytest.raises(ValueError):
            method(None)

    @pytest.mark.parametrize("method_name", ["add_track", "remove_track", "add_media", "remove_media"])
    def test_add_and_remove_refuse_wrong_types(self, project, method_name):
        method = getattr(project, method_name)
        with pytest.raises(TypeError):
            method("not the right type")

    def test_setters_change_the_values(self, project, video):
        track = Track()
        project.set_name("Renamed")
        project.set_tracks([track])
        project.set_media([video])
        project.set_total_duration(12.5)
        project.set_save_path("projects/test.qcp")

        assert project.get_name() == "Renamed"
        assert project.get_tracks() == [track]
        assert project.get_media() == [video]
        assert project.get_total_duration() == 12.5
        assert project.get_save_path() == "projects/test.qcp"

    @pytest.mark.parametrize("setter_name, bad_value, error", [
        ("set_name", None, ValueError),
        ("set_name", 42, TypeError),
        ("set_tracks", None, ValueError),
        ("set_tracks", "tracks", TypeError),
        ("set_media", None, ValueError),
        ("set_media", "media", TypeError),
        ("set_total_duration", None, ValueError),
        ("set_total_duration", "12", TypeError),
        ("set_save_path", None, ValueError),
        ("set_save_path", 42, TypeError),
    ])
    def test_setters_refuse_bad_values(self, project, setter_name, bad_value, error):
        setter = getattr(project, setter_name)
        with pytest.raises(error):
            setter(bad_value)


class TestTrack:
    def test_new_track_is_empty(self):
        assert Track().get_clips() == []

    def test_clips_stay_in_the_order_they_were_added(self, video):
        track = Track()
        first = Clip(video, 0, 5)
        second = Clip(video, 0, 3)
        track.add_clip(first)
        track.add_clip(second)
        assert track.get_clips() == [first, second]

        track.remove_clip(first)
        assert track.get_clips() == [second]

    def test_set_clips(self, video):
        track = Track()
        clip = Clip(video, 0, 5)
        track.set_clips([clip])
        assert track.get_clips() == [clip]

    @pytest.mark.parametrize("method_name", ["add_clip", "remove_clip"])
    def test_add_and_remove_refuse_bad_values(self, method_name):
        method = getattr(Track(), method_name)
        with pytest.raises(ValueError):
            method(None)
        with pytest.raises(TypeError):
            method("not a clip")

    def test_set_clips_refuses_bad_values(self):
        track = Track()
        with pytest.raises(ValueError):
            track.set_clips(None)
        with pytest.raises(TypeError):
            track.set_clips("clips")


class TestClip:
    def test_clip_keeps_its_values(self, video):
        clip = Clip(video, 2, 7, 10)
        assert clip.get_source() is video
        assert clip.get_in_point() == 2
        assert clip.get_out_point() == 7
        assert clip.get_position() == 10
        assert clip.get_effects() == []

    def test_duration_is_out_point_minus_in_point(self, video):
        clip = Clip(video, 2, 7)
        assert clip.get_duration() == 5

    @pytest.mark.parametrize("in_point, out_point", [
        (5, 2),
        (3, 3),
        (-1, 5),
        (0, 25),
    ])
    def test_cannot_create_an_invalid_clip(self, video, in_point, out_point):
        with pytest.raises(ValueError):
            Clip(video, in_point, out_point)

    def test_cannot_create_a_clip_without_a_media(self):
        with pytest.raises(ValueError):
            Clip(None, 0, 5)
        with pytest.raises(TypeError):
            Clip("video.mp4", 0, 5)

    # An image has no duration, so an image clip can last as long as we want.
    def test_image_clip_can_be_as_long_as_wanted(self, image):
        clip = Clip(image, 0, 600)
        assert clip.get_duration() == 600

    def test_set_in_and_out_points(self, video):
        clip = Clip(video, 0, 10)
        clip.set_in_point(4)
        clip.set_out_point(8)
        assert clip.get_in_point() == 4
        assert clip.get_out_point() == 8

    @pytest.mark.parametrize("setter_name, bad_value, error", [
        ("set_in_point", None, ValueError),
        ("set_in_point", "2", TypeError),
        ("set_in_point", -1, ValueError),
        ("set_in_point", 10, ValueError),
        ("set_out_point", None, ValueError),
        ("set_out_point", "8", TypeError),
        ("set_out_point", 0, ValueError),
        ("set_out_point", 21, ValueError),
    ])
    def test_in_and_out_setters_refuse_bad_values(self, video, setter_name, bad_value, error):
        clip = Clip(video, 0, 10)
        setter = getattr(clip, setter_name)
        with pytest.raises(error):
            setter(bad_value)

    # Setting the points one by one would fail here, because 12 is after the old out point.
    def test_trim_changes_both_points_at_once(self, video):
        clip = Clip(video, 0, 10)
        clip.trim(12, 18)
        assert clip.get_in_point() == 12
        assert clip.get_out_point() == 18

    def test_invalid_trim_leaves_the_clip_unchanged(self, video):
        clip = Clip(video, 0, 10)
        with pytest.raises(ValueError):
            clip.trim(8, 4)
        assert clip.get_in_point() == 0
        assert clip.get_out_point() == 10

    def test_set_position(self, video):
        clip = Clip(video, 0, 5)
        clip.set_position(3.5)
        assert clip.get_position() == 3.5

        with pytest.raises(ValueError):
            clip.set_position(None)
        with pytest.raises(TypeError):
            clip.set_position("3")

    def test_set_source(self, video):
        clip = Clip(video, 0, 5)
        other = VideoMedia("other.mp4", "other", 30.0, (1280, 720), 25, "")
        clip.set_source(other)
        assert clip.get_source() is other

        with pytest.raises(ValueError):
            clip.set_source(None)
        with pytest.raises(TypeError):
            clip.set_source("other.mp4")

    def test_add_and_remove_effects(self, video):
        clip = Clip(video, 0, 5)
        clip.add_effect("blur")
        clip.add_effect("text")
        assert clip.get_effects() == ["blur", "text"]

        clip.remove_effect("blur")
        assert clip.get_effects() == ["text"]

        clip.set_effects(["logo"])
        assert clip.get_effects() == ["logo"]

    # The getter gives a copy, so changing that copy must not change the clip.
    def test_returned_effects_are_a_copy(self, video):
        clip = Clip(video, 0, 5)
        clip.add_effect("blur")
        clip.get_effects().clear()
        assert clip.get_effects() == ["blur"]

    def test_effect_methods_refuse_bad_values(self, video):
        clip = Clip(video, 0, 5)
        with pytest.raises(ValueError):
            clip.add_effect(None)
        with pytest.raises(ValueError):
            clip.remove_effect(None)
        with pytest.raises(ValueError):
            clip.set_effects(None)
        with pytest.raises(TypeError):
            clip.set_effects("blur")


class TestModelSignal:
    def test_emit_calls_every_connected_function_in_order(self):
        signal = ModelSignal()
        calls = []

        def first():
            calls.append("first")

        def second():
            calls.append("second")

        signal.connect(first)
        signal.connect(second)
        signal.emit()
        assert calls == ["first", "second"]

    def test_disconnected_function_is_not_called_anymore(self):
        signal = ModelSignal()
        calls = []

        def on_emit():
            calls.append(1)

        signal.connect(on_emit)
        signal.disconnect(on_emit)
        signal.emit()
        assert calls == []

    # A function may disconnect itself while the signal is being sent.
    def test_function_can_disconnect_itself_during_emit(self):
        signal = ModelSignal()
        calls = []

        def once():
            calls.append("once")
            signal.disconnect(once)

        def always():
            calls.append("always")

        signal.connect(once)
        signal.connect(always)
        signal.emit()
        signal.emit()
        assert calls == ["once", "always", "always"]

    def test_refuses_bad_values(self):
        signal = ModelSignal()
        with pytest.raises(TypeError):
            signal.connect("not a function")
        with pytest.raises(ValueError):
            signal.disconnect(print)


class TestTimelineModel:
    def test_refuses_a_missing_or_wrong_project(self, model):
        with pytest.raises(ValueError):
            TimelineModel(None)
        with pytest.raises(TypeError):
            TimelineModel("project")
        with pytest.raises(ValueError):
            model.set_project(None)
        with pytest.raises(TypeError):
            model.set_project("project")

    # The project may already contain clips when the model is created.
    def test_computes_the_total_duration_of_an_existing_project(self, project, track, video):
        track.add_clip(Clip(video, 0, 6, 4))
        model = TimelineModel(project)
        assert model.get_project() is project
        assert project.get_total_duration() == 10

    def test_set_project_sends_the_signal_and_updates_the_duration(self, model, signals, video):
        other_project = Project("Other")
        other_track = Track()
        other_project.add_track(other_track)
        other_track.add_clip(Clip(video, 0, 3, 2))

        model.set_project(other_project)

        assert model.get_project() is other_project
        assert other_project.get_total_duration() == 5
        assert len(signals) == 1

    def test_add_clip(self, model, track, signals, video):
        clip = Clip(video, 0, 5, 3)
        model.add_clip(track, clip)
        assert track.get_clips() == [clip]
        assert model.get_project().get_total_duration() == 8
        assert len(signals) == 1

    def test_cannot_add_the_same_clip_twice(self, model, track, video):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        with pytest.raises(ValueError):
            model.add_clip(track, clip)

    def test_cannot_use_a_track_that_is_not_in_the_project(self, model, video):
        outside_track = Track()
        with pytest.raises(ValueError):
            model.add_clip(outside_track, Clip(video, 0, 5))

    @pytest.mark.parametrize("method_name", ["add_clip", "remove_clip"])
    def test_refuses_missing_or_wrong_track_and_clip(self, model, track, video, method_name):
        method = getattr(model, method_name)
        clip = Clip(video, 0, 5)
        with pytest.raises(ValueError):
            method(None, clip)
        with pytest.raises(ValueError):
            method(track, None)
        with pytest.raises(TypeError):
            method("track", clip)
        with pytest.raises(TypeError):
            method(track, "clip")

    def test_remove_clip(self, model, track, signals, video):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        model.remove_clip(track, clip)
        assert track.get_clips() == []
        assert model.get_project().get_total_duration() == 0
        assert len(signals) == 2

    def test_cannot_remove_a_clip_that_is_not_on_the_track(self, model, track, video):
        with pytest.raises(ValueError):
            model.remove_clip(track, Clip(video, 0, 5))

    def test_move_clip_on_the_same_track(self, model, track, signals, video):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        model.move_clip(track, clip, 10)
        assert clip.get_position() == 10
        assert track.get_clips() == [clip]
        assert model.get_project().get_total_duration() == 15
        assert len(signals) == 2

    def test_move_clip_to_another_track(self, model, project, track, video):
        other_track = Track()
        project.add_track(other_track)
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)

        model.move_clip(track, clip, 2, other_track)

        assert track.get_clips() == []
        assert other_track.get_clips() == [clip]
        assert clip.get_position() == 2

    @pytest.mark.parametrize("bad_position, error", [
        (None, ValueError),
        ("10", TypeError),
        (-1, ValueError),
    ])
    def test_move_clip_refuses_a_bad_position(self, model, track, video, bad_position, error):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        with pytest.raises(error):
            model.move_clip(track, clip, bad_position)
        assert clip.get_position() == 0

    def test_move_clip_refuses_a_bad_target_track(self, model, track, video):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        with pytest.raises(TypeError):
            model.move_clip(track, clip, 2, "track")
        with pytest.raises(ValueError):
            model.move_clip(track, clip, 2, Track())

    def test_move_clip_refuses_a_clip_that_is_not_on_the_track(self, model, track, video):
        with pytest.raises(ValueError):
            model.move_clip(track, Clip(video, 0, 5), 2)

    def test_trimming_the_end_keeps_the_start_in_place(self, model, track, video):
        clip = Clip(video, 0, 10, 5)
        model.add_clip(track, clip)
        model.trim_clip(track, clip, 0, 6)
        assert clip.get_position() == 5
        assert clip.get_duration() == 6
        assert model.get_project().get_total_duration() == 11

    def test_trimming_the_start_keeps_the_end_in_place(self, model, track, video):
        clip = Clip(video, 0, 10, 5)
        model.add_clip(track, clip)
        model.trim_clip(track, clip, 3, 10)
        assert clip.get_position() == 8
        assert clip.get_position() + clip.get_duration() == 15

    # Moving the start back by 4s would put this clip, placed at 1s, before the start of the timeline.
    def test_trim_refuses_to_start_before_zero(self, model, track, signals, video):
        clip = Clip(video, 4, 10, 1)
        model.add_clip(track, clip)
        with pytest.raises(ValueError):
            model.trim_clip(track, clip, 0, 10)
        assert clip.get_in_point() == 4
        assert clip.get_position() == 1
        assert len(signals) == 1

    def test_trim_refuses_invalid_points(self, model, track, video):
        clip = Clip(video, 0, 10)
        model.add_clip(track, clip)
        with pytest.raises(ValueError):
            model.trim_clip(track, clip, 6, 2)
        with pytest.raises(ValueError):
            model.trim_clip(track, clip, 0, 25)
        assert clip.get_out_point() == 10

    def test_trim_refuses_a_clip_that_is_not_on_the_track(self, model, track, video):
        with pytest.raises(ValueError):
            model.trim_clip(track, Clip(video, 0, 5), 1, 4)

    def test_total_duration_is_the_end_of_the_last_clip(self, model, project, track, video):
        other_track = Track()
        project.add_track(other_track)
        model.add_clip(track, Clip(video, 0, 5, 0))
        model.add_clip(other_track, Clip(video, 0, 4, 12))
        model.add_clip(track, Clip(video, 0, 3, 6))
        assert project.get_total_duration() == 16

    # A refused operation must not ask the UI to redraw.
    def test_refused_operations_do_not_send_the_signal(self, model, track, signals, video):
        clip = Clip(video, 0, 5)
        model.add_clip(track, clip)
        with pytest.raises(ValueError):
            model.add_clip(track, clip)
        with pytest.raises(ValueError):
            model.move_clip(track, clip, -2)
        with pytest.raises(ValueError):
            model.remove_clip(Track(), clip)
        assert len(signals) == 1
