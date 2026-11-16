import numpy as np
import pytest

from effects.audio_effects import (
    AUDIO_EFFECTS, AudioEffect, EchoEffect, GainEffect, NoiseReductionEffect,
)
from effects.base_effect import Effect

RATE = 48000


def sine(frequency, seconds=1.0, amplitude=0.2):
    t = np.arange(round(seconds * RATE)) / RATE
    wave = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    return np.vstack([wave, wave])


def rms(samples):
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


def test_audio_effects_are_effects():
    assert AUDIO_EFFECTS == [GainEffect, EchoEffect, NoiseReductionEffect]
    for effect_class in AUDIO_EFFECTS:
        assert issubclass(effect_class, AudioEffect)
        assert issubclass(effect_class, Effect)
        assert effect_class.KIND == "audio"


def test_effects_keep_shape_type_and_input():
    samples = sine(440)
    copy = samples.copy()
    for effect_class in AUDIO_EFFECTS:
        result = effect_class().apply(samples, sample_rate=RATE)
        assert result.shape == samples.shape
        assert result.dtype == np.float32
    assert np.array_equal(samples, copy)


def test_bad_samples_are_refused():
    for effect_class in AUDIO_EFFECTS:
        effect = effect_class()
        with pytest.raises(ValueError):
            effect.apply(None)
        with pytest.raises(TypeError):
            effect.apply([0.0, 0.1])
        with pytest.raises(ValueError):
            effect.apply(np.zeros(100, dtype=np.float32))
        with pytest.raises(ValueError):
            effect.apply(np.zeros((2, 100), dtype=np.float64))
        with pytest.raises(ValueError):
            effect.apply(sine(440), sample_rate=0)


def test_gain():
    samples = sine(440)
    louder = GainEffect({"gain_db": 6.0}).apply(samples, sample_rate=RATE)
    quieter = GainEffect({"gain_db": -20.0}).apply(samples, sample_rate=RATE)
    assert rms(louder) / rms(samples) == pytest.approx(10 ** (6 / 20), rel=0.01)
    assert rms(quieter) / rms(samples) == pytest.approx(0.1, rel=0.01)
    with pytest.raises(ValueError):
        GainEffect({"gain_db": 50.0})


def test_echo_adds_a_quieter_delayed_copy():
    # A single click: the echoes are copies of it, later and quieter.
    samples = np.zeros((2, RATE), dtype=np.float32)
    samples[:, 0] = 1.0
    result = EchoEffect({"delay": 0.1, "decay": 0.5, "repeats": 3}).apply(samples, sample_rate=RATE)
    delay = round(0.1 * RATE)
    assert result[0, 0] == pytest.approx(1.0)
    assert result[0, delay] == pytest.approx(0.5)
    assert result[0, 2 * delay] == pytest.approx(0.25)
    assert result[0, 3 * delay] == pytest.approx(0.125)
    assert result[0, 4 * delay] == 0.0


def test_echo_longer_than_the_clip_changes_nothing():
    samples = sine(440, seconds=0.1)
    result = EchoEffect({"delay": 1.0}).apply(samples, sample_rate=RATE)
    assert np.array_equal(result, samples)


def test_noise_reduction_keeps_the_voice_and_cuts_rumble_and_hiss():
    effect = NoiseReductionEffect({"low_cut": 150.0, "high_cut": 6000.0})
    voice = sine(1000)
    rumble = sine(30)
    hiss = sine(15000)
    assert rms(effect.apply(voice, sample_rate=RATE)) > 0.8 * rms(voice)
    assert rms(effect.apply(rumble, sample_rate=RATE)) < 0.2 * rms(rumble)
    assert rms(effect.apply(hiss, sample_rate=RATE)) < 0.2 * rms(hiss)


def test_noise_reduction_refuses_crossed_cuts():
    effect = NoiseReductionEffect({"low_cut": 1000.0, "high_cut": 1000.0})
    with pytest.raises(ValueError):
        effect.apply(sine(440), sample_rate=RATE)
