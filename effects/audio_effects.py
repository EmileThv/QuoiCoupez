import numpy as np
from audiomentations import Gain, HighPassFilter


def _check_samples(name, samples):
    if samples is None:
        raise ValueError(f"{name}.apply: samples cannot be None")
    if not isinstance(samples, np.ndarray):
        raise TypeError(f"{name}.apply: samples must be a numpy array")


# GainEffect : volume change. params: {"gain_db": number (default 0), "sample_rate": int}
class GainEffect:
    def apply(self, samples, params=None):
        _check_samples("gain_effect", samples)
        params = params or {}
        gain_db = params.get("gain_db", 0.0)
        sample_rate = params.get("sample_rate", 44100)
        if not isinstance(gain_db, (int, float)):
            raise TypeError("gain_effect.apply: gain_db must be a number")

        # min == max: fixed gain instead of a random one
        transform = Gain(min_gain_db=gain_db, max_gain_db=gain_db, p=1.0)
        return transform(samples=samples, sample_rate=sample_rate)


# HighPassEffect : removes low frequencies (rumble). params: {"cutoff_hz": number, "sample_rate": int}
class HighPassEffect:
    def apply(self, samples, params=None):
        _check_samples("high_pass_effect", samples)
        params = params or {}
        cutoff = params.get("cutoff_hz", 100)
        sample_rate = params.get("sample_rate", 44100)
        if not isinstance(cutoff, (int, float)) or cutoff <= 0:
            raise ValueError("high_pass_effect.apply: cutoff_hz must be a positive number")

        transform = HighPassFilter(min_cutoff_freq=cutoff, max_cutoff_freq=cutoff, p=1.0)
        return transform(samples=samples, sample_rate=sample_rate)


# EchoEffect : adds a delayed, attenuated copy of the signal.
# params: {"delay_s": number > 0, "decay": 0..1, "sample_rate": int}
class EchoEffect:
    def apply(self, samples, params=None):
        _check_samples("echo_effect", samples)
        params = params or {}
        delay_s = params.get("delay_s", 0.3)
        decay = params.get("decay", 0.5)
        sample_rate = params.get("sample_rate", 44100)
        if not isinstance(delay_s, (int, float)) or delay_s <= 0:
            raise ValueError("echo_effect.apply: delay_s must be a positive number")
        if not isinstance(decay, (int, float)) or not 0 <= decay <= 1:
            raise ValueError("echo_effect.apply: decay must be between 0 and 1")

        delay = int(delay_s * sample_rate)
        result = samples.copy()
        if 0 < delay < samples.shape[-1]:
            result[..., delay:] += decay * samples[..., :-delay]
        return np.clip(result, -1.0, 1.0)