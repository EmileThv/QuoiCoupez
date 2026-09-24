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
        return self.effects

    # Returns the duration of the clip
    def get_duration(self):
        return self.out_point - self.in_point


    # Setters

    # Sets the source media of the clip
    def set_source(self, source):
        if source is None:
            raise ValueError("clip.set_source: source cannot be None")
        else:
            self.source = source

    # Sets the in point of the clip
    def set_in_point(self, in_point):
        if not isinstance(in_point, (int, float)):
            raise TypeError("clip.set_in_point: in_point must be a number")
        else:
            self.in_point = in_point

    # Sets the out point of the clip
    def set_out_point(self, out_point):
        if not isinstance(out_point, (int, float)):
            raise TypeError("clip.set_out_point: out_point must be a number")
        else:
            self.out_point = out_point

    # Sets the position of the clip on the track
    def set_position(self, position):
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
