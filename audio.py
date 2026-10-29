#script die de audio regeld voor "Luister.py" (instellingen)

from collections import deque

import librosa
import numpy as np

SAMPLERATE = 16000
BLOK = 0.1
BLOK_SAMPLES = int(SAMPLERATE * BLOK)
VOORLOOP = 3
LENGTE = 3.5
LENGTE_BLOKKEN = round(LENGTE / BLOK)


def rms(blok):
    return float(np.sqrt(np.mean(blok ** 2)))


def kalibreer(stream, seconden=1.5):
    """Meet het achtergrondgeluid en geeft een volumedrempel terug."""
    print(f"Even stil zijn... achtergrondgeluid meten ({seconden} s)")
    niveaus = []
    for _ in range(int(seconden / BLOK)):
        data, _ = stream.read(BLOK_SAMPLES)
        niveaus.append(rms(data[:, 0]))
    drempel = max(np.mean(niveaus) * 4, 0.01)
    print(f"Volumedrempel ingesteld op {drempel:.4f}")
    return drempel


def wacht_op_woord(stream, drempel):
    """Wacht tot er geluid boven de drempel is en geeft LENGTE seconden audio terug.

    Er worden ook een paar blokken van vóór het geluid meegenomen, zodat het
    begin van het woord niet wordt afgeknipt.
    """
    voorloop = deque(maxlen=VOORLOOP)
    while True:
        data, _ = stream.read(BLOK_SAMPLES)
        blok = data[:, 0].copy()
        if rms(blok) > drempel:
            blokken = list(voorloop) + [blok]
            while len(blokken) < LENGTE_BLOKKEN:
                data, _ = stream.read(BLOK_SAMPLES)
                blokken.append(data[:, 0].copy())
            return np.concatenate(blokken).astype(np.float32)
        voorloop.append(blok)


def wacht_op_stilte(stream, drempel, blokken=3):
    """Wacht tot het een paar blokken stil is (voorkomt dubbele detectie)."""
    stil = 0
    while stil < blokken:
        data, _ = stream.read(BLOK_SAMPLES)
        stil = stil + 1 if rms(data[:, 0]) < drempel else 0


def features(audio):
    """Feature-vector: gemiddelde en spreiding van MFCC's en hun verandering (delta)."""
    audio = librosa.util.fix_length(audio, size=int(SAMPLERATE * LENGTE))
    piek = np.max(np.abs(audio))
    if piek > 0:
        audio = audio / piek
    mfcc = librosa.feature.mfcc(y=audio, sr=SAMPLERATE, n_mfcc=20)
    delta = librosa.feature.delta(mfcc)
    return np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1),
                           delta.mean(axis=1), delta.std(axis=1)])
