"""Aladin Desktop captures for the report, driven through SAMP (aladin_send).

Each view loads local FITS files (the CDS was unreachable), sets zoom and contrast, draws the
"ruler" measurements of p4_medidas_perfiles.py and saves Aladin's own view as PNG.
Needs Aladin Desktop open with its SAMP hub. Run: .venv/bin/python resultados/scripts/p_capturas_aladin.py
"""

import json
from pathlib import Path

import pandas as pd

from aladin_mcp import samp

ROOT = Path(__file__).resolve().parents[2] / "resultados"
P4, P5, OUT = ROOT / "punto4", ROOT / "punto5", ROOT / "capturas"
OUT.mkdir(exist_ok=True)
rulers = {r["clave"]: r for r in json.load(open(P4 / "medidas_perfiles.json"))}

BANDS = [  # key, FITS, zoom, colour-map stretch, label
    ("optico", "LMC_optico_Mellinger_luminancia_20deg.fits", "20deg", "sqrt", "Óptico (Mellinger)"),
    ("akari", "LMC_infrarrojo_AKARI140um_20deg.fits", "20deg", "sqrt", "Infrarrojo AKARI 140 um"),
    ("planck857", "LMC_radio_Planck857GHz_20deg.fits", "20deg", "sqrt", "Submm Planck 857 GHz"),
    ("planck030", "LMC_radio_Planck030GHz_20deg.fits", "20deg", "linear", "Radio Planck 30 GHz"),
    ("fermi", "LMC_gamma_Fermi3-300GeV_20deg.fits", "20deg", "linear", "Gamma Fermi 3-300 GeV"),
    ("30dor", "30Dor_optico_DSS2red_1.5deg.fits", "1.5deg", "log", "30 Doradus DSS2 roja"),
]


def run(lines, name):
    out = OUT / name
    reply = samp.send("; ".join(lines + [f"save {out}"]), 90)
    ok = reply.get("enviado") and all(r.get("confirmado") for r in reply["respuestas"])
    print(f"{name}: {'ok' if ok and out.exists() else 'FAILED ' + json.dumps(reply, ensure_ascii=False)[:300]}")


def ruler(m, axis, colour):
    (r1, d1), (r2, d2) = m[f"extremos_{axis}"]
    value, unit = m[f"eje_{axis}"], "'" if m["unidad"] == "arcmin" else " deg"
    return [f"draw {colour} line({r1},{d1},{r2},{d2})",
            f'draw {colour} string({r2},{d2},"{axis}: {value:.2f}{unit}")']


for key, fits_name, zoom, stretch, label in BANDS:
    m = rulers[key]
    lines = ["reset", f"load {P4 / fits_name}", "sync", f"cm gray {stretch} autocut", f"zoom {zoom}"]
    if m["eje_mayor"] is not None:
        lines += ruler(m, "mayor", "red") + ruler(m, "menor", "yellow")
    else:
        lines.append(f'draw red string({m["extremos_mayor"][1][0]},{m["extremos_mayor"][1][1]},"sin borde medible en el mapa crudo")')
    run(lines, f"aladin_regla_{key}.png")

# Mellinger channels combined into a colour plane inside Aladin.
run(["reset"] + [f"load {P4 / f'LMC_optico_Mellinger{c}_20deg.fits'}" for c in ("Red", "Green", "Blue")]
    + ["sync", "RGB 1 2 3", "sync", "zoom 20deg"], "aladin_LMC_Mellinger_RGB.png")

# Bonanos+ 2009 massive stars over the optical image.
run(["reset", f"load {P4 / 'LMC_optico_Mellinger_luminancia_20deg.fits'}", "sync", "cm gray sqrt autocut",
     f"load {P4 / 'Bonanos2009_LMC_para_Aladin.xml'}", "sync", "zoom 12deg"], "aladin_Bonanos2009_sobre_LMC.png")

# NGC 4755 with its SIMBAD bright stars labelled.
stars = pd.read_csv(P5 / "NGC4755_estrellas_brillantes_SIMBAD.csv").head(6)
labels = [f'draw {"red" if bv > 1 else "cyan"} string({ra},{dec},"{str(n).replace("V* ", "").replace("* ", "")}")'
          for n, ra, dec, bv in zip(stars["main_id"], stars["ra"], stars["dec"], stars["B_V"])]
run(["reset", f"load {P5 / 'NGC4755_DSS2red_20arcmin.fits'}", "sync", "cm gray log autocut", "zoom 15arcmin"]
    + labels, "aladin_NGC4755.png")
