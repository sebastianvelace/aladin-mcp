"""Point 4(a): angular size of the LMC in four bands and of 30 Doradus, at several thresholds.

Uses the same code as the MCP tool measure_angular_size.
Run: .venv/bin/python resultados/scripts/p4a_measure.py
"""

import json
import shutil
from pathlib import Path

import numpy as np

from aladin_mcp import imaging

R = Path(__file__).resolve().parents[2] / "resultados" / "punto4"
D_KPC = 50.0
IMAGES = {
    "optico DSS2 red": "LMC_optico_DSS2red_20deg.fits",
    "infrarrojo AKARI 140 um": "LMC_infrarrojo_AKARI140um_20deg.fits",
    "radio/submm Planck 857 GHz": "LMC_radio_Planck857GHz_20deg.fits",
    "gamma Fermi 3-300 GeV": "LMC_gamma_Fermi3-300GeV_20deg.fits",
    "30 Dor (optico DSS2 red)": "30Dor_optico_DSS2red_1.5deg.fits",
}

rows = []
for band, name in IMAGES.items():
    path = R / name
    if not path.exists():
        rows.append({"banda": band, "error": "image not downloaded"})
        continue
    for umbral in (2.0, 3.0, 5.0):
        try:
            m = imaging.measure_size(str(path), umbral, None, D_KPC)
        except Exception as exc:
            rows.append({"banda": band, "umbral_sigma": umbral, "error": str(exc)})
            continue
        clean_png = R / f"medida_{path.stem}_umbral{umbral:g}.png"
        shutil.move(m["png_diagnostico"], clean_png)
        rows.append({
            "banda": band, "umbral_sigma": umbral,
            "D_equiv_deg": m["diametro_equivalente_deg"], "D_equiv_arcmin": m["diametro_equivalente_arcmin"],
            "eje_mayor_deg": m["eje_mayor_deg"], "eje_menor_deg": m["eje_menor_deg"],
            "D_fisico_kpc": m["diametro_fisico_kpc"], "toca_borde": m["toca_el_borde"],
            "fraccion_imagen": m["fraccion_de_la_imagen"], "region": m["region_elegida"],
            "avisos": m["avisos"], "png": str(clean_png),
        })

json.dump(rows, open(R / "medidas_diametro.json", "w"), indent=2, ensure_ascii=False)
for r in rows:
    if "error" in r:
        print(f"{r['banda']:28s} u={r.get('umbral_sigma')}  ERROR {r['error']}")
    else:
        print(f"{r['banda']:28s} u={r['umbral_sigma']:<3g} D={r['D_equiv_deg']:6.2f} deg ({r['D_equiv_arcmin']:6.1f}')"
              f" ejes={r['eje_mayor_deg']:.2f}x{r['eje_menor_deg']:.2f} deg  {r['D_fisico_kpc']:5.2f} kpc"
              f" borde={r['toca_borde']} frac={r['fraccion_imagen']} {'!' if r['avisos'] else ''}")
