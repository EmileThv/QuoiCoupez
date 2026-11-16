import re
from abc import ABC, abstractmethod

import numpy as np


# Effect: abstract base class of every effect.
#
# A subclass gives:
# - NAME: the name shown in the effects panel,
# - PARAMS: the description of each parameter, for example
#   {"intensity": {"type": int, "default": 5, "min": 0, "max": 50, "label": "Intensité"}}
#   ("min", "max", "label" and "kind" are optional; "kind" can be "color" or "file" to help the UI;
#   "pattern" + "pattern_hint" check a str value with a regular expression),
# - apply(frame, params): returns a new frame with the effect applied.
#
# An effect object also keeps its own parameters (get_params / set_param), so it can be stored
# in a clip and applied on each frame during playback with apply(frame).
class Effect(ABC):
    NAME = "Effet"
    PARAMS = {}

    def __init__(self, params=None):
        self.params = self.resolve_params(params)

    # Returns the frame with the effect applied. params: values to use instead of the effect's own.
    @abstractmethod
    def apply(self, frame, params=None):
        pass

    # Returns the name shown in the UI
    def get_name(self):
        return self.NAME

    # Returns a copy of the effect's own parameters
    def get_params(self):
        return dict(self.params)

    # Changes one parameter after checking its value
    def set_param(self, name, value):
        new_params = self.get_params()
        new_params[name] = value
        # A new dict is built then swapped, so a playback thread never reads a half-changed one.
        self.params = self.resolve_params(new_params)

    # Default value of every parameter
    @classmethod
    def default_params(cls):
        return {name: spec["default"] for name, spec in cls.PARAMS.items()}

    # Checks the given values and fills in the missing ones with their default value.
    # With params=None, the effect's own parameters are used (when the effect has been created).
    def resolve_params(self, params):
        effect_name = self._error_name()
        if params is None:
            params = getattr(self, "params", None) or {}
        if not isinstance(params, dict):
            raise TypeError(f"{effect_name}.apply: params must be of type dict")

        resolved = self.default_params()
        for name, value in params.items():
            if name not in self.PARAMS:
                raise ValueError(f"{effect_name}.apply: unknown parameter '{name}'")
            _check_param(effect_name, name, value, self.PARAMS[name])
            resolved[name] = value
        return resolved

    # Checks that the frame is a color image made of uint8 values (OpenCV BGR format)
    def check_frame(self, frame):
        effect_name = self._error_name()
        if frame is None:
            raise ValueError(f"{effect_name}.apply: frame cannot be None")
        if not isinstance(frame, np.ndarray):
            raise TypeError(f"{effect_name}.apply: frame must be a numpy array")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(f"{effect_name}.apply: frame must be a color image of shape (h, w, 3)")
        if frame.dtype != np.uint8:
            raise ValueError(f"{effect_name}.apply: frame must contain uint8 values")

    # "BlurEffect" -> "blur_effect", used at the start of error messages
    def _error_name(self):
        name = type(self).__name__
        return "".join("_" + c.lower() if c.isupper() else c for c in name).lstrip("_")

    def __repr__(self):
        return f"{type(self).__name__}({self.params})"


def _check_param(effect_name, name, value, spec):
    expected_type = spec["type"]
    # An int is also accepted where a float is expected, for example 1 instead of 1.0.
    # A bool is refused even though Python considers it an int.
    if isinstance(value, bool) and expected_type is not bool:
        is_right_type = False
    elif expected_type is float:
        is_right_type = isinstance(value, (int, float))
    else:
        is_right_type = isinstance(value, expected_type)
    if not is_right_type:
        raise TypeError(f"{effect_name}.apply: {name} must be of type {expected_type.__name__}")

    if "min" in spec and value < spec["min"]:
        raise ValueError(f"{effect_name}.apply: {name} must be at least {spec['min']}")
    if "max" in spec and value > spec["max"]:
        raise ValueError(f"{effect_name}.apply: {name} must be at most {spec['max']}")
    if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
        raise ValueError(f"{effect_name}.apply: {name} must look like {spec['pattern_hint']}")
