import numpy as np
from audiomentations import Gain, HighPassFilter, LowPassFilter

from effects.base_effect import Effect

DEFAULT_SAMPLE_RATE = 48000


# AudioEffect: base class of the audio effects.
# apply(samples, params, sample_rate) takes float32 samples of shape (channels, length), with
# values between -1 and 1, and returns new samples of the same shape (the input is not changed).
class AudioEffect(Effect):
    KIND = "audio"

    def check_samples(self, samples, sample_rate):
        effect_name = self._error_name()
        if samples is None:
            raise ValueError(f"{effect_name}.apply: samples cannot be None")
        if not isinstance(samples, np.ndarray):
            raise TypeError(f"{effect_name}.apply: samples must be a numpy array")
        if samples.ndim != 2:
            raise ValueError(f"{effect_name}.apply: samples must have the shape (channels, length)")
        if samples.dtype != np.float32:
            raise ValueError(f"{effect_name}.apply: samples must contain float32 values")
        if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError(f"{effect_name}.apply: sample_rate must be a positive int")


# GainEffect: makes the sound louder or quieter (audiomentations.Gain).
class GainEffect(AudioEffect):
    NAME = "Volume (gain)"
    PARAMS = {
        "gain_db": {"type": float, "default": 6.0, "min": -40.0, "max": 20.0, "label": "Gain (dB)"},
    }

    def apply(self, samples, params=None, sample_rate=DEFAULT_SAMPLE_RATE):
        self.check_samples(samples, sample_rate)
        params = self.resolve_params(params)
        # min = max and p = 1: audiomentations is made deterministic, the effect is always applied.
        gain = Gain(min_gain_db=params["gain_db"], max_gain_db=params["gain_db"], p=1.0)
        return gain(samples.copy(), sample_rate=sample_rate)


# EchoEffect: adds copies of the sound, each one later and quieter than the previous one.
# Audiomentations has no echo transform, so it is computed directly with numpy.
class EchoEffect(AudioEffect):
    NAME = "Écho"
    PARAMS = {
        "delay": {"type": float, "default": 0.3, "min": 0.01, "max": 2.0, "label": "Retard (s)"},
        "decay": {"type": float, "default": 0.5, "min": 0.0, "max": 0.95, "label": "Atténuation"},
        "repeats": {"type": int, "default": 3, "min": 1, "max": 10, "label": "Répétitions"},
    }

    def apply(self, samples, params=None, sample_rate=DEFAULT_SAMPLE_RATE):
        self.check_samples(samples, sample_rate)
        params = self.resolve_params(params)
        result = samples.copy()
        delay = round(params["delay"] * sample_rate)
        length = samples.shape[1]

        # The echoes are cut at the end of the clip, so its duration does not change.
        for repeat in range(1, params["repeats"] + 1):
            start = delay * repeat
            if start >= length:
                break
            result[:, start:] += samples[:, :length - start] * (params["decay"] ** repeat)
        return result


# NoiseReductionEffect: removes the low rumble and the high hiss that are outside the voice range,
# with the high-pass and low-pass filters of audiomentations. It is a filter, not a real denoiser:
# a noise in the same frequencies as the voice is kept.
class NoiseReductionEffect(AudioEffect):
    NAME = "Réduction de bruit"
    PARAMS = {
        "low_cut": {"type": float, "default": 100.0, "min": 20.0, "max": 1000.0, "label": "Coupe les graves sous (Hz)"},
        "high_cut": {"type": float, "default": 8000.0, "min": 1000.0, "max": 20000.0, "label": "Coupe les aigus au-dessus de (Hz)"},
    }

    def apply(self, samples, params=None, sample_rate=DEFAULT_SAMPLE_RATE):
        self.check_samples(samples, sample_rate)
        params = self.resolve_params(params)
        if params["low_cut"] >= params["high_cut"]:
            raise ValueError("noise_reduction_effect.apply: low_cut must be lower than high_cut")

        high_pass = HighPassFilter(min_cutoff_freq=params["low_cut"], max_cutoff_freq=params["low_cut"], p=1.0)
        result = high_pass(samples.copy(), sample_rate=sample_rate)
        # A low-pass cut above half the sample rate means nothing: it is skipped.
        if params["high_cut"] < sample_rate / 2:
            low_pass = LowPassFilter(min_cutoff_freq=params["high_cut"], max_cutoff_freq=params["high_cut"], p=1.0)
            result = low_pass(result, sample_rate=sample_rate)
        return result.astype(np.float32)


# Audio effects offered in the effects panel, in display order.
AUDIO_EFFECTS = [GainEffect, EchoEffect, NoiseReductionEffect]
