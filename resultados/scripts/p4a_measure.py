"""Point 4(a): angular size of the LMC in each band and of 30 Doradus, at 2, 3 and 5 sigma.

Uses the same code as the MCP tool measure_angular_size and draws Spanish diagnostic figures.
Run: .venv/bin/python resultados/scripts/p4a_measure.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from figuras_es import save, show, sky_axes  # noqa: E402

from aladin_mcp import imaging  # noqa: E402

R = Path(__file__).resolve().parents[2] / "resultados" / "punto4"
D_KPC = 50.0

# (key, label, FITS, smoothing sigma in degrees or None for the tool default, valid?, note)
BANDS = [
    ("optico", "Óptico (Mellinger RGB, luminancia)", "LMC_optico_Mellinger_luminancia_20deg.fits", None, True, ""),
    ("akari", "Infrarrojo lejano (AKARI 140 µm)", "LMC_infrarrojo_AKARI140um_20deg.fits", None, True, ""),
    ("planck857", "Submilimétrico (Planck 857 GHz)", "LMC_radio_Planck857GHz_20deg.fits", None, True,
     "polvo de la Vía Láctea alrededor"),
    ("planck030", "Radio (Planck 30 GHz)", "LMC_radio_Planck030GHz_20deg.fits", None, True,
     "dominado por 30 Doradus y regiones HII"),
    ("fermi", "Rayos gamma (Fermi 3–300 GeV, suavizado σ = 0.5°)", "LMC_gamma_Fermi3-300GeV_20deg.fits", 0.5, True,
     "cota superior: el suavizado ensancha la mancha"),
    ("fermi4", "Rayos gamma (Fermi 1–3 GeV, suavizado σ = 0.5°)", "LMC_gamma_Fermi4_20deg.fits", 0.5, True,
     "comprobación cruzada"),
    ("dss", "Óptico (DSS2 roja, SkyView) – DESCARTADA", "LMC_optico_DSS2red_20deg.fits", None, False,
     "el contorno sigue los escalones entre placas"),
    ("30dor", "30 Doradus (DSS2 roja, 1.5°)", "30Dor_optico_DSS2red_1.5deg.fits", None, True,
     "solo el núcleo brillante; costura de placa a la derecha"),
]

rows = []
for key, label, name, sigma_deg, valid, note in BANDS:
    path = R / name
    sigma_px = None
    if sigma_deg:
        sigma_px = sigma_deg / abs(fits.getheader(path)["CDELT1"])
    for umbral in (2.0, 3.0, 5.0):
        row = {"clave": key, "banda": label, "umbral_sigma": umbral, "valida": valid, "nota": note}
        try:
            m = imaging.measure_size(str(path), umbral, sigma_px, D_KPC, return_arrays=True)
        except ValueError as exc:
            row["error"] = str(exc)
            rows.append(row)
            continue
        if m["region_elegida"].startswith("largest"):
            row["valida"] = False
            row["nota"] = "el centro queda bajo el umbral: la región elegida puede ser otra fuente"
        fig = plt.figure(figsize=(7, 7))
        ax = sky_axes(fig, m["_wcs"])
        # Show what was measured: for the extra-smoothed Fermi maps, the smoothed map.
        shown = ndimage.gaussian_filter(np.nan_to_num(m["_data"]), sigma_px) if sigma_px else m["_data"]
        show(ax, shown, cmap="magma" if sigma_px else "gray")
        ax.contour(m["_region"], levels=[0.5], colors="cyan", linewidths=1.3)
        ax.set_title(f"{label}\numbral = fondo + {umbral:g} σ  →  D ≈ {m['diametro_equivalente_deg']:.2f}°",
                     fontsize=10)
        png = R / f"medida_{key}_umbral{umbral:g}.png"
        save(fig, png)
        row.update({
            "D_equiv_deg": m["diametro_equivalente_deg"], "D_equiv_arcmin": m["diametro_equivalente_arcmin"],
            "eje_mayor_deg": m["eje_mayor_deg"], "eje_menor_deg": m["eje_menor_deg"],
            "D_fisico_kpc": m["diametro_fisico_kpc"], "toca_borde": m["toca_el_borde"],
            "fraccion_imagen": m["fraccion_de_la_imagen"], "png": str(png.relative_to(R.parents[1])),
        })
        rows.append(row)

json.dump(rows, open(R / "medidas_diametro.json", "w"), indent=2, ensure_ascii=False)

# Summary panel at 3 sigma for the bands used in the answer table.
panel = [k for k in ("optico", "akari", "planck857", "planck030", "fermi", "30dor")]
from PIL import Image  # noqa: E402

ims = [Image.open(R / f"medida_{k}_umbral3.png").convert("RGB") for k in panel]
w = 700
ims = [im.resize((w, int(im.height * w / im.width))) for im in ims]
h = max(im.height for im in ims)
out = Image.new("RGB", (3 * w, 2 * h), "white")
for i, im in enumerate(ims):
    out.paste(im, ((i % 3) * w, (i // 3) * h))
out.save(R / "panel_medidas_umbral3.png", dpi=(180, 180))

for r in rows:
    if "error" in r:
        print(f"{r['clave']:10s} u={r['umbral_sigma']:<3g} ERROR {r['error']}")
    else:
        print(f"{r['clave']:10s} u={r['umbral_sigma']:<3g} D={r['D_equiv_deg']:6.2f}° ({r['D_equiv_arcmin']:6.1f}') "
              f"ejes={r['eje_mayor_deg']:.2f}x{r['eje_menor_deg']:.2f}° {r['D_fisico_kpc']:5.2f} kpc "
              f"valida={r['valida']} borde={r['toca_borde']}")
