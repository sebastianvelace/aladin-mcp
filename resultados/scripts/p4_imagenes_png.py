"""Point 4: Spanish-labelled PNG of every survey image of the LMC and 30 Doradus.

Run: .venv/bin/python resultados/scripts/p4_imagenes_png.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, str(Path(__file__).parent))
from figuras_es import save, show, sky_axes  # noqa: E402

R = Path(__file__).resolve().parents[2] / "resultados" / "punto4"

TITLES = {
    "LMC_optico_DSS2red_20deg": "LMC – óptico, DSS2 placa roja (SkyView), 20°\nmosaico con escalones entre placas",
    "LMC_optico_Mellinger_luminancia_20deg": "LMC – óptico, Mellinger (luminancia R+G+B), 20°",
    "LMC_optico_MellingerRed_20deg": "LMC – óptico, Mellinger canal rojo, 20°",
    "LMC_optico_MellingerGreen_20deg": "LMC – óptico, Mellinger canal verde, 20°",
    "LMC_optico_MellingerBlue_20deg": "LMC – óptico, Mellinger canal azul, 20°",
    "LMC_infrarrojo_AKARI140um_20deg": "LMC – infrarrojo lejano, AKARI 140 µm, 20°",
    "LMC_radio_Planck857GHz_20deg": "LMC – submilimétrico, Planck 857 GHz (polvo), 20°",
    "LMC_radio_Planck030GHz_20deg": "LMC – radio, Planck 30 GHz, 20°",
    "LMC_gamma_Fermi3-300GeV_20deg": "LMC – rayos gamma, Fermi 3–300 GeV (sin suavizar), 20°",
    "LMC_gamma_Fermi1_20deg": "LMC – rayos gamma, Fermi 30–100 MeV, 20°",
    "LMC_gamma_Fermi2_20deg": "LMC – rayos gamma, Fermi 100–300 MeV, 20°",
    "LMC_gamma_Fermi3_20deg": "LMC – rayos gamma, Fermi 0.3–1 GeV, 20°",
    "LMC_gamma_Fermi4_20deg": "LMC – rayos gamma, Fermi 1–3 GeV, 20°",
    "30Dor_optico_DSS2red_1.5deg": "Nebulosa de la Tarántula (30 Doradus) – óptico, DSS2 roja, 1.5°",
}

for stem, title in TITLES.items():
    hdu = fits.open(R / f"{stem}.fits")[0]
    fig = plt.figure(figsize=(7, 7))
    ax = sky_axes(fig, WCS(hdu.header).celestial)
    show(ax, np.asarray(hdu.data, dtype=float), cmap="magma" if "Fermi" in stem else "gray")
    ax.set_title(title, fontsize=10)
    save(fig, R / f"{stem}.png")
    print(stem)

# Colour composite of the three Mellinger channels.
channels = [fits.open(R / f"LMC_optico_Mellinger{c}_20deg.fits")[0] for c in ("Red", "Green", "Blue")]
planes = []
for ch in channels:
    d = np.nan_to_num(ch.data.astype(float))
    lo, hi = np.percentile(d, [1, 99.7])
    planes.append(np.clip((d - lo) / (hi - lo), 0, 1) ** 0.6)
fig = plt.figure(figsize=(7.5, 7.5))
ax = sky_axes(fig, WCS(channels[0].header).celestial)
ax.imshow(np.dstack(planes), origin="lower")
ax.set_title("Gran Nube de Magallanes – óptico (Mellinger RGB), 20°")
save(fig, R / "LMC_optico_Mellinger_color_20deg.png")
