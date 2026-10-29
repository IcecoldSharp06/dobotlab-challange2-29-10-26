#Live luisteren en commando's naar de robot sturen (zonder internet).

#Elke keer dat je iets zegt, herkent het model het woord. Het commando wordt
#in het bestand brug/commando.jsonl gezet; het robotscript in DobotLab leest
#dat bestand en voert het uit.

#- Onder de DREMPEL is het model niet zeker genoeg -> "twijfel"
#  (de robot doet niets en je kunt het opnieuw zeggen).
#- Elke herkenning wordt opgeslagen in herkenningen.csv (voor je testresultaten).

import csv
import json
import os
import time

import joblib
import sounddevice as sd

from audio import BLOK_SAMPLES, SAMPLERATE, features, kalibreer, wacht_op_stilte, wacht_op_woord

DREMPEL = 0.60                         # minimale zekerheid voor een besluit

MAP = os.path.dirname(os.path.abspath(__file__))
BRUG_MAP = os.path.join(MAP, "brug")
COMMANDO_BESTAND = os.path.join(BRUG_MAP, "commando.jsonl")
LOG_BESTAND = os.path.join(MAP, "herkenningen.csv")

model = joblib.load(os.path.join(MAP, "spraakmodel.joblib"))["model"]

os.makedirs(BRUG_MAP, exist_ok=True)
open(COMMANDO_BESTAND, "a").close()
print("Brugmap:", BRUG_MAP)
print("  -> dit pad moet bij BRUG_MAP staan in je DobotLab-script\n")

nieuw = not os.path.exists(LOG_BESTAND)
log = open(LOG_BESTAND, "a", newline="")
schrijver = csv.writer(log)
if nieuw:
    schrijver.writerow(["tijd", "id", "model", "zekerheid", "besluit"])

nr = 0
with sd.InputStream(samplerate=SAMPLERATE, channels=1, blocksize=BLOK_SAMPLES) as stream:
    drempel = kalibreer(stream)
    print('\nLuisteren... zeg "warm", "koud", "stop" of "to me, my x-men" (Ctrl+C om te stoppen)')
    try:
        while True:
            audio = wacht_op_woord(stream, drempel)
            kansen = model.predict_proba([features(audio)])[0]
            i = kansen.argmax()
            woord, zekerheid = model.classes_[i], float(kansen[i])
            besluit = woord if zekerheid >= DREMPEL else "twijfel"

            nr += 1
            schrijver.writerow([time.strftime("%H:%M:%S"), nr, woord, round(zekerheid, 3), besluit])
            log.flush()
            print(f"[{nr}] gehoord: {woord} ({zekerheid:.0%}) -> {besluit}")

            with open(COMMANDO_BESTAND, "a") as f:
                f.write(json.dumps({"id": nr, "besluit": besluit,
                                    "zekerheid": round(zekerheid, 3)}) + "\n")
            wacht_op_stilte(stream, drempel)
    except KeyboardInterrupt:
        pass

log.close()