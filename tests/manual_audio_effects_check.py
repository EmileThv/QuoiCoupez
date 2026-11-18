import sys
import os
import wave
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from effects.audio_effects import GainEffect, HighPassEffect, EchoEffect

SR = 44100


def save_wav(path, samples):
    data = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    t = np.arange(SR * 2) / SR
    samples = (0.3 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 50 * t)).astype(np.float32)
    # short beep so the echo is audible
    beep = np.zeros_like(samples)
    beep[:SR // 4] = samples[:SR // 4]

    p = {"sample_rate": SR}
    save_wav(os.path.join(root, "assets", "audio_original.wav"), samples)
    save_wav(os.path.join(root, "assets", "audio_gain.wav"), GainEffect().apply(samples, {**p, "gain_db": 6}))
    save_wav(os.path.join(root, "assets", "audio_highpass.wav"), HighPassEffect().apply(samples, {**p, "cutoff_hz": 200}))
    save_wav(os.path.join(root, "assets", "audio_echo.wav"), EchoEffect().apply(beep, {**p, "delay_s": 0.3, "decay": 0.6}))
    print("Done: listen to the audio_*.wav files in assets/")


if __name__ == "__main__":
    main() 