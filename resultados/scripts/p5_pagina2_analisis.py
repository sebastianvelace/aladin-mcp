"""Point 5(1): analyse the Jewel Box photo on page 2 of the workshop sheet.

Detects stars in the printed photo, finds the cluster centre as the peak of the stellar
surface density, draws the X and a square, and estimates colour (O..M bar) and brightness
(dot scale 1-10) for the stars inside the square. Estimates are as rough as the exercise
intends: the input is a phone photo of a printed page.
Run: .venv/bin/python resultados/scripts/p5_pagina2_analisis.py
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT = Path(__file__).resolve().parents[2] / "resultados" / "punto5"
page = Image.open(OUT / "pagina2.jpg").convert("RGB")
rgb = np.asarray(page).astype(float)

# Region of the cluster photo and of the scales on the page (pixels of pagina2.jpg).
X0, Y0, X1, Y1 = 180, 428, 572, 782  # excludes the paper fold at y~795
BAR_Y = slice(390, 404)
SWATCH_X = {"O": (191, 209), "B": (212, 229), "A": (234, 249), "F1": (253, 265), "F2": (269, 284),
            "G": (288, 306), "K1": (312, 324), "K2": (330, 348), "M": (352, 368)}
CLASSES = list(SWATCH_X)

swatch = {k: rgb[BAR_Y, a:b].reshape(-1, 3).mean(axis=0) for k, (a, b) in SWATCH_X.items()}


def chroma(c):
    """Brightness-independent colour: normalised (r, g, b)."""
    return c / max(c.sum(), 1)


photo = rgb[Y0:Y1, X0:X1]
lum = photo.mean(axis=2)
bg = ndimage.median_filter(lum, size=25)
mask = (lum - bg) > 80  # lower thresholds pick up paper grain and JPEG noise
labels, n = ndimage.label(mask)
objs = ndimage.find_objects(labels)

stars = []
for i, sl in enumerate(objs, start=1):
    area = int((labels[sl] == i).sum())
    if area < 2:
        continue
    cy, cx = ndimage.center_of_mass(mask, labels, i)
    # Colour from the halo around the core (cores are saturated white in the print).
    r = max(3, int(np.sqrt(area)))
    ys, xs = np.ogrid[-cy:photo.shape[0] - cy, -cx:photo.shape[1] - cx]
    d2 = xs ** 2 + ys ** 2
    ring = (d2 <= (2.2 * r) ** 2) & (lum > bg + 15)
    col = chroma(photo[ring].mean(axis=0)) if ring.any() else chroma(photo[labels == i].mean(axis=0))
    # The print desaturates halos (blue ~0.41 vs ~0.65 in the printed B swatch), so matching
    # against the swatches fails. Use a blueness index t = b - r with cuts by perceived colour.
    t = col[2] - col[0]
    cls = ("B" if t >= 0.12 else "A" if t >= 0.04 else "F1" if t >= -0.02 else "F2" if t >= -0.06
           else "G" if t >= -0.09 else "K1" if t >= -0.11 else "K2" if t >= -0.16 else "M")
    glow = int(ring.sum())
    stars.append({"x": cx + X0, "y": cy + Y0, "area_core": area, "area_glow": glow, "clase": cls, "indice_azul": round(float(t), 3),
                  "rgb_norm": [round(float(v), 3) for v in col]})

# Brightness 1..10: rank stars by glow area into the ten size bins of the printed scale,
# with bin edges set geometrically between the largest and smallest detections.
areas = np.array([s["area_glow"] for s in stars], dtype=float)
edges = np.geomspace(areas.max(), max(areas.min(), 1), 11)
for s in stars:
    s["brillo"] = int(min(10, max(1, np.searchsorted(-edges, -s["area_glow"]))))

# Two centre estimates: plain number density (faint field stars weigh as much as members)
# and brightness-weighted density (bright stars are almost all members, as Gaia shows).
dens = np.zeros(lum.shape)
wdens = np.zeros(lum.shape)
for s in stars:
    dens[int(s["y"] - Y0), int(s["x"] - X0)] += 1
    wdens[int(s["y"] - Y0), int(s["x"] - X0)] += 11 - s["brillo"]
smooth = ndimage.gaussian_filter(dens, 35)
ny, nx = np.unravel_index(np.argmax(smooth), smooth.shape)
wsmooth = ndimage.gaussian_filter(wdens, 35)
py, px = np.unravel_index(np.argmax(wsmooth), wsmooth.shape)
print(f"number-density peak=({nx + X0},{ny + Y0})  brightness-weighted peak=({px + X0},{py + Y0})")
# Adopted centre: centroid of the three bright concentrations that form the visual core
# (orange star, bright blue star just below it, blue group lower-left), located by eye on
# pagina2.jpg. Both automatic peaks above fall within ~60 px of it; the brightness-weighted
# one is pulled by spurious detections in the halo of a saturated star.
BRIGHT_CORE = [(379, 552), (407, 581), (325, 647)]
cx, cy = (int(round(np.mean([p[0] for p in BRIGHT_CORE]))), int(round(np.mean([p[1] for p in BRIGHT_CORE]))))
px, py = cx - X0, cy - Y0
field = np.median(smooth)
limit_r = None
for rad in range(10, 400, 5):
    yy, xx = np.ogrid[-py:smooth.shape[0] - py, -px:smooth.shape[1] - px]
    ring = (np.hypot(xx, yy) >= rad - 5) & (np.hypot(xx, yy) < rad)
    if ring.any() and smooth[ring].mean() < 1.3 * field:
        limit_r = rad
        break

HALF = 65  # square of 150 px (~37% of the photo width) centred on the X
# Merge detections lying inside the halo of a brighter star (fragments of one glow),
# and drop levels 9-10, which at this resolution are mostly paper grain.
kept = []
for s in sorted(stars, key=lambda s: -s["area_glow"]):
    if all(np.hypot(s["x"] - k["x"], s["y"] - k["y"]) > 0.6 * np.sqrt(k["area_glow"]) for k in kept):
        kept.append(s)
inside = [s for s in kept if abs(s["x"] - cx) <= HALF and abs(s["y"] - cy) <= HALF and s["brillo"] <= 8]

draw_img = page.copy()
dr = ImageDraw.Draw(draw_img)
if limit_r:
    dr.ellipse([cx - limit_r, cy - limit_r, cx + limit_r, cy + limit_r], outline=(255, 215, 0), width=3)
dr.rectangle([cx - HALF, cy - HALF, cx + HALF, cy + HALF], outline=(0, 255, 0), width=3)
dr.line([cx - 12, cy - 12, cx + 12, cy + 12], fill=(255, 0, 0), width=5)
dr.line([cx - 12, cy + 12, cx + 12, cy - 12], fill=(255, 0, 0), width=5)
for k, s in enumerate(sorted(inside, key=lambda s: s["brillo"]), start=1):
    s["id"] = k
    dr.text((s["x"] + 4, s["y"] - 12), str(k), fill=(255, 255, 0))
draw_img.save(OUT / "pagina2_con_X_y_cuadrado.jpg", quality=95)
draw_img.crop((X0 - 10, Y0 - 70, X1 + 10, Y1 + 10)).resize((800, 916)).save(OUT / "pagina2_cumulo_ampliado.png")

json.dump({"centro_px": [int(cx), int(cy)], "centro_densidad_numerica_px": [int(nx + X0), int(ny + Y0)], "radio_limite_px": limit_r, "lado_cuadrado_px": 2 * HALF,
           "estrellas_detectadas": len(stars), "dentro_del_cuadrado": inside},
          open(OUT / "pagina2_estimaciones.json", "w"), indent=2)
print(f"stars={len(stars)} centre=({cx},{cy}) limit_r={limit_r}px inside={len(inside)}")
for s in sorted(inside, key=lambda s: s["brillo"]):
    print(s["id"], s["clase"], s["brillo"], s["area_glow"], s["indice_azul"])


# ---- Filled worksheet: brightness (1 top .. 10 bottom) vs colour class (O .. M)
import matplotlib.pyplot as plt
import pandas as pd

tab = pd.DataFrame([{"estrella": s["id"], "color_estimado": s["clase"], "brillo_estimado": s["brillo"],
                     "indice_azul": s["indice_azul"], "x_px": round(s["x"]), "y_px": round(s["y"])}
                    for s in sorted(inside, key=lambda s: s["id"])])
tab.to_csv(OUT / "pagina2_tabla_estrellas_cuadrado.csv", index=False)
counts = tab.groupby(["color_estimado", "brillo_estimado"]).size()

fig, ax = plt.subplots(figsize=(7, 7))
for (cls, b), k in counts.items():
    xs = CLASSES.index(cls) + 0.5 + (np.arange(k) % 4 - 1.5) * 0.18
    ys = b - 0.5 + (np.arange(k) // 4 - (k - 1) // 8) * 0.22
    ax.scatter(xs, ys, s=28, color="k")
ax.set_xticks(np.arange(len(CLASSES)) + 0.5, CLASSES)
ax.set_yticks(np.arange(10) + 0.5, range(1, 11))
ax.set_xlim(0, len(CLASSES)); ax.set_ylim(10, 0)
ax.set_xticks(range(len(CLASSES) + 1), minor=True); ax.set_yticks(range(11), minor=True)
ax.grid(which="minor", color="k", lw=1); ax.tick_params(which="minor", length=0)
ax.set_xlabel("Color de la estrella"); ax.set_ylabel("Brillo (tamaño del punto en la imagen)")
ax.set_title(f"Hoja de trabajo – {len(tab)} estrellas dentro del cuadrado")
fig.savefig(OUT / "hoja_de_trabajo_llena.png", dpi=180, bbox_inches="tight")
print(counts.unstack(fill_value=0).to_string())
