#MAIN SCRIPT

#Robotbesturing: spraakgestuurd sorteren op warme en koude kleuren.

#Hoe het werkt:
#- luister.py (laptop + microfoon) herkent wat je zegt en zet het commando
#  in het bestand brug/commando.jsonl. Dit script leest dat bestand.
#- "warm"  -> volgende warme blok (geel/rood) naar de warme zone
#- "koud"  -> volgende koude blok (groen/blauw) naar de koude zone
#- "xmen"  -> ("to me, my x-men") robot gaat naar home
#- "stop"  -> robot gaat naar home en het programma stopt
#- "twijfel" -> robot doet niets

#Met TEST_ZONDER_MICROFOON = True sorteert de robot alle blokken zelf.

import json
import os
import time

from DobotEDU import *

TEST_ZONDER_MICROFOON = False   # True = alle blokken zelf sorteren | False = spraakherkenning

BRUG_MAP = r"C:\Users\Bram\Downloads\spraaksorteren\spraaksorteren\brug"

# --- Raster met blokken (Basic scene) --------------------------------------
# 4 kolommen van 4 blokken: groen, blauw, geel, rood.
KOLOMMEN = ["groen", "blauw", "geel", "rood"]
RIJEN = 4
WARM = {"rood", "geel"}

EERSTE_BLOK = (280.95, -30, -42.38)   # bovenste groene blok
KOLOM_STAP = (0, 20)                  # verschil naar het blok ernaast
RIJ_STAP = (18.35, 0)                 # verschil naar het blok eronder

# --- Afleverzones -----------------------------------------------------------
ZONES = {
    "warm": (334, 69, -42.38),
    "koud": (334, -69, -42.38),
}
ZONE_STAPPEN = {
    #        naast elkaar   volgende rij
    "warm": ((0, 20),       (-18.35, 0)),
    "koud": ((0, -20),      (-18.35, 0)),
}
PER_RIJ = 2


def blok_positie(kolom, rij):
    x, y, z = EERSTE_BLOK
    return (x + kolom * KOLOM_STAP[0] + rij * RIJ_STAP[0],
            y + kolom * KOLOM_STAP[1] + rij * RIJ_STAP[1],
            z)


def zone_positie(soort, nummer):
    x, y, z = ZONES[soort]
    (kx, ky), (rx, ry) = ZONE_STAPPEN[soort]
    kolom, rij = nummer % PER_RIJ, nummer // PER_RIJ
    return (x + kolom * kx + rij * rx, y + kolom * ky + rij * ry, z)


voorraad = {"warm": [], "koud": []}
for rij in range(RIJEN):
    for k, kleur in enumerate(KOLOMMEN):
        soort = "warm" if kleur in WARM else "koud"
        voorraad[soort].append((kleur, blok_positie(k, rij)))


# --- Robotbewegingen --------------------------------------------------------
def beweeg(x, y, z):
    m_lite.set_ptpcmd(0, x, y, z, 0)


def zuignap(aan):
    m_lite.set_endeffector_suctioncup(True, aan)


def pak_en_plaats(van, naar):
    beweeg(*van)
    zuignap(True)
    beweeg(*naar)
    zuignap(False)


# --- Sorteerlogica ----------------------------------------------------------
tellers = {"warm": 0, "koud": 0, "twijfel": 0}
cyclustijden = []


def verwerk(soort):
    if soort not in voorraad:
        tellers["twijfel"] += 1
        print("Niet verstaan -> robot doet niets")
        return
    if not voorraad[soort]:
        print(f"Geen {soort}e blokken meer over")
        return
    kleur, van = voorraad[soort].pop(0)
    naar = zone_positie(soort, tellers[soort])
    start = time.time()
    pak_en_plaats(van, naar)
    duur = time.time() - start
    tellers[soort] += 1
    cyclustijden.append(duur)
    gem = sum(cyclustijden) / len(cyclustijden)
    print(f"{soort}: {kleur} blok gesorteerd in {duur:.1f} s (gemiddeld {gem:.1f} s) {tellers}")


def wacht_op_commando(pad, positie):
    """Wacht op een nieuwe regel in het commandobestand."""
    while True:
        with open(pad, "r") as f:
            f.seek(positie)
            regel = f.readline()
            if regel.endswith("\n"):
                positie = f.tell()
                if regel.strip():
                    return json.loads(regel), positie
                continue
        time.sleep(0.2)


# --- Hoofdprogramma ---------------------------------------------------------
m_lite.set_homecmd()

if TEST_ZONDER_MICROFOON:
    while voorraad["warm"] or voorraad["koud"]:
        for soort in ("warm", "koud"):
            if voorraad[soort]:
                verwerk(soort)
else:
    pad = os.path.join(BRUG_MAP, "commando.jsonl")
    if not os.path.exists(pad):
        raise SystemExit("Bestand niet gevonden: " + pad +
                         "\nStart eerst luister.py en controleer BRUG_MAP.")
    positie = os.path.getsize(pad)          # oude commando's overslaan
    print("Klaar! Zeg: warm, koud, to me my x-men of stop")

    while voorraad["warm"] or voorraad["koud"]:
        commando, positie = wacht_op_commando(pad, positie)
        soort = commando.get("besluit")
        print("Ontvangen:", soort, commando.get("zekerheid"))
        if soort == "stop":
            print("Stop-commando ontvangen")
            break
        if soort == "xmen":
            print("To me, my X-Men! -> robot gaat naar home")
            m_lite.set_homecmd()
            continue
        verwerk(soort)

print("Klaar:", tellers)
m_lite.set_homecmd()