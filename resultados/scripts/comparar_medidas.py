"""Compare your manual Aladin measurements with the automatic ones and with the catalogue values.

1. Fill resultados/punto4/medidas_manuales.csv (axes in degrees; the 30 Dor row in arcminutes).
2. Run: .venv/bin/python resultados/scripts/comparar_medidas.py
Outputs: resultados/punto4/comparacion_medidas.csv and comparacion_medidas.png
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from figuras_es import save  # noqa: E402

R = Path(__file__).resolve().parents[2] / "resultados" / "punto4"

# Manual-sheet row -> key in medidas_diametro.json; 30 Dor is handled in arcminutes.
ROWS = {"optico": "optico", "AKARI": "akari", "Planck 857 GHz": "planck857", "Planck 30 GHz": "planck030",
        "Fermi": "fermi", "30 Dor (minutos de arco)": "30dor"}
# Catalogue references (major, minor axes): SIMBAD and RC3 for the LMC (deg), SIMBAD for 30 Dor (arcmin).
REFS = {"LMC SIMBAD": (5.38, 4.58), "LMC RC3 D25": (10.76, 9.16)}
REF_30DOR = {"30 Dor SIMBAD": (40.0, 25.0)}

manual = pd.read_csv(R / "medidas_manuales.csv")
manual = manual.dropna(subset=["eje_mayor_grados"])
if manual.empty:
    sys.exit("medidas_manuales.csv is still empty: fill in at least one row and run again.")

auto = json.load(open(R / "medidas_diametro.json"))
auto_by = {(r["clave"], r["umbral_sigma"]): r for r in auto if "eje_mayor_deg" in r}

rows = []
for _, m in manual.iterrows():
    key = ROWS.get(str(m["banda"]).strip())
    if key is None:
        print(f"Unknown band '{m['banda']}', skipped. Valid names: {list(ROWS)}")
        continue
    factor = 60.0 if key == "30dor" else 1.0  # automatic values are in degrees
    a = {u: auto_by.get((key, u)) for u in (2.0, 3.0, 5.0)}
    rows.append({
        "banda": m["banda"],
        "unidad": "arcmin" if key == "30dor" else "grados",
        "manual_mayor": m["eje_mayor_grados"], "manual_menor": m["eje_menor_grados"],
        "auto3s_mayor": round(a[3.0]["eje_mayor_deg"] * factor, 2) if a[3.0] else None,
        "auto3s_menor": round(a[3.0]["eje_menor_deg"] * factor, 2) if a[3.0] else None,
        "auto_mayor_rango_5s_2s": (f"{a[5.0]['eje_mayor_deg'] * factor:.2f}–{a[2.0]['eje_mayor_deg'] * factor:.2f}"
                                   if a[5.0] and a[2.0] else None),
        "diferencia_mayor_%": (round(100 * (m["eje_mayor_grados"] / (a[3.0]["eje_mayor_deg"] * factor) - 1), 1)
                               if a[3.0] else None),
        "comentario": m.get("comentario"),
    })
table = pd.DataFrame(rows)
table.to_csv(R / "comparacion_medidas.csv", index=False)
print(table.to_string(index=False))

# Figure: major and minor axes, manual vs automatic (bar = 3 sigma, whisker = 5 to 2 sigma range).
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [3, 1]})
for ax, subset, refs, unit in [(ax1, table[table["unidad"] == "grados"], REFS, "grados"),
                               (ax2, table[table["unidad"] == "arcmin"], REF_30DOR, "minutos de arco")]:
    if subset.empty:
        ax.set_visible(False)
        continue
    x = np.arange(len(subset))
    for off, col, label, colour in [(-0.2, "manual_mayor", "Manual (Aladin)", "tab:orange"),
                                    (0.2, "auto3s_mayor", "Automática 3σ", "tab:blue")]:
        ax.bar(x + off, subset[col], 0.38, label=label, color=colour)
    lo_hi = subset["auto_mayor_rango_5s_2s"].dropna().str.split("–", expand=True).astype(float)
    if not lo_hi.empty:
        idx = [list(subset.index).index(i) for i in lo_hi.index]
        ax.vlines(np.array(idx) + 0.2, lo_hi[0], lo_hi[1], color="k", lw=1.5, label="Rango automático 5σ–2σ")
    for (name, (major, _)), ls in zip(refs.items(), ["--", ":"]):
        ax.axhline(major, ls=ls, color="0.3", label=f"{name}: {major:g}")
    ax.set_xticks(x, subset["banda"], rotation=20)
    ax.set_ylabel(f"Eje mayor ({unit})")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
fig.suptitle("Eje mayor de la emisión: medida manual frente a la automática y a los catálogos")
save(fig, R / "comparacion_medidas.png")
print(f"\nSaved {R / 'comparacion_medidas.csv'} and {R / 'comparacion_medidas.png'}")
