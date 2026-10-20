import cv2
import numpy as np

from effects.base_effect import Effect, register_effect


# Grayscale effect : converts the frame to grayscale (blended with the original according to "intensity")
@register_effect
class GrayscaleEffect(Effect):
    NAME = "Noir et blanc"
    PARAMS = {
        "intensity": {"type": float, "default": 1.0, "min": 0.0, "max": 1.0, "label": "Intensité"},
    }

    def apply(self, frame, params):
        gray = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        return cv2.addWeighted(gray, params["intensity"], frame, 1.0 - params["intensity"], 0)


# Brightness effect : adds a constant to every pixel (clipped to [0, 255])
@register_effect
class BrightnessEffect(Effect):
    NAME = "Luminosité"
    PARAMS = {
        "value": {"type": int, "default": 40, "min": -255, "max": 255, "label": "Valeur"},
    }

    def apply(self, frame, params):
        return np.clip(frame.astype(np.int16) + params["value"], 0, 255).astype(np.uint8)
