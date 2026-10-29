#Script voor het verzamelen van audio.

#Output: in data -> folders voor alle individuele woorden

import os
import time

import sounddevice as sd
import soundfile as sf

from audio import BLOK_SAMPLES, SAMPLERATE, kalibreer, wacht_op_stilte, wacht_op_woord

KLASSEN = ["warm", "koud", "stop", "xmen"]
ZINNEN = {"xmen": "to me, my x-men"}
DATA_MAP = "data"
PER_RONDE = 20

for k in KLASSEN:
    os.makedirs(os.path.join(DATA_MAP, k), exist_ok=True)


def tel():
    return {k: len(os.listdir(os.path.join(DATA_MAP, k))) for k in KLASSEN}


with sd.InputStream(samplerate=SAMPLERATE, channels=1, blocksize=BLOK_SAMPLES) as stream:
    drempel = kalibreer(stream)
    while True:
        print("\nHuidige aantallen:", tel())
        keuze = input(f"Welk woord opnemen? {KLASSEN} (of q om te stoppen): ").strip().lower()
        if keuze == "q":
            break
        if keuze not in KLASSEN:
            print("Onbekende keuze.")
            continue
        hint = f'zeg "{ZINNEN.get(keuze, keuze)}"'
        print(f"Klaar voor {PER_RONDE} opnames: {hint}, telkens met een korte pauze.")
        for i in range(PER_RONDE):
            audio = wacht_op_woord(stream, drempel)
            pad = os.path.join(DATA_MAP, keuze, f"{int(time.time() * 1000)}.wav")
            sf.write(pad, audio, SAMPLERATE)
            print(f"  {i + 1}/{PER_RONDE} opgeslagen")
            wacht_op_stilte(stream, drempel)

print("Totaal:", tel())
