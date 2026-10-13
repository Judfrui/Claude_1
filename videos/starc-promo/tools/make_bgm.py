"""Bande-son originale du film STARC (90 s, 120 BPM, une mesure = 2 s).

Synthèse entièrement procédurale (numpy uniquement), déterministe.
Usage : python3 tools/make_bgm.py assets/audio/bgm_raw.wav
Le mastering (loudnorm) est fait ensuite avec ffmpeg.
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 90.0
N = int(SR * DUR)
BEAT = 0.5
BAR = 2.0
rng = np.random.default_rng(20261013)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fir_lowpass(cut, taps=511):
    n = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * cut / SR * n) * np.blackman(taps)
    return h / h.sum()


def fir_highpass(cut, taps=511):
    h = -fir_lowpass(cut, taps)
    h[(taps - 1) // 2] += 1.0
    return h


def fir_bandpass(lo, hi, taps=511):
    return fir_lowpass(hi, taps) - fir_lowpass(lo, taps)


def fftconv(x, h):
    L = len(x) + len(h) - 1
    n = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:L]
    d = (len(h) - 1) // 2
    return y[d:d + len(x)]


def saw_blep(freq, n, phase0=0.0):
    dt = freq / SR
    t = (phase0 + dt * np.arange(n)) % 1.0
    y = 2 * t - 1
    a = t < dt
    x = t[a] / dt
    y[a] -= x + x - x * x - 1
    b = t > 1 - dt
    x = (t[b] - 1) / dt
    y[b] -= x * x + x + x + 1
    return y


def env_adsr(n, a, d, s, r, hold):
    e = np.zeros(n)
    ia, idd, ih, ir = int(a * SR), int(d * SR), int(hold * SR), int(r * SR)
    k = 0
    seg = min(ia, n)
    e[:seg] = np.linspace(0, 1, seg, endpoint=False)
    k = seg
    seg = min(idd, n - k)
    e[k:k + seg] = np.linspace(1, s, seg, endpoint=False)
    k += seg
    seg = max(0, min(ih - k, n - k))
    e[k:k + seg] = s
    k += seg
    seg = min(ir, n - k)
    if seg > 0:
        e[k:k + seg] = np.linspace(s, 0, seg)
    return e


def place(buf, sig, t0, gain=1.0):
    i = int(round(t0 * SR))
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


# Harmonie : Am9 | Fmaj7 | C(add9) | Gsus4
CHORDS = [
    {"root": 45, "pad": [57, 60, 64, 67, 71]},
    {"root": 41, "pad": [53, 57, 60, 64, 67]},
    {"root": 48, "pad": [55, 60, 62, 64, 67]},
    {"root": 43, "pad": [55, 60, 62, 67, 71]},
]
FINAL = {"root": 48, "pad": [55, 60, 64, 67, 72]}
NBARS = int(DUR / BAR)


def chord_at(bar):
    if bar >= 43:
        return FINAL
    return CHORDS[bar % 4]


def section(t):
    if t < 8:
        return "intro"
    if t < 24:
        return "verse"
    if t < 54:
        return "drive"
    if t < 62:
        return "break"
    if t < 82:
        return "chorus"
    return "outro"


# ---------- Pad ----------
pad = np.zeros((N, 2))
for bar in range(NBARS):
    ch = chord_at(bar)
    t0 = bar * BAR
    length = BAR + 0.6 if bar < NBARS - 1 else DUR - t0
    n = int(length * SR)
    env = env_adsr(n, 0.35, 0.4, 0.85, 0.6, length - 0.6)
    for j, m in enumerate(ch["pad"]):
        for side, det in ((0, -0.07), (1, 0.07)):
            f = midi(m) * 2 ** (det / 12)
            v = saw_blep(f, n, phase0=(j * 0.137 + side * 0.31) % 1) + 0.6 * saw_blep(f * 2 ** (0.04 / 12), n, 0.5)
            place(pad[:, side], v * env, t0, 0.05)
pad_dark = np.stack([fftconv(pad[:, c], fir_lowpass(700)) for c in range(2)], 1)
pad_bright = np.stack([fftconv(pad[:, c], fir_lowpass(2600)) for c in range(2)], 1)
tt = np.arange(N) / SR
bright = np.clip((tt - 1.0) / 7.0, 0, 1)
bright = np.where(tt >= 62, 1.0, np.where(tt >= 54, 0.35, bright))
bright = np.where((tt >= 8) & (tt < 54), 0.75, bright)
pad_mix = pad_dark * (1 - bright[:, None]) + pad_bright * bright[:, None]
pad_gain = np.interp(tt, [0, 6, 8, 54, 56, 62, 82, 86, 90], [0.5, 0.9, 0.8, 0.8, 1.0, 0.85, 0.85, 0.9, 0.0])
pad_mix *= pad_gain[:, None]

# ---------- Arpège pluck ----------
arp = np.zeros((N, 2))
pattern = [0, 2, 4, 1, 3, 4, 2, 1]
for k in range(int(DUR / 0.125)):
    t0 = k * 0.125
    sec = section(t0)
    if sec == "outro" and t0 > 88.5:
        break
    bar = int(t0 // BAR)
    ch = chord_at(bar)
    tones = ch["pad"]
    idx = pattern[k % 8]
    m = tones[idx] + 12
    if sec == "chorus" and (k % 16) in (6, 14):
        m += 12
    vel = 0.55 + 0.45 * ((k % 4) == 0) - 0.15 * ((k % 2) == 1)
    if sec == "intro":
        vel *= min(1.0, 0.25 + t0 / 8.0)
    if sec == "break":
        vel *= 0.8
    dur = 0.45
    n = int(dur * SR)
    tl = np.arange(n) / SR
    f = midi(m)
    sig = (np.sin(2 * np.pi * f * tl) + 0.35 * np.sin(2 * np.pi * 2 * f * tl) * np.exp(-tl / 0.05)
           + 0.12 * np.sin(2 * np.pi * 3 * f * tl) * np.exp(-tl / 0.03))
    sig *= np.exp(-tl / 0.16) * np.minimum(1, tl / 0.003)
    pan = 0.5 + 0.25 * np.sin(k * 0.7)
    place(arp[:, 0], sig, t0, 0.11 * vel * (1 - pan) * 2)
    place(arp[:, 1], sig, t0, 0.11 * vel * pan * 2)
# Écho ping-pong (croche pointée)
d = int(0.375 * SR)
echo = np.zeros_like(arp)
for i, g in enumerate([0.42, 0.26, 0.16, 0.09]):
    src = arp[:, (i + 1) % 2]
    sh = d * (i + 1)
    echo[sh:, i % 2] += src[:-sh] * g
arp = arp + np.stack([fftconv(echo[:, c], fir_lowpass(3500)) for c in range(2)], 1)

# ---------- Basse ----------
bass = np.zeros(N)
for k in range(int(DUR / 0.25)):
    t0 = k * 0.25
    sec = section(t0)
    if sec in ("intro",) or (sec == "break" and t0 < 60) or t0 >= 88:
        continue
    bar = int(t0 // BAR)
    root = chord_at(bar)["root"]
    m = root + (12 if (k % 8) in (3, 7) and sec in ("drive", "chorus") else 0)
    n = int(0.24 * SR)
    tl = np.arange(n) / SR
    f = midi(m)
    sig = 0.8 * np.sin(2 * np.pi * f * tl) + 0.35 * saw_blep(f, n)
    sig *= env_adsr(n, 0.004, 0.08, 0.75, 0.03, 0.2)
    place(bass, sig, t0, 0.32)
bass = fftconv(bass, fir_lowpass(520))

# ---------- Batterie ----------
kick = np.zeros(N)
clap = np.zeros(N)
hats = np.zeros(N)
ticks = np.zeros(N)
sidechain = np.ones(N)


def kick_sample():
    n = int(0.45 * SR)
    tl = np.arange(n) / SR
    f = 46 + 95 * np.exp(-tl / 0.028)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-tl / 0.22)
    click = rng.standard_normal(n) * np.exp(-tl / 0.0025) * 0.25
    return s + click


KICK = kick_sample()
nclap = int(0.4 * SR)
tlc = np.arange(nclap) / SR
CLAP = fftconv(rng.standard_normal(nclap), fir_bandpass(900, 6000, 255))
CLAP_ENV = (np.exp(-tlc / 0.006) * (tlc < 0.012) + np.exp(-np.maximum(0, tlc - 0.012) / 0.012) * ((tlc >= 0.012) & (tlc < 0.022))
            + np.exp(-np.maximum(0, tlc - 0.022) / 0.16) * (tlc >= 0.022))
CLAP = CLAP * CLAP_ENV
nh = int(0.08 * SR)
tlh = np.arange(nh) / SR
HAT = fftconv(rng.standard_normal(nh), fir_highpass(7500, 255)) * np.exp(-tlh / 0.022)
nt = int(0.05 * SR)
tlt = np.arange(nt) / SR
TICK = (np.sin(2 * np.pi * 3100 * tlt) * np.exp(-tlt / 0.007) + 0.5 * np.sin(2 * np.pi * 5300 * tlt) * np.exp(-tlt / 0.004))

for k in range(int(DUR / 0.125)):
    t0 = k * 0.125
    sec = section(t0)
    on_beat = k % 4 == 0
    beat_idx = k // 4
    if sec in ("verse", "drive", "chorus") and on_beat:
        place(kick, KICK, t0, 0.9)
        i = int(t0 * SR)
        m = min(N, i + int(0.3 * SR))
        sidechain[i:m] = np.minimum(sidechain[i:m], 0.35 + 0.65 * (np.arange(m - i) / (0.3 * SR)) ** 0.7)
    if sec == "outro" and on_beat and t0 < 84:
        place(kick, KICK, t0, 0.7)
    if sec in ("drive", "chorus") and on_beat and beat_idx % 2 == 1:
        place(clap, CLAP, t0, 0.5)
    if sec in ("verse", "drive", "chorus"):
        if k % 4 == 2:
            place(hats, HAT, t0, 0.32)
        elif sec in ("drive", "chorus") and k % 2 == 1:
            place(hats, HAT, t0, 0.12 + 0.05 * (k % 3))
    if sec == "drive" and 24 <= t0 < 46:
        acc = 1.0 if k % 4 == 0 else (0.55 if k % 2 == 0 else 0.3)
        place(ticks, TICK, t0, 0.07 * acc)
    if sec == "break" and on_beat:
        place(ticks, TICK, t0, 0.08)

# ---------- Effets : impacts, montées, souffles ----------
fx = np.zeros(N)


def impact(t0, gain=1.0):
    n = int(2.6 * SR)
    tl = np.arange(n) / SR
    f = 34 + 40 * np.exp(-tl / 0.08)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.9)
    noise = fftconv(rng.standard_normal(n), fir_lowpass(5000, 255)) * np.exp(-tl / 0.7) * 0.25
    place(fx, (boom * 0.9 + noise) * gain, t0)


def riser(t0, t1, gain=1.0):
    n = int((t1 - t0) * SR)
    tl = np.arange(n) / SR
    p = tl / (t1 - t0)
    nz = rng.standard_normal(n)
    lo = fftconv(nz, fir_bandpass(300, 1200, 255))
    hi = fftconv(nz, fir_bandpass(2000, 9000, 255))
    s = (lo * (1 - p) + hi * p) * p ** 2.2
    f = 180 + 900 * p ** 2
    s += 0.15 * np.sin(2 * np.pi * np.cumsum(f) / SR) * p ** 2
    place(fx, s * gain, t0)


def whoosh(tc, gain=1.0):
    n = int(0.7 * SR)
    tl = np.arange(n) / SR
    p = tl / 0.7
    nz = rng.standard_normal(n)
    s = fftconv(nz, fir_bandpass(500, 5000, 255))
    e = np.where(p < 0.62, (p / 0.62) ** 2.5, np.exp(-(p - 0.62) / 0.08))
    place(fx, s * e * gain, tc - 0.43)


riser(5.6, 8.0, 0.28)
impact(8.0, 0.9)
riser(59.8, 62.0, 0.26)
impact(62.0, 0.85)
impact(82.0, 0.8)
for tc in (12.0, 24.0, 46.0, 54.0, 74.0):
    whoosh(tc, 0.16)
whoosh(64.0, 0.12)

# ---------- Réverbération ----------
irn = int(2.4 * SR)
tli = np.arange(irn) / SR
ir = np.stack([rng.standard_normal(irn) * np.exp(-tli / 0.55) for _ in range(2)], 1)
ir[:, 0] = fftconv(ir[:, 0], fir_lowpass(6000, 255))
ir[:, 1] = fftconv(ir[:, 1], fir_lowpass(6000, 255))
ir /= np.sqrt((ir ** 2).sum(0))


def fft_rev(x, h):
    L = len(x) + len(h) - 1
    n = 1 << (L - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[: len(x)]


send = pad_mix * 0.35 + arp * 0.5 + np.stack([clap, clap], 1) * 0.35 + np.stack([fx, fx], 1) * 0.3
wet = np.stack([fft_rev(send[:, c], ir[:, c]) for c in range(2)], 1)

# ---------- Mixage ----------
sc = sidechain[:, None]
mix = (pad_mix * sc * 0.9
       + arp * 1.0
       + np.stack([bass * sidechain, bass * sidechain], 1) * 0.8
       + np.stack([kick, kick], 1) * 0.68
       + np.stack([clap * 0.9, clap * 1.1], 1) * 0.8
       + np.stack([hats * 0.8, hats * 1.2], 1) * 0.7
       + np.stack([ticks * 1.1, ticks * 0.9], 1) * 0.8
       + np.stack([fx, fx], 1) * 0.9
       + wet * 0.35)
fade = np.clip((DUR - tt) / 3.5, 0, 1) ** 1.5
mix *= fade[:, None]
mix /= np.abs(mix).max()
mix = np.tanh(mix * 1.6) / np.tanh(1.6)
mix *= 0.89

out = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print("ok", sys.argv[1], out.shape)
