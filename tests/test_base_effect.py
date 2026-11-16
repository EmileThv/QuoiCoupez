import numpy as np
import pytest

from effects.base_effect import Effect
from effects.video_effects import (
    VIDEO_EFFECTS, BlurEffect, ColorCorrectionEffect, ImageOverlayEffect, TextOverlayEffect,
)


@pytest.fixture
def frame():
    image = np.zeros((90, 160, 3), dtype=np.uint8)
    image[:, 80:] = 200
    return image


class TestEffectBase:
    def test_effect_is_abstract(self):
        with pytest.raises(TypeError):
            Effect()

    def test_every_video_effect_inherits_effect(self):
        assert VIDEO_EFFECTS == [BlurEffect, ColorCorrectionEffect, TextOverlayEffect, ImageOverlayEffect]
        for effect_class in VIDEO_EFFECTS:
            assert issubclass(effect_class, Effect)
            assert effect_class.NAME != Effect.NAME
            for spec in effect_class.PARAMS.values():
                assert "type" in spec and "default" in spec

    def test_new_effect_has_default_params(self):
        assert BlurEffect().get_params() == {"intensity": 5}
        assert ColorCorrectionEffect().get_params() == {"brightness": 0.0, "contrast": 1.0}

    def test_constructor_params_are_checked(self):
        assert BlurEffect({"intensity": 3}).get_params() == {"intensity": 3}
        with pytest.raises(ValueError):
            BlurEffect({"unknown": 1})
        with pytest.raises(TypeError):
            BlurEffect("intensity")

    def test_set_param(self):
        effect = TextOverlayEffect()
        effect.set_param("text", "Bonjour")
        effect.set_param("x", 1)  # an int is accepted for a float
        assert effect.get_params()["text"] == "Bonjour"
        assert effect.get_params()["x"] == 1

    def test_set_param_refuses_bad_values_and_keeps_the_old_ones(self):
        effect = TextOverlayEffect()
        before = effect.get_params()
        with pytest.raises(ValueError):
            effect.set_param("color", "rouge")
        with pytest.raises(ValueError):
            effect.set_param("opacity", 2.0)
        with pytest.raises(TypeError):
            effect.set_param("size", "grand")
        with pytest.raises(TypeError):
            BlurEffect().set_param("intensity", True)
        with pytest.raises(ValueError):
            effect.set_param("nope", 1)
        assert effect.get_params() == before

    def test_get_params_returns_a_copy(self):
        effect = BlurEffect()
        effect.get_params()["intensity"] = 40
        assert effect.get_params()["intensity"] == 5


class TestApplyWithOwnParams:
    def test_apply_without_params_uses_the_effect_params(self, frame):
        effect = BlurEffect({"intensity": 0})
        assert np.array_equal(effect.apply(frame), frame)
        effect.set_param("intensity", 10)
        assert not np.array_equal(effect.apply(frame), frame)

    def test_given_params_replace_the_effect_params(self, frame):
        effect = BlurEffect({"intensity": 10})
        assert np.array_equal(effect.apply(frame, {"intensity": 0}), frame)

    def test_effects_do_not_modify_the_frame(self, frame):
        copy = frame.copy()
        for effect_class in VIDEO_EFFECTS:
            effect_class().apply(frame)
        assert np.array_equal(frame, copy)

    def test_color_correction(self, frame):
        result = ColorCorrectionEffect({"brightness": 10, "contrast": 1.0}).apply(frame)
        assert result[0, 0, 0] == 10
        assert result[0, 100, 0] == 210

    def test_bad_frames_are_refused(self):
        for effect_class in VIDEO_EFFECTS:
            with pytest.raises(ValueError):
                effect_class().apply(None)
            with pytest.raises(TypeError):
                effect_class().apply([[0, 0, 0]])
            with pytest.raises(ValueError):
                effect_class().apply(np.zeros((10, 10), dtype=np.uint8))

    def test_error_messages_start_with_the_effect_name(self, frame):
        with pytest.raises(ValueError, match=r"^blur_effect\.apply"):
            BlurEffect().apply(frame, {"intensity": -1})
        with pytest.raises(ValueError, match=r"^image_overlay_effect\.apply"):
            ImageOverlayEffect().apply(None)
