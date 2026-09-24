from abc import ABC, abstractmethod

# Media class : abstract base class representing a source media file
# (video, audio or image) that can be referenced by one or more Clips.
class Media(ABC):
    @abstractmethod
    def __init__(self, file_path, name, thumbnail_path):
        if file_path is None:
            raise ValueError("media.__init__: file_path cannot be None")
        if name is None:
            raise ValueError("media.__init__: name cannot be None")
        if thumbnail_path is None:
            raise ValueError("media.__init__: thumbnail_path cannot be None")
        if not isinstance(file_path, str):
            raise TypeError("media.__init__: file_path must be of type str")
        if not isinstance(name, str):
            raise TypeError("media.__init__: name must be of type str")
        if not isinstance(thumbnail_path, str):
            raise TypeError("media.__init__: thumbnail_path must be of type str")
        
        self.file_path = file_path
        self.name = name
        self.thumbnail_path = thumbnail_path


    # Getters

    # Returns the file path
    def get_file_path(self):
        return self.file_path

    # Returns the media name
    def get_name(self):
        return self.name

    # Returns the thumbnail path
    def get_thumbnail_path(self):
        return self.thumbnail_path


    # Setters

    # Sets the file path
    def set_file_path(self, file_path):
        if file_path is None:
            raise ValueError("media.set_file_path: file_path cannot be None")
        if not isinstance(file_path, str):
            raise TypeError("media.set_file_path: file_path must be of type str")
        self.file_path = file_path

    # Sets the media name
    def set_name(self, name):
        if name is None:
            raise ValueError("media.set_name: name cannot be None")
        if not isinstance(name, str):
            raise TypeError("media.set_name: name must be of type str")
        self.name = name

    # Sets the thumbnail path
    def set_thumbnail_path(self, thumbnail_path):
        if thumbnail_path is None:
            raise ValueError("media.set_thumbnail_path: thumbnail_path cannot be None")
        if not isinstance(thumbnail_path, str):
            raise TypeError("media.set_thumbnail_path: thumbnail_path must be of type str")
        self.thumbnail_path = thumbnail_path


# VideoMedia class : a media file containing video (and usually audio).
class VideoMedia(Media):
    def __init__(self, file_path, name, duration, resolution, fps, thumbnail_path):
        if duration is None:
            raise ValueError("video_media.__init__: duration cannot be None")
        if resolution is None:
            raise ValueError("video_media.__init__: resolution cannot be None")
        if fps is None:
            raise ValueError("video_media.__init__: fps cannot be None")
        if not isinstance(duration, (int, float)):
            raise TypeError("video_media.__init__: duration must be a number or None")
        if not isinstance(resolution, tuple):
            raise TypeError("video_media.__init__: resolution must be a tuple or None")
        if not isinstance(fps, (int, float)):
            raise TypeError("video_media.__init__: fps must be a number or None")
        
        super().__init__(file_path, name, thumbnail_path)
        self.duration = duration
        self.resolution = resolution
        self.fps = fps


    # Getters

    # Returns the duration of the video (in seconds)
    def get_duration(self):
        return self.duration

    # Returns the resolution of the video as a (width, height) tuple
    def get_resolution(self):
        return self.resolution

    # Returns the frame rate of the video
    def get_fps(self):
        return self.fps
    

    # Setters

    # Sets the duration of the video
    def set_duration(self, duration):
        if duration is None:
            raise ValueError("video_media.set_duration: duration cannot be None")
        if not isinstance(duration, (int, float)):
            raise TypeError("video_media.set_duration: duration must be a number or None")
        self.duration = duration

    # Sets the resolution of the video
    def set_resolution(self, resolution):
        if resolution is None:
            raise ValueError("video_media.set_resolution: resolution cannot be None")
        if not isinstance(resolution, tuple):
            raise TypeError("video_media.set_resolution: resolution must be a tuple or None")
        self.resolution = resolution

    # Sets the frame rate of the video
    def set_fps(self, fps):
        if fps is None:
            raise ValueError("video_media.set_fps: fps cannot be None")
        if not isinstance(fps, (int, float)):
            raise TypeError("video_media.set_fps: fps must be a number or None")
        self.fps = fps


# AudioMedia class : a media file containing only audio.
class AudioMedia(Media):
    def __init__(self, file_path, name, duration, thumbnail_path):
        if duration is None:
            raise ValueError("audio_media.__init__: duration cannot be None")
        if not isinstance(duration, (int, float)):
            raise TypeError("audio_media.__init__: duration must be a number or None")
        
        super().__init__(file_path, name, thumbnail_path)
        self.duration = duration

    # Returns the duration of the audio (in seconds)
    def get_duration(self):
        return self.duration

    # Sets the duration of the audio
    def set_duration(self, duration):
        if duration is None:
            raise ValueError("audio_media.set_duration: duration cannot be None")
        if not isinstance(duration, (int, float)):
            raise TypeError("audio_media.set_duration: duration must be a number or None")
        self.duration = duration


# ImageMedia class : a static image media file.
class ImageMedia(Media):
    def __init__(self, file_path, name, resolution, thumbnail_path):
        if resolution is None:
            raise ValueError("image_media.__init__: resolution cannot be None")
        if not isinstance(resolution, tuple):
            raise TypeError("image_media.__init__: resolution must be a tuple or None")
        
        super().__init__(file_path, name, thumbnail_path)
        self.resolution = resolution

    # Returns the resolution of the image as a (width, height) tuple
    def get_resolution(self):
        return self.resolution

    # Sets the resolution of the image
    def set_resolution(self, resolution):
        if resolution is None:
            raise ValueError("image_media.set_resolution: resolution cannot be None")
        if not isinstance(resolution, tuple):
            raise TypeError("image_media.set_resolution: resolution must be a tuple or None")
        self.resolution = resolution