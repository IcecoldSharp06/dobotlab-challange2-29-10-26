#Script voor het trainen van alle verzamelde audio

#Output: Spraakmodel.joblib

import glob
import json
import os
import time

import joblib
import numpy as np
import soundfile as sf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from audio import features

DATA_MAP = "data"
KLASSEN = ["warm", "koud", "stop", "xmen"]

X, y = [], []
for klasse in KLASSEN:
    for pad in glob.glob(os.path.join(DATA_MAP, klasse, "*.wav")):
        audio, _ = sf.read(pad, dtype="float32")
        X.append(features(audio))
        y.append(klasse)

X, y = np.array(X), np.array(y)
aantallen = {k: int((y == k).sum()) for k in KLASSEN}
print("Aantal opnames per woord:", aantallen)
if min(aantallen.values()) < 10:
    raise SystemExit("Te weinig data. Neem minstens 20 opnames per woord op (liefst 40+).")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42)

model = make_pipeline(StandardScaler(), SVC(kernel="rbf", probability=True, random_state=42))
start = time.time()
model.fit(X_train, y_train)
trainduur = time.time() - start

voorspeld = model.predict(X_test)
nauwkeurigheid = accuracy_score(y_test, voorspeld)
matrix = confusion_matrix(y_test, voorspeld, labels=KLASSEN)

print(f"\nNauwkeurigheid op testset: {nauwkeurigheid:.1%}")
print("\nConfusion matrix (rij = echt, kolom = voorspeld):", KLASSEN)
print(matrix)
print("\n" + classification_report(y_test, voorspeld, labels=KLASSEN, zero_division=0))

joblib.dump({"model": model, "klassen": KLASSEN}, "spraakmodel.joblib")
with open("resultaten.json", "w") as f:
    json.dump({
        "datum": time.strftime("%Y-%m-%d %H:%M"),
        "aantallen": aantallen,
        "aantal_train": int(len(X_train)),
        "aantal_test": int(len(X_test)),
        "nauwkeurigheid": round(float(nauwkeurigheid), 4),
        "confusion_matrix": matrix.tolist(),
        "klassen": KLASSEN,
        "trainduur_sec": round(trainduur, 2),
    }, f, indent=2)
print("Model opgeslagen als spraakmodel.joblib, resultaten in resultaten.json")
