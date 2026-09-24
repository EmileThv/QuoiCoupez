# Classe Project : représente l'état global d'un projet de montage
# (liste des pistes, durée totale, médias importés, sauvegarde /
# chargement du projet...).
import core.track

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
        return self.tracks

    # Returns the total duration
    def get_total_duration(self):
        return self.total_duration

    # Returns the list of media
    def get_media(self):
        return self.media

    # Returns the save path
    def get_save_path(self):
        return self.save_path


    # Setters

    # Sets the name of the project
    def set_name(self, name):
        self.name = name

    # Sets the list of tracks
    def set_tracks(self, tracks):
        self.tracks = tracks

    # Sets the total duration
    def set_total_duration(self, duration):
        self.total_duration = duration

    # Sets the list of media
    def set_media(self, media):
        self.media = media

    # Sets the save path
    def set_save_path(self, path):
        self.save_path = path



    # Adds a track to the project
    def add_track(self, track):
        if not isinstance(track, core.track.Track):
            raise TypeError("project.add_track: track must be of type core.track.Track")
        elif track is None:
            raise ValueError("project.add_track: track cannot be None")
        else:
            self.tracks.append(track)

    # Removes a track from the project
    def remove_track(self, track):
        if not isinstance(track, core.track.Track):
            raise TypeError("project.remove_track: track must be of type core.track.Track")
        elif track is None:
            raise ValueError("project.remove_track: track cannot be None")
        else:
            self.tracks.remove(track)

    # Adds a media to the project
    def add_media(self, media):
        if media is None:
            raise ValueError("project.add_media: media cannot be None")
        else:
            self.media.append(media)