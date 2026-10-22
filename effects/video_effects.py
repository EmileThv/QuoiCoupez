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


# TextOverlayEffect: writes a text on the frame. x, y (top-left) and size are fractions of the frame size
class TextOverlayEffect:
    NAME = "Texte"
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
        mask = _text_mask(params["text"], max(1, round(params["size"] * frame_height)))
        patch = np.full(mask.shape + (3,), color, dtype=np.uint8)
        x, y = round(params["x"] * frame_width), round(params["y"] * frame_height)
        return _blend(frame, patch, mask * params["opacity"], x, y)


# ImageOverlayEffect: draws an image/logo on the frame, keeping its transparency (PNG).
# x, y (top-left) and width are fractions of the frame size; the height keeps the image's ratio
class ImageOverlayEffect:
    NAME = "Image / logo"
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
        width = max(1, round(params["width"] * frame_width))
        height = max(1, round(image.shape[0] * width / image.shape[1]))
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

        alpha = image[:, :, 3].astype(np.float32) / 255 * params["opacity"]
        x, y = round(params["x"] * frame_width), round(params["y"] * frame_height)
        return _blend(frame, image[:, :, :3], alpha, x, y)


def _check_frame(effect_name, frame):
    if frame is None:
        raise ValueError(f"{effect_name}.apply: frame cannot be None")
    if not isinstance(frame, np.ndarray):
        raise TypeError(f"{effect_name}.apply: frame must be a numpy array")
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
        raise ValueError(f"{effect_name}.apply: frame must be a BGR uint8 array of shape (h, w, 3)")


# Defaults + checks from PARAMS; to be replaced by Effect.resolve_params once base_effect.py is merged
def _resolve_params(effect_name, specs, params):
    if params is not None and not isinstance(params, dict):
        raise TypeError(f"{effect_name}.apply: params must be of type dict")
    resolved = {name: spec["default"] for name, spec in specs.items()}
    for name, value in (params or {}).items():
        if name not in specs:
            raise ValueError(f"{effect_name}.apply: unknown parameter '{name}'")
        spec = specs[name]
        expected = (int, float) if spec["type"] is float else spec["type"]
        if not isinstance(value, expected):
            raise TypeError(f"{effect_name}.apply: {name} must be of type {spec['type'].__name__}")
        if ("min" in spec and value < spec["min"]) or ("max" in spec and value > spec["max"]):
            raise ValueError(f"{effect_name}.apply: {name} must be between {spec['min']} and {spec['max']}")
        resolved[name] = value
    return resolved


def _hex_to_bgr(effect_name, color):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"{effect_name}.apply: color must look like #RRGGBB")
    red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return blue, green, red


# Cached: during playback the same text is drawn on every frame
@functools.lru_cache(maxsize=32)
def _text_mask(text, height_px):
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, height_px // 12)
    (_, reference_height), _ = cv2.getTextSize(text, font, 1.0, thickness)
    scale = height_px / reference_height
    (width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    mask = np.zeros((text_height + baseline + thickness, width + thickness), dtype=np.uint8)
    cv2.putText(mask, text, (0, text_height), font, scale, 255, thickness, cv2.LINE_AA)
    return mask.astype(np.float32) / 255


@functools.lru_cache(maxsize=16)
def _load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"image_overlay_effect.apply: no file at {path}")
    # np.fromfile + imdecode: cv2.imread fails on accented paths on Windows
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"image_overlay_effect.apply: {path} is not a valid image")
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    return image


# Alpha-blends patch onto a copy of frame at (x, y); the parts outside the frame are cut
def _blend(frame, patch, alpha, x, y):
    result = frame.copy()
    frame_height, frame_width = frame.shape[:2]
    left, top = max(x, 0), max(y, 0)
    right = min(x + patch.shape[1], frame_width)
    bottom = min(y + patch.shape[0], frame_height)
    if right <= left or bottom <= top:
        return result

    patch = patch[top - y:bottom - y, left - x:right - x].astype(np.float32)
    alpha = alpha[top - y:bottom - y, left - x:right - x, None]
    region = result[top:bottom, left:right].astype(np.float32)
    result[top:bottom, left:right] = (patch * alpha + region * (1 - alpha) + 0.5).astype(np.uint8)
    return result