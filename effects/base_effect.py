from abc import ABC, abstractmethod

# Registre des effets disponibles : nom -> classe. Alimenté par le décorateur register_effect.
_EFFECT_REGISTRY = {}


# Effect class : abstract base class of every effect. A concrete effect declares its name and the
# specification of its parameters, and implements apply(frame, params).
#
# PARAMS describes the parameters for the UI (effects_panel), as {param_name: spec}, with spec a dict:
#   {"type": int | float | str | bool, "default": ..., "min": ..., "max": ..., "label": "..."}
# ("min", "max" and "label" are optional and only used by numeric parameters / display).
class Effect(ABC):
    NAME = None
    PARAMS = {}

    # Applies the effect on a frame (BGR numpy array) and returns the modified frame
    @abstractmethod
    def apply(self, frame, params):
        pass

    # Returns the display name of the effect
    @classmethod
    def get_name(cls):
        return cls.NAME if cls.NAME is not None else cls.__name__

    # Returns the parameter specifications
    @classmethod
    def get_param_specs(cls):
        return dict(cls.PARAMS)

    # Returns the default value of every parameter
    @classmethod
    def get_default_params(cls):
        return {name: spec["default"] for name, spec in cls.PARAMS.items()}

    # Returns params completed with default values, and checked against the specifications
    @classmethod
    def resolve_params(cls, params=None):
        if params is not None and not isinstance(params, dict):
            raise TypeError("effect.resolve_params: params must be of type dict")
        resolved = cls.get_default_params()
        for name, value in (params or {}).items():
            if name not in cls.PARAMS:
                raise ValueError(f"effect.resolve_params: unknown parameter '{name}'")
            resolved[name] = value
        return resolved


# EffectInstance class : an effect applied to a clip, with its own parameter values.
# This is what Clip.add_effect stores, so the playback pipeline only has to call apply(frame).
class EffectInstance:
    def __init__(self, effect, params=None):
        if effect is None:
            raise ValueError("effect_instance.__init__: effect cannot be None")
        if not isinstance(effect, Effect):
            raise TypeError("effect_instance.__init__: effect must be of type effects.base_effect.Effect")
        self.effect = effect
        self.params = type(effect).resolve_params(params)

    # Returns the effect
    def get_effect(self):
        return self.effect

    # Returns a copy of the parameters
    def get_params(self):
        return self.params.copy()

    # Returns the display name of the effect
    def get_name(self):
        return type(self.effect).get_name()

    # Applies the effect with its parameters on a frame
    def apply(self, frame):
        return self.effect.apply(frame, self.params)


# Class decorator : registers an Effect subclass so that it appears in the effects panel
def register_effect(effect_class):
    if not (isinstance(effect_class, type) and issubclass(effect_class, Effect)):
        raise TypeError("register_effect: effect_class must be a subclass of effects.base_effect.Effect")
    _EFFECT_REGISTRY[effect_class.get_name()] = effect_class
    return effect_class


# Returns the list of registered effect classes
def get_available_effects():
    return list(_EFFECT_REGISTRY.values())
