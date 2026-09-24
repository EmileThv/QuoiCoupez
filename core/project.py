import core.track
import core.media

# Project class : represents a global state of a project of video montage, containing a list of tracks, total duration, 
# imported media and save path
class Project:
    def __init__(self, name):
        self.name = name
        self.tracks = []
        self.total_duration = 0
        self.media = []
        self.save_path = None

    # Getters

    # Returns the name of the project
    def get_name(self):
        
        return self.name

    # Returns the list of tracks
    def get_tracks(self):
        return self.tracks.copy()

    # Returns the total duration
    def get_total_duration(self):
        return self.total_duration

    # Returns the list of media
    def get_media(self):
        return self.media.copy()

    # Returns the save path
    def get_save_path(self):
        return self.save_path


    # Setters

    # Sets the name of the project
    def set_name(self, name):
        if name is None:
            raise ValueError("project.set_name: name cannot be None")
        if not isinstance(name, str):
            raise TypeError("project.set_name: name must be of type str")
        self.name = name

    # Sets the list of tracks
    def set_tracks(self, tracks):
        if tracks is None:
            raise ValueError("project.set_tracks: tracks cannot be None")
        if not isinstance(tracks, list):
            raise TypeError("project.set_tracks: tracks must be of type list")
        self.tracks = tracks

    # Sets the total duration
    def set_total_duration(self, duration):
        if duration is None:
            raise ValueError("project.set_total_duration: duration cannot be None")
        if not isinstance(duration, int, float):
            raise TypeError("project.set_total_duration: duration must be of type int")
        self.total_duration = duration

    # Sets the list of media
    def set_media(self, media):
        if media is None:
            raise ValueError("project.set_media: media cannot be None")
        if not isinstance(media, list):
            raise TypeError("project.set_media: media must be of type list")
        self.media = media

    # Sets the save path
    def set_save_path(self, path):
        if path is None:
            raise ValueError("project.set_save_path: path cannot be None")
        if not isinstance(path, str):
            raise TypeError("project.set_save_path: path must be of type str")
        self.save_path = path


    # Methods

    # Adds a track to the project
    def add_track(self, track):
        if track is None:
            raise ValueError("project.add_track: track cannot be None")
        elif not isinstance(track, core.track.Track):
            raise TypeError("project.add_track: track must be of type core.track.Track")
        else:
            self.tracks.append(track)

    # Removes a track from the project
    def remove_track(self, track):
        if track is None:
            raise ValueError("project.remove_track: track cannot be None")
        elif not isinstance(track, core.track.Track):
            raise TypeError("project.remove_track: track must be of type core.track.Track")
        else:
            self.tracks.remove(track)

    # Adds a media to the project
    def add_media(self, media):
        if media is None:
            raise ValueError("project.add_media: media cannot be None")
        elif not isinstance(media, core.media.Media):
            raise TypeError("project.add_media: media must be of type core.media.Media")
        else:
            self.media.append(media)

    # Removes a media from the project
    def remove_media(self, media):
        if media is None:
            raise ValueError("project.remove_media: media cannot be None")
        elif not isinstance(media, core.media.Media):
            raise TypeError("project.remove_media: media must be of type core.media.Media")
        else:
            self.media.remove(media)