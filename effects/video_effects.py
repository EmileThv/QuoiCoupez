import cv2
import numpy as np

# BlurEffect : gaussian blur. params: {"intensity": int >= 0} (0 = no blur)
class BlurEffect:
    def apply(self, frame, params=None):
        if frame is None:
            raise ValueError("blur_effect.apply: frame cannot be None")
        if not isinstance(frame, np.ndarray):
            raise TypeError("blur_effect.apply: frame must be a numpy array")

        params = params or {}
        intensity = params.get("intensity", 5)

        if not isinstance(intensity, int):
            raise TypeError("blur_effect.apply: intensity must be of type int")
        if intensity < 0:
            raise ValueError("blur_effect.apply: intensity must be >= 0")

        if intensity == 0:
            return frame.copy()

        kernel_size = 2 * intensity + 1
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

# ColorCorrectionEffect : brightness and contrast.
# params: {"brightness": number (-255..255, default 0),
#          "contrast": number (>= 0, default 1.0, 1.0 = unchanged)}
class ColorCorrectionEffect:
    def apply(self, frame, params=None):
        if frame is None:
            raise ValueError("color_correction_effect.apply: frame cannot be None")
        if not isinstance(frame, np.ndarray):
            raise TypeError("color_correction_effect.apply: frame must be a numpy array")

        params = params or {}
        brightness = params.get("brightness", 0)
        contrast = params.get("contrast", 1.0)

        if not isinstance(brightness, (int, float)):
            raise TypeError("color_correction_effect.apply: brightness must be a number")
        if not isinstance(contrast, (int, float)):
            raise TypeError("color_correction_effect.apply: contrast must be a number")
        if contrast < 0:
            raise ValueError("color_correction_effect.apply: contrast must be >= 0")

        return cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)