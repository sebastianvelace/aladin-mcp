"""Point 5: DSS2 red image of NGC 4755 with the SIMBAD bright stars labelled (Spanish).

Run: .venv/bin/python resultados/scripts/p5_ngc4755_identificadas.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, str(Path(__file__).parent))
from figuras_es import save, show, sky_axes  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "resultados" / "punto5"
stars = pd.read_csv(OUT / "NGC4755_estrellas_brillantes_SIMBAD.csv").head(9)
hdu = fits.open(OUT / "NGC4755_DSS2red_20arcmin.fits")[0]
wcs = WCS(hdu.header)

fig = plt.figure(figsize=(8, 8))
ax = sky_axes(fig, wcs)
show(ax, hdu.data, cmap="gray_r")
# Label offsets (points) chosen by hand so that neighbouring labels do not overlap.
OFFSETS = {"HD 111904": (14, 10), "kap Cru": (-110, 2), "HD 111990": (-95, 10), "BU Cru": (18, -28),
           "DU Cru": (14, 14), "CC Cru": (14, 10), "CPD-59  4552": (14, -6), "CN Cru": (-100, -30),
           "BV Cru": (18, -4)}
for _, row in stars.iterrows():
    dx, dy = OFFSETS.get(str(row["main_id"]).replace("V* ", "").replace("* ", ""), (14, 10))
    x, y = wcs.world_to_pixel_values(row["ra"], row["dec"])
    red = row["B_V"] > 1
    colour = "red" if red else "tab:blue"
    ax.plot(x, y, "o", mfc="none", mec=colour, ms=16, mew=1.5)
    name = str(row["main_id"]).replace("V* ", "").replace("* ", "")
    ax.annotate(f"{name}\n{row['sp_type']}, V = {row['vmag']:.1f}", (x, y), xytext=(dx, dy),
                textcoords="offset points", fontsize=7, color=colour, weight="bold")
cx, cy = wcs.world_to_pixel_values(193.415, -60.371111)
ax.plot(cx, cy, "x", color="lime", ms=14, mew=3, label="Centro según SIMBAD")
ax.legend(loc="lower left", fontsize=8)
ax.set_title("NGC 4755 – DSS2 roja, 20′, con las estrellas brillantes de SIMBAD")
save(fig, OUT / "NGC4755_DSS2red_estrellas_identificadas.png")
