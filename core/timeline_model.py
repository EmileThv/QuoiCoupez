import core.project
import core.track
import core.clip

# TimelineModel: centralizes operations on tracks/clips for a project, separate from the UI widget.
class TimelineModel:
    def __init__(self, project):
        if project is None:
            raise ValueError("timeline_model.__init__: project cannot be None")
        if not isinstance(project, core.project.Project):
            raise TypeError("timeline_model.__init__: project must be of type core.project.Project")
        self.project = project


    # Getters

    # Returns the project managed by this model
    def get_project(self):
        return self.project


    # Setters

    # Sets the project managed by this model
    def set_project(self, project):
        if project is None:
            raise ValueError("timeline_model.set_project: project cannot be None")
        if not isinstance(project, core.project.Project):
            raise TypeError("timeline_model.set_project: project must be of type core.project.Project")
        self.project = project


    # Methods

    # Adds a clip to a track of the project
    def add_clip(self, track, clip):
        if track is None:
            raise ValueError("timeline_model.add_clip: track cannot be None")
        if clip is None:
            raise ValueError("timeline_model.add_clip: clip cannot be None")
        if not isinstance(clip, core.clip.Clip):
            raise TypeError("timeline_model.add_clip: clip must be of type core.clip.Clip")
        if not isinstance(track, core.track.Track):
            raise TypeError("timeline_model.add_clip: track must be of type core.track.Track")
        if track not in self.project.get_tracks():
            raise ValueError("timeline_model.add_clip: track is not part of the project")
        
        track.add_clip(clip)

    # Removes a clip from a track of the project
    def remove_clip(self, track, clip):
        if track is None:
            raise ValueError("timeline_model.remove_clip: track cannot be None")
        if clip is None:
            raise ValueError("timeline_model.remove_clip: clip cannot be None")
        if not isinstance(clip, core.clip.Clip):
            raise TypeError("timeline_model.remove_clip: clip must be of type core.clip.Clip")
        if not isinstance(track, core.track.Track):
            raise TypeError("timeline_model.remove_clip: track must be of type core.track.Track")
        if track not in self.project.get_tracks():
            raise ValueError("timeline_model.remove_clip: track is not part of the project")
        
        track.remove_clip(clip)
