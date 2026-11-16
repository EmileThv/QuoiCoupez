import cv2
import numpy as np
import pytest

from effects.audio_effects import AUDIO_EFFECTS
from effects.video_effects import (
    VIDEO_EFFECTS, BlurEffect, ColorCorrectionEffect, ImageOverlayEffect, TextOverlayEffect,
)

HEIGHT, WIDTH = 120, 200


@pytest.fixture
def gray():
    return np.full((HEIGHT, WIDTH, 3), 100, dtype=np.uint8)


@pytest.fixture
def edge():
    # Left half black, right half white: a sharp vertical edge in the middle.
    image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    image[:, WIDTH // 2:] = 255
    return image


# Saves an image with numpy (works with accents in the path on Windows, like the effect).
def save_image(path, image):
    success, encoded = cv2.imencode(path.suffix, image)
    assert success
    encoded.tofile(str(path))
    return str(path)


@pytest.fixture
def logo(tmp_path):
    # 20 x 10 RGBA image: left half opaque red, right half fully transparent.
    image = np.zeros((10, 20, 4), dtype=np.uint8)
    image[:, :10] = (0, 0, 255, 255)
    image[:, 10:] = (0, 255, 0, 0)
    return save_image(tmp_path / "logo.png", image)


# --- Common rules ----------------------------------------------------------------------------

@pytest.mark.parametrize("effect_class", VIDEO_EFFECTS)
def test_result_is_a_new_frame_of_the_same_shape(effect_class, edge):
    copy = edge.copy()
    result = effect_class().apply(edge)
    assert result.shape == edge.shape
    assert result.dtype == np.uint8
    assert result is not edge
    assert np.array_equal(edge, copy)


@pytest.mark.parametrize("effect_class", VIDEO_EFFECTS + AUDIO_EFFECTS)
def test_every_parameter_has_a_valid_default_and_a_label(effect_class):
    effect = effect_class()
    for name, spec in effect_class.PARAMS.items():
        assert "label" in spec
        assert effect.get_params()[name] == spec["default"]
        if "min" in spec:
            assert spec["min"] <= spec["default"] <= spec["max"]


# --- Blur ------------------------------------------------------------------------------------

def test_blur_zero_changes_nothing(edge):
    assert np.array_equal(BlurEffect({"intensity": 0}).apply(edge), edge)


def test_blur_softens_the_edge_more_when_stronger(edge):
    weak = BlurEffect({"intensity": 3}).apply(edge)
    strong = BlurEffect({"intensity": 20}).apply(edge)
    column = WIDTH // 2 - 2  # just left of the edge: was black
    assert 0 < weak[60, column, 0] < strong[60, column, 0]
    # Far from the edge, the image stays the same.
    assert weak[60, 5, 0] == 0 and weak[60, WIDTH - 5, 0] == 255


def test_blur_refuses_bad_intensity(edge):
    with pytest.raises(TypeError):
        BlurEffect().apply(edge, {"intensity": 2.5})
    with pytest.raises(ValueError):
        BlurEffect().apply(edge, {"intensity": -1})
    with pytest.raises(ValueError):
        BlurEffect().apply(edge, {"intensity": 51})


# --- Color correction ------------------------------------------------------------------------

def test_default_color_correction_changes_nothing(gray):
    assert np.array_equal(ColorCorrectionEffect().apply(gray), gray)


def test_contrast_and_brightness(gray):
    assert ColorCorrectionEffect({"contrast": 2.0}).apply(gray)[0, 0, 0] == 200
    assert ColorCorrectionEffect({"brightness": -30}).apply(gray)[0, 0, 0] == 70
    assert ColorCorrectionEffect({"contrast": 0.0, "brightness": 40}).apply(gray)[0, 0, 0] == 40


# A strong darkening gives black (cv2.convertScaleAbs used to turn -155 into 155).
def test_color_correction_stays_between_0_and_255(gray):
    assert ColorCorrectionEffect({"contrast": 3.0, "brightness": 255}).apply(gray)[0, 0, 0] == 255
    assert ColorCorrectionEffect({"brightness": -255}).apply(gray)[0, 0, 0] == 0


def test_color_correction_refuses_out_of_range_values(gray):
    with pytest.raises(ValueError):
        ColorCorrectionEffect().apply(gray, {"contrast": -0.1})
    with pytest.raises(ValueError):
        ColorCorrectionEffect().apply(gray, {"brightness": 300})
    with pytest.raises(TypeError):
        ColorCorrectionEffect().apply(gray, {"brightness": "40"})


# --- Text overlay ----------------------------------------------------------------------------

def test_empty_text_changes_nothing(gray):
    assert np.array_equal(TextOverlayEffect({"text": ""}).apply(gray), gray)


def test_text_is_drawn_in_its_color_near_its_position(gray):
    result = TextOverlayEffect({"text": "HELLO", "x": 0.1, "y": 0.1, "size": 0.3, "color": "#FF0000"}).apply(gray)
    changed = np.any(result != gray, axis=2)
    rows, columns = np.nonzero(changed)
    assert len(rows) > 0
    assert rows.min() >= round(0.1 * HEIGHT) and columns.min() >= round(0.1 * WIDTH)
    # Fully covered pixels have exactly the text color (BGR: red = index 2).
    assert any(tuple(pixel) == (0, 0, 255) for pixel in result[changed])


def test_text_opacity(gray):
    params = {"text": "X", "x": 0.0, "y": 0.0, "size": 0.9, "color": "#FFFFFF"}
    full = TextOverlayEffect(params).apply(gray)
    half = TextOverlayEffect(dict(params, opacity=0.5)).apply(gray)
    hidden = TextOverlayEffect(dict(params, opacity=0.0)).apply(gray)
    assert full.max() == 255
    assert 100 < half.max() < 255
    assert np.array_equal(hidden, gray)


def test_text_partly_outside_the_frame_is_cut(gray):
    # Starts 20 px before the right edge: most of the text is outside.
    result = TextOverlayEffect({"text": "HHHHHH", "x": 0.9, "y": 0.3, "size": 0.5}).apply(gray)
    assert result.shape == gray.shape
    assert np.any(result != gray)


def test_text_refuses_bad_values(gray):
    with pytest.raises(ValueError):
        TextOverlayEffect().apply(gray, {"color": "#12345"})
    with pytest.raises(ValueError):
        TextOverlayEffect().apply(gray, {"size": 0})
    with pytest.raises(TypeError):
        TextOverlayEffect().apply(gray, {"text": 12})


# --- Image overlay ---------------------------------------------------------------------------

def test_no_image_changes_nothing(gray):
    assert np.array_equal(ImageOverlayEffect().apply(gray), gray)


def test_image_keeps_its_transparency(gray, logo):
    # width 0.1 of a 200 px frame = 20 px: the logo keeps its size (20 x 10) at (20, 12).
    result = ImageOverlayEffect({"image_path": logo, "x": 0.1, "y": 0.1, "width": 0.1}).apply(gray)
    assert tuple(result[15, 25]) == (0, 0, 255)  # opaque red half
    assert tuple(result[15, 35]) == (100, 100, 100)  # transparent half: the frame is kept
    assert tuple(result[50, 100]) == (100, 100, 100)  # outside the logo


def test_image_is_resized_to_the_wanted_width(gray, logo):
    # width 0.5 = 100 px: the logo is 5 times bigger (100 x 50), its red half is 50 px wide.
    result = ImageOverlayEffect({"image_path": logo, "x": 0.0, "y": 0.0, "width": 0.5}).apply(gray)
    red = np.all(result == (0, 0, 255), axis=2)
    rows, columns = np.nonzero(red)
    assert columns.max() - columns.min() + 1 == pytest.approx(50, abs=2)
    assert rows.max() - rows.min() + 1 == pytest.approx(50, abs=2)


def test_image_opacity(gray, logo):
    result = ImageOverlayEffect({"image_path": logo, "x": 0.1, "y": 0.1, "width": 0.1, "opacity": 0.5}).apply(gray)
    blue, green, red = result[15, 25]
    assert (blue, green) == (50, 50) and red == pytest.approx(178, abs=1)


def test_images_without_transparency_are_opaque(tmp_path, gray):
    gray_image = save_image(tmp_path / "gris.png", np.full((10, 10), 200, dtype=np.uint8))
    jpeg = save_image(tmp_path / "bleu.jpg", np.full((10, 10, 3), (255, 0, 0), dtype=np.uint8))
    params = {"x": 0.0, "y": 0.0, "width": 0.05}
    assert tuple(ImageOverlayEffect(dict(params, image_path=gray_image)).apply(gray)[2, 2]) == (200, 200, 200)
    blue, green, red = ImageOverlayEffect(dict(params, image_path=jpeg)).apply(gray)[2, 2]
    assert blue > 240 and green < 15 and red < 15


def test_image_path_with_accents(tmp_path, gray):
    folder = tmp_path / "dossier é"
    folder.mkdir()
    path = save_image(folder / "logo_ç.png", np.full((10, 10, 3), 255, dtype=np.uint8))
    result = ImageOverlayEffect({"image_path": path, "x": 0.0, "y": 0.0, "width": 0.05}).apply(gray)
    assert tuple(result[2, 2]) == (255, 255, 255)


def test_image_outside_the_frame_changes_nothing(gray, logo):
    result = ImageOverlayEffect({"image_path": logo, "x": 1.0, "y": 1.0}).apply(gray)
    assert np.array_equal(result, gray)


def test_bad_image_files(tmp_path, gray):
    with pytest.raises(FileNotFoundError):
        ImageOverlayEffect().apply(gray, {"image_path": str(tmp_path / "absent.png")})
    not_an_image = tmp_path / "texte.png"
    not_an_image.write_text("pas une image")
    with pytest.raises(ValueError):
        ImageOverlayEffect().apply(gray, {"image_path": str(not_an_image)})


# --- Chaining ------------------------------------------------------------------------------

def test_effects_can_be_chained(gray, logo):
    effects = [
        ColorCorrectionEffect({"brightness": 50}),
        BlurEffect({"intensity": 1}),
        TextOverlayEffect({"text": "A"}),
        ImageOverlayEffect({"image_path": logo}),
    ]
    frame = gray
    for effect in effects:
        frame = effect.apply(frame)
    assert frame.shape == gray.shape
    assert frame[HEIGHT - 1, 0, 0] == 150  # corner: only the brightness changed it
