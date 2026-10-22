"""Generates the Dice Shaker sound effects (16-bit mono WAV) into build/generated/shaker/audio/.
All sounds are synthesised (no recordings), short and soft. Deterministic (fixed seeds).

usage: python gen_sounds.py
"""
import os
import wave

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(REPO, "build", "generated", "shaker", "audio")
RATE = 44100


def t(seconds):
    return np.arange(int(RATE * seconds)) / RATE


def env(length, attack=0.002, decay=0.05):
    x = np.arange(length) / RATE
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    return a * np.exp(-x / max(decay, 1e-4))


def bandnoise(rng, length, low, high):
    noise = rng.standard_normal(length)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(length, 1 / RATE)
    spectrum[(freqs < low) | (freqs > high)] = 0
    out = np.fft.irfft(spectrum, length)
    return out / (np.max(np.abs(out)) + 1e-9)


def tone(freq, seconds, decay, partials=((1, 1.0),)):
    x = t(seconds)
    out = np.zeros_like(x)
    for mult, amp in partials:
        out += amp * np.sin(2 * np.pi * freq * mult * x)
    return out * env(len(x), 0.003, decay)


def click(rng, glass=True, pitch=1.0):
    length = int(RATE * 0.07)
    burst = bandnoise(rng, length, 1500 * pitch, 7000 * pitch) * env(length, 0.0005, 0.006)
    if glass:
        x = np.arange(length) / RATE
        ring = (np.sin(2 * np.pi * 3100 * pitch * x) * 0.5 + np.sin(2 * np.pi * 4700 * pitch * x) * 0.3) * env(length, 0.001, 0.02)
        burst = burst * 0.7 + ring * 0.5
    return burst


def place(out, sound, at):
    start = int(at * RATE)
    end = min(len(out), start + len(sound))
    if start < len(out):
        out[start:end] += sound[:end - start]


def rattle():
    rng = np.random.default_rng(1)
    out = np.zeros(int(RATE * 0.75))
    times = np.sort(rng.uniform(0.0, 0.62, 26))
    for at in times:
        place(out, click(rng, True, rng.uniform(0.8, 1.25)) * rng.uniform(0.35, 0.9), at)
    return out


def land():
    rng = np.random.default_rng(2)
    out = np.zeros(int(RATE * 0.3))
    for at in (0.0, 0.05, 0.09, 0.16):
        place(out, click(rng, True, rng.uniform(0.7, 0.9)) * rng.uniform(0.4, 0.8), at)
    return out


def coin():
    rng = np.random.default_rng(3)
    out = np.zeros(int(RATE * 0.45))
    clink = tone(2780, 0.4, 0.08, ((1, 1.0), (1.48, 0.6), (2.31, 0.35)))
    place(out, clink, 0.0)
    place(out, tone(3350, 0.3, 0.05, ((1, 0.6), (1.6, 0.3))), 0.07)
    slide = bandnoise(rng, int(RATE * 0.15), 2500, 6000) * env(int(RATE * 0.15), 0.02, 0.05) * 0.25
    place(out, slide, 0.12)
    return out


def crank():
    rng = np.random.default_rng(4)
    out = np.zeros(int(RATE * 0.09))
    place(out, bandnoise(rng, int(RATE * 0.05), 600, 3500) * env(int(RATE * 0.05), 0.0005, 0.008), 0.0)
    place(out, tone(950, 0.06, 0.012) * 0.4, 0.0)
    return out


def pop():
    x = t(0.3)
    freq = 520 * np.exp(-x * 9) + 160
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    out = np.sin(phase) * env(len(x), 0.002, 0.07)
    bounce = tone(300, 0.1, 0.02) * 0.4
    place(out, bounce, 0.17)
    return out


def chime(notes, spacing, decay, length):
    out = np.zeros(int(RATE * length))
    for i, freq in enumerate(notes):
        place(out, tone(freq, length - i * spacing, decay, ((1, 1.0), (2, 0.25), (3, 0.08))) * 0.6, i * spacing)
    return out


def level():
    return chime([1046.5, 1318.5, 1568.0], 0.07, 0.25, 0.75)


def learn():
    out = chime([784.0, 987.8, 1174.7, 1568.0], 0.06, 0.3, 0.9)
    rng = np.random.default_rng(5)
    shimmer = bandnoise(rng, len(out), 4000, 9000) * env(len(out), 0.05, 0.25) * 0.08
    return out + shimmer


def lucky():
    out = np.zeros(int(RATE * 0.9))
    place(out, rattle()[: int(RATE * 0.5)] * 0.8, 0.0)
    place(out, chime([1318.5, 1760.0, 2093.0], 0.05, 0.22, 0.5), 0.38)
    return out


def card():
    rng = np.random.default_rng(6)
    length = int(RATE * 0.28)
    x = np.arange(length) / RATE
    swoosh = bandnoise(rng, length, 1200, 6500) * np.sin(np.pi * np.clip(x / 0.22, 0, 1)) ** 2 * 0.45
    place_out = np.zeros(length)
    place_out += swoosh
    place(place_out, click(rng, False, 0.6) * 0.5, 0.2)
    return place_out


def buy():
    out = np.zeros(int(RATE * 0.5))
    for i, freq in enumerate((2637.0, 3136.0, 3951.0)):
        place(out, tone(freq, 0.35, 0.07, ((1, 1.0), (1.5, 0.4))) * 0.55, i * 0.06)
    return out


def denied():
    return tone(185.0, 0.25, 0.06, ((1, 1.0), (2, 0.2))) * 0.8


SOUNDS = {"rattle": rattle, "land": land, "coin": coin, "crank": crank, "pop": pop, "level": level,
          "learn": learn, "lucky": lucky, "card": card, "buy": buy, "denied": denied}


def write(name, samples, peak=0.55):
    samples = np.asarray(samples, dtype=np.float64)
    fade = min(len(samples), int(RATE * 0.01))
    samples[-fade:] *= np.linspace(1, 0, fade)
    samples = samples / (np.max(np.abs(samples)) + 1e-9) * peak
    data = (samples * 32767).astype("<i2").tobytes()
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(data)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in SOUNDS.items():
        write(name, make(), 0.45 if name in ("rattle", "land", "crank") else 0.55)
    print("wrote %d sounds to %s" % (len(SOUNDS), OUT))


if __name__ == "__main__":
    main()
