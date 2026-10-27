import functools
import os
import re

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


# TextOverlayEffect: writes a text on the frame.
class TextOverlayEffect:
    NAME = "Texte"
    # Positions and sizes are fractions of the frame size, for example x = 0.5 is the middle.
    PARAMS = {
        "text": {"type": str, "default": "Texte", "label": "Texte"},
        "x": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position X"},
        "y": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position Y"},
        "size": {"type": float, "default": 0.08, "min": 0.01, "max": 1.0, "label": "Taille"},
        "color": {"type": str, "default": "#FFFFFF", "label": "Couleur (#RRGGBB)"},
        "opacity": {"type": float, "default": 1.0, "min": 0.0, "max": 1.0, "label": "Opacité"},
    }

    def apply(self, frame, params=None):
        _check_frame("text_overlay_effect", frame)
        params = _resolve_params("text_overlay_effect", self.PARAMS, params)
        color = _hex_to_bgr("text_overlay_effect", params["color"])
        if params["text"] == "":
            return frame.copy()

        frame_height, frame_width = frame.shape[:2]
        text_height = max(1, round(params["size"] * frame_height))
        mask = _text_mask(params["text"], text_height)

        # A rectangle filled with the text color: the mask decides where it is visible.
        mask_height, mask_width = mask.shape
        colored_rectangle = np.full((mask_height, mask_width, 3), color, dtype=np.uint8)
        alpha = mask * params["opacity"]

        x = round(params["x"] * frame_width)
        y = round(params["y"] * frame_height)
        return _blend(frame, colored_rectangle, alpha, x, y)


# ImageOverlayEffect: draws an image or a logo on the frame and keeps its transparency.
class ImageOverlayEffect:
    NAME = "Image / logo"
    # Positions and width are fractions of the frame size, and the height follows the image's shape.
    PARAMS = {
        "image_path": {"type": str, "default": "", "label": "Fichier image"},
        "x": {"type": float, "default": 0.8, "min": 0.0, "max": 1.0, "label": "Position X"},
        "y": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position Y"},
        "width": {"type": float, "default": 0.15, "min": 0.01, "max": 1.0, "label": "Largeur"},
        "opacity": {"type": float, "default": 1.0, "min": 0.0, "max": 1.0, "label": "Opacité"},
    }

    def apply(self, frame, params=None):
        _check_frame("image_overlay_effect", frame)
        params = _resolve_params("image_overlay_effect", self.PARAMS, params)
        if params["image_path"] == "":
            return frame.copy()

        frame_height, frame_width = frame.shape[:2]
        image = _load_image(params["image_path"])
        image_height, image_width = image.shape[:2]

        width = max(1, round(params["width"] * frame_width))
        height = max(1, round(image_height * width / image_width))
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

        colors = image[:, :, :3]
        pixel_opacity = image[:, :, 3].astype(np.float32) / 255
        alpha = pixel_opacity * params["opacity"]

        x = round(params["x"] * frame_width)
        y = round(params["y"] * frame_height)
        return _blend(frame, colors, alpha, x, y)


def _check_frame(effect_name, frame):
    if frame is None:
        raise ValueError(f"{effect_name}.apply: frame cannot be None")
    if not isinstance(frame, np.ndarray):
        raise TypeError(f"{effect_name}.apply: frame must be a numpy array")
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(f"{effect_name}.apply: frame must be a color image of shape (h, w, 3)")
    if frame.dtype != np.uint8:
        raise ValueError(f"{effect_name}.apply: frame must contain uint8 values")


# Checks the given values and fills in the missing ones with their default value.
# To be replaced by Effect.resolve_params when base_effect.py is on main.
def _resolve_params(effect_name, specs, params):
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise TypeError(f"{effect_name}.apply: params must be of type dict")

    resolved = {}
    for name in specs:
        resolved[name] = specs[name]["default"]

    for name, value in params.items():
        if name not in specs:
            raise ValueError(f"{effect_name}.apply: unknown parameter '{name}'")
        _check_param(effect_name, name, value, specs[name])
        resolved[name] = value
    return resolved


def _check_param(effect_name, name, value, spec):
    expected_type = spec["type"]
    # An int is also accepted where a float is expected, for example 1 instead of 1.0.
    if expected_type is float:
        is_right_type = isinstance(value, (int, float))
    else:
        is_right_type = isinstance(value, expected_type)
    if not is_right_type:
        raise TypeError(f"{effect_name}.apply: {name} must be of type {expected_type.__name__}")

    if "min" in spec and value < spec["min"]:
        raise ValueError(f"{effect_name}.apply: {name} must be at least {spec['min']}")
    if "max" in spec and value > spec["max"]:
        raise ValueError(f"{effect_name}.apply: {name} must be at most {spec['max']}")


# Converts a color like "#FF8800" to the (blue, green, red) order used by OpenCV.
def _hex_to_bgr(effect_name, color):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"{effect_name}.apply: color must look like #RRGGBB")
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return blue, green, red


# Draws the text in white on black, so each pixel says how much of the text color to show.
# The result is cached, because the same text is drawn again on every frame.
@functools.lru_cache(maxsize=32)
def _text_mask(text, height_px):
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, height_px // 12)

    # Measures the text at scale 1 to find the scale that gives the wanted height.
    size_at_scale_1, _ = cv2.getTextSize(text, font, 1.0, thickness)
    scale = height_px / size_at_scale_1[1]

    text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
    text_width = text_size[0]
    text_height = text_size[1]

    mask_height = text_height + baseline + thickness
    mask_width = text_width + thickness
    mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
    cv2.putText(mask, text, (0, text_height), font, scale, 255, thickness, cv2.LINE_AA)
    return mask.astype(np.float32) / 255


# Loads an image only once and always gives it 4 channels: blue, green, red and opacity.
@functools.lru_cache(maxsize=16)
def _load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"image_overlay_effect.apply: no file at {path}")

    # cv2.imread fails on Windows when the path has accents, so numpy reads the file instead.
    file_bytes = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"image_overlay_effect.apply: {path} is not a valid image")

    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    return image


# Pastes the patch on a copy of the frame at (x, y), and cuts what goes outside the frame.
def _blend(frame, patch, alpha, x, y):
    result = frame.copy()
    frame_height, frame_width = frame.shape[:2]
    patch_height, patch_width = patch.shape[:2]

    # Visible part of the patch, in frame coordinates.
    left = max(x, 0)
    top = max(y, 0)
    right = min(x + patch_width, frame_width)
    bottom = min(y + patch_height, frame_height)
    if right <= left or bottom <= top:
        return result

    # The same part, in patch coordinates.
    patch_left = left - x
    patch_top = top - y
    patch_right = right - x
    patch_bottom = bottom - y

    visible_patch = patch[patch_top:patch_bottom, patch_left:patch_right].astype(np.float32)
    visible_alpha = alpha[patch_top:patch_bottom, patch_left:patch_right]
    # Gives each pixel's alpha to its 3 color channels.
    visible_alpha = visible_alpha[:, :, np.newaxis]
    background = result[top:bottom, left:right].astype(np.float32)

    # alpha = 1 shows only the patch, alpha = 0 keeps only the frame.
    mixed = visible_patch * visible_alpha + background * (1 - visible_alpha)
    result[top:bottom, left:right] = np.round(mixed).astype(np.uint8)
    return result
