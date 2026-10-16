import core.media

# Clip class: an excerpt of a source media, with in/out points, position on the track, and applied effects.
class Clip:
    def __init__(self, source, in_point=0, out_point=0, position=0):
        self.source = source
        self.in_point = in_point
        self.out_point = out_point
        self.position = position
        self.effects = []


    # Getters

    # Returns the source media of the clip
    def get_source(self):
        return self.source

    # Returns the in point
    def get_in_point(self):
        return self.in_point

    # Returns the out point
    def get_out_point(self):
        return self.out_point

    # Returns the position of the clip on the track
    def get_position(self):
        return self.position

    # Returns the list of effects applied to the clip
    def get_effects(self):
        return self.effects.copy()

    # Returns the duration of the clip
    def get_duration(self):
        return self.out_point - self.in_point


    # Setters

    # Sets the source media of the clip
    def set_source(self, source):
        if source is None:
            raise ValueError("clip.set_source: source cannot be None")
        elif not isinstance(source, core.media.Media):
            raise TypeError("clip.set_source: source must be of type core.media.Media")
        else:
            self.source = source

    # Sets the in point of the clip
    def set_in_point(self, in_point):
        self._check_points("set_in_point", in_point, self.out_point)
        self.in_point = in_point

    # Sets the out point of the clip
    def set_out_point(self, out_point):
        self._check_points("set_out_point", self.in_point, out_point)
        self.out_point = out_point

    # Sets both points at once, so the clip is never invalid in between
    def trim(self, in_point, out_point):
        self._check_points("trim", in_point, out_point)
        self.in_point = in_point
        self.out_point = out_point

    # Sets the position of the clip on the track
    def set_position(self, position):
        if position is None:
            raise ValueError("clip.set_position: position cannot be None")
        if not isinstance(position, (int, float)):
            raise TypeError("clip.set_position: position must be a number")
        else:
            self.position = position

    # Sets the list of effects applied to the clip
    def set_effects(self, effects):
        if effects is None:
            raise ValueError("clip.set_effects: effects cannot be None")
        elif not isinstance(effects, list):
            raise TypeError("clip.set_effects: effects must be a list")
        else:
            self.effects = effects


    # Adds an effect to the clip
    def add_effect(self, effect):
        if effect is None:
            raise ValueError("clip.add_effect: effect cannot be None")
        else:
            self.effects.append(effect)

    # Removes an effect from the clip
    def remove_effect(self, effect):
        if effect is None:
            raise ValueError("clip.remove_effect: effect cannot be None")
        else:
            self.effects.remove(effect)

    def _check_points(self, method_name, in_point, out_point):
        for name, value in (("in_point", in_point), ("out_point", out_point)):
            if value is None:
                raise ValueError(f"clip.{method_name}: {name} cannot be None")
            if not isinstance(value, (int, float)):
                raise TypeError(f"clip.{method_name}: {name} must be a number")
        if in_point < 0:
            raise ValueError(f"clip.{method_name}: in_point cannot be negative")
        if out_point <= in_point:
            raise ValueError(f"clip.{method_name}: out_point must be greater than in_point")
        # ImageMedia has no duration, so an image clip can be as long as wanted
        if hasattr(self.source, "get_duration") and out_point > self.source.get_duration():
            raise ValueError(f"clip.{method_name}: out_point cannot exceed the source duration")
