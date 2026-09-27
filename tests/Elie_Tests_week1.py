# Manual test script of week 1: checks that Project, Track, Media
# and Clip fit together correctly. Not a pytest suite, just run it
# directly and read the printed output.


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
    print(f"Added track, project now has {len(project.get_tracks())} track(s)")

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
    print(f"Added clip to track, duration={clip.get_duration()}s, track now has {len(track.get_clips())} clip(s)")

    model.remove_clip(track, clip)
    print(f"Removed clip, track now has {len(track.get_clips())} clip(s)")

    print("Week 1 objective OK: Project -> Track -> Clip all fit together.")


if __name__ == "__main__":
    main()
