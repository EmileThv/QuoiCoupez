# Week 4 manual test, run with: python -m tests.Elie_Tests_week4

from core.project import Project
from core.track import Track
from core.media import VideoMedia
from core.clip import Clip
from core.timeline_model import TimelineModel


def print_state(project, clip):
    print(f"    clip: in={clip.get_in_point()}s out={clip.get_out_point()}s "
          f"position={clip.get_position()}s duration={clip.get_duration()}s")
    print(f"    project total duration: {project.get_total_duration()}s")


def main():
    project = Project("Demo project")
    track = Track()
    project.add_track(track)
    media = VideoMedia("assets/video.mp4", "demo", 20.0, (1920, 1080), 30, "")

    model = TimelineModel(project)
    signals = []
    model.changed.connect(lambda: signals.append(1))

    clip = Clip(media, 0, 10, 5)
    print("Add a 10s clip at 5s")
    model.add_clip(track, clip)
    print_state(project, clip)

    print("Trim the end: out 10s -> 6s (clip gets shorter, start stays)")
    model.trim_clip(track, clip, 0, 6)
    print_state(project, clip)

    print("Trim the start: in 0s -> 2s (clip shifts so its end stays at 11s)")
    model.trim_clip(track, clip, 2, 6)
    print_state(project, clip)

    print("Invalid trims are refused and change nothing")
    for in_point, out_point, reason in ((4, 3, "out before in"), (2, 25, "past the media end"), (-1, 6, "negative in")):
        try:
            model.trim_clip(track, clip, in_point, out_point)
        except ValueError as error:
            print(f"    {reason}: refused ({error})")
    print_state(project, clip)

    ok = clip.get_duration() == 4 and clip.get_position() == 7 and project.get_total_duration() == 11 and len(signals) == 3
    print(f"\nSignals received: {len(signals)} / 3 expected")
    print("Week 4 objective OK: trimming updates the clip and the total duration." if ok else "Week 4 objective FAILED")


if __name__ == "__main__":
    main()
