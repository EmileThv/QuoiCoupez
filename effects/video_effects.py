import functools
import os
import re

import cv2
import numpy as np

from effects.base_effect import Effect

# BlurEffect: gaussian blur (0 = no blur).
class BlurEffect(Effect):
    NAME = "Flou"
    PARAMS = {
        "intensity": {"type": int, "default": 5, "min": 0, "max": 50, "label": "Intensité"},
    }

    def apply(self, frame, params=None):
        self.check_frame(frame)
        params = self.resolve_params(params)
        intensity = params["intensity"]
        if intensity == 0:
            return frame.copy()

        kernel_size = 2 * intensity + 1
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)


# ColorCorrectionEffect: brightness and contrast (contrast 1.0 and brightness 0 = unchanged).
class ColorCorrectionEffect(Effect):
    NAME = "Luminosité / contraste"
    PARAMS = {
        "brightness": {"type": float, "default": 0.0, "min": -255.0, "max": 255.0, "label": "Luminosité"},
        "contrast": {"type": float, "default": 1.0, "min": 0.0, "max": 3.0, "label": "Contraste"},
    }

    def apply(self, frame, params=None):
        self.check_frame(frame)
        params = self.resolve_params(params)
        return cv2.convertScaleAbs(frame, alpha=params["contrast"], beta=params["brightness"])


# TextOverlayEffect: writes a text on the frame.
class TextOverlayEffect(Effect):
    NAME = "Texte"
    # Positions and sizes are fractions of the frame size, for example x = 0.5 is the middle.
    PARAMS = {
        "text": {"type": str, "default": "Texte", "label": "Texte"},
        "x": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position X"},
        "y": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position Y"},
        "size": {"type": float, "default": 0.08, "min": 0.01, "max": 1.0, "label": "Taille"},
        "color": {"type": str, "default": "#FFFFFF", "label": "Couleur (#RRGGBB)", "kind": "color",
                  "pattern": r"#[0-9a-fA-F]{6}", "pattern_hint": "#RRGGBB"},
        "opacity": {"type": float, "default": 1.0, "min": 0.0, "max": 1.0, "label": "Opacité"},
    }

    def apply(self, frame, params=None):
        self.check_frame(frame)
        params = self.resolve_params(params)
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
class ImageOverlayEffect(Effect):
    NAME = "Image / logo"
    # Positions and width are fractions of the frame size, and the height follows the image's shape.
    PARAMS = {
        "image_path": {"type": str, "default": "", "label": "Fichier image", "kind": "file"},
        "x": {"type": float, "default": 0.8, "min": 0.0, "max": 1.0, "label": "Position X"},
        "y": {"type": float, "default": 0.05, "min": 0.0, "max": 1.0, "label": "Position Y"},
        "width": {"type": float, "default": 0.15, "min": 0.01, "max": 1.0, "label": "Largeur"},
        "opacity": {"type": float, "default": 1.0, "min": 0.0, "max": 1.0, "label": "Opacité"},
    }

    def apply(self, frame, params=None):
        self.check_frame(frame)
        params = self.resolve_params(params)
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


# Video effects offered in the effects panel, in display order.
VIDEO_EFFECTS = [BlurEffect, ColorCorrectionEffect, TextOverlayEffect, ImageOverlayEffect]


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
