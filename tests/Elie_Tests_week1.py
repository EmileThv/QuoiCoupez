# Manual test script of week 1


from core.project import Project
from core.track import Track
from core.media import VideoMedia
from core.clip import Clip
from core.timeline_model import TimelineModel


def main():
    project = Project("Demo project")
    print(f"Created project: {project.get_name()}")

    track = Track()
    project.add_track(track)
    track_count = len(project.get_tracks())
    print(f"Added track, project now has {track_count} track(s)")

    media = VideoMedia(
        file_path="assets/demo.mp4",
        name="demo",
        duration=10.0,
        resolution=(1920, 1080),
        fps=30,
        thumbnail_path="assets/demo_thumb.png",
    )
    project.add_media(media)
    print(f"Added media: {media.get_name()} ({media.get_resolution()} @ {media.get_fps()}fps)")

    clip = Clip(source=media, in_point=0, out_point=5, position=0)
    model = TimelineModel(project)
    model.add_clip(track, clip)
    clip_count = len(track.get_clips())
    print(f"Added clip to track, duration={clip.get_duration()}s, track now has {clip_count} clip(s)")

    model.remove_clip(track, clip)
    clip_count = len(track.get_clips())
    print(f"Removed clip, track now has {clip_count} clip(s)")

    print("Week 1 objective OK: Project -> Track -> Clip all fit together.")


if __name__ == "__main__":
    main()
