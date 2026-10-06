# Manual test script of week 3hg    

from core.project import Project
from core.track import Track
from core.media import VideoMedia
from core.clip import Clip
from core.timeline_model import TimelineModel


def print_tracks(project, names):
    for index, track in enumerate(project.get_tracks()):
        clips = ", ".join(f"{names[clip]} @ {clip.get_position()}s" for clip in track.get_clips())
        print(f"    Track {index + 1}: [{clips}]")


def main():
    project = Project("Demo project")
    track_1, track_2 = Track(), Track()
    project.add_track(track_1)
    project.add_track(track_2)

    media = VideoMedia("assets/video.mp4", "demo", 20.0, (1920, 1080), 30, "")
    clip_a = Clip(media, 0, 5, 0)
    clip_b = Clip(media, 0, 3, 6)
    names = {clip_a: "A", clip_b: "B"}

    model = TimelineModel(project)

    # Stands in for timeline_widget.refresh()
    signals = []
    model.changed.connect(lambda: (signals.append(1), print(f"    -> changed signal received ({len(signals)})")))

    print("Add clips A and B on track 1")
    model.add_clip(track_1, clip_a)
    model.add_clip(track_1, clip_b)
    print_tracks(project, names)

    print("Move B to 10s on the same track")
    model.move_clip(track_1, clip_b, 10)
    print_tracks(project, names)

    print("Move A to 2s on track 2")
    model.move_clip(track_1, clip_a, 2, track_2)
    print_tracks(project, names)

    print("Delete B")
    model.remove_clip(track_1, clip_b)
    print_tracks(project, names)

    print("Invalid move (negative position) is refused without signal")
    try:
        model.move_clip(track_2, clip_a, -3)
    except ValueError as error:
        print(f"    refused: {error}")
    print_tracks(project, names)

    expected = 5
    print(f"\nSignals received: {len(signals)} / {expected} expected")
    print("Week 3 objective OK: the model notifies every change." if len(signals) == expected else "Week 3 objective FAILED")


if __name__ == "__main__":
    main()
