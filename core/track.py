import core.clip

# Track class : represents a track (audio or video) of the timeline, containing an ordered list of clips. 
class Track:
    def __init__(self):
        self.clips = []

    # Returns the list of clips
    def get_clips(self):
        return self.clips

    # Sets the list of clips
    def set_clips(self, clips):
        if not isinstance(clips, list):
            raise TypeError("track.set_clips: clips must be of type list")
        self.clips = clips


    # Methods

    # Adds a clip to the track
    def add_clip(self, clip):
        if clip is None:
            raise ValueError("track.add_clip: clip cannot be None")
        if not isinstance(clip, core.clip.Clip):
            raise ValueError("track.add_clip: clip must be of type core.clip.Clip")
        self.clips.append(clip)

    # Removes a clip from the track
    def remove_clip(self, clip):
        if clip is None:
            raise ValueError("track.remove_clip: clip cannot be None")
        if not isinstance(clip, core.clip.Clip):
            raise ValueError("track.remove_clip: clip must be of type core.clip.Clip")
        self.clips.remove(clip)