"""Point 4(a), "manual" check: measure the LMC and 30 Doradus along their axes with brightness
profiles, the way one measures with Aladin's ruler, independently of measure_angular_size.

For each image: take a strip along the major axis and one along the minor axis, compute the
median brightness across the strip (so single stars do not count) with no 2-D smoothing, and
put each edge where the profile falls to the local sky plus 10 % of the peak-to-sky contrast
(5 % and 20 % are reported as the sensitivity). Done by Claude, not by a person.
Run: .venv/bin/python resultados/scripts/p4_medidas_perfiles.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from figuras_es import save  # noqa: E402

R = Path(__file__).resolve().parents[2] / "resultados" / "punto4"
LMC = (80.894167, -69.756111)        # SIMBAD centre of the LMC
DOR30 = (84.65, -69.086389)          # SIMBAD centre of the 30 Dor nebula

# key, label, file, centre, half-length of the ruler (deg), strip width (deg), unit factor,
# longest internal dip skipped (deg)
TARGETS = [
    ("optico", "Óptico (Mellinger)", "LMC_optico_Mellinger_luminancia_20deg.fits", LMC, 9.5, 0.6, 1, 0.5),
    ("akari", "Infrarrojo (AKARI 140 µm)", "LMC_infrarrojo_AKARI140um_20deg.fits", LMC, 9.5, 0.6, 1, 0.5),
    ("planck857", "Submilimétrico (Planck 857 GHz)", "LMC_radio_Planck857GHz_20deg.fits", LMC, 9.5, 0.6, 1, 0.5),
    ("planck030", "Radio (Planck 30 GHz)", "LMC_radio_Planck030GHz_20deg.fits", LMC, 9.5, 0.6, 1, 0.5),
    ("fermi", "Rayos gamma (Fermi 3–300 GeV, mapa crudo)", "LMC_gamma_Fermi3-300GeV_20deg.fits", LMC, 9.5, 1.0, 1, 0.5),
    ("30dor", "30 Doradus (DSS2 roja)", "30Dor_optico_DSS2red_1.5deg.fits", DOR30, 0.7, 0.05, 60, 2 / 60),
]


def axis_angle(data, cx, cy, radius_px, bkg, sd):
    """Position angle (radians, in pixel space) of the major axis from intensity moments."""
    img = ndimage.median_filter(data, size=3)
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    w = np.where((np.hypot(xx - cx, yy - cy) < radius_px) & (img > bkg + 2 * sd), img - bkg, 0.0)
    mx, my = (w * xx).sum() / w.sum(), (w * yy).sum() / w.sum()
    cov = np.cov(np.vstack([(xx - mx).ravel(), (yy - my).ravel()]), aweights=w.ravel())
    vals, vecs = np.linalg.eigh(cov)
    major = vecs[:, np.argmax(vals)]
    return float(np.arctan2(major[1], major[0]))


def profile(data, cx, cy, angle, half_px, width_px):
    """Median brightness across a strip, sampled every pixel along the given direction."""
    t = np.arange(-half_px, half_px + 1)
    s = np.arange(-(width_px // 2), width_px // 2 + 1)
    dx, dy = np.cos(angle), np.sin(angle)
    px, py = -dy, dx  # perpendicular
    xs = cx + t[:, None] * dx + s[None, :] * px
    ys = cy + t[:, None] * dy + s[None, :] * py
    vals = ndimage.map_coordinates(data, [ys, xs], order=1, mode="nearest")
    return t, np.median(vals, axis=1)


CONTRASTS = (0.05, 0.10, 0.20)  # decided before looking at the results; 0.10 is the main one


def edges(t, prof, gap_px, contrast):
    """Edge on each side where the profile falls to that side's sky + contrast x (peak - sky).

    Fixed-contrast criterion, like an eye looking at a screen with a fixed stretch. Each side
    uses its own neighbouring sky (median of its outer 20 %) because the Milky Way adds
    gradients, and internal dips shorter than gap_px are skipped. Returns
    (left, right, skies, levels, detected); not detected when the peak is not 5 noise units
    above the sky (e.g. the raw Fermi photon map) or an edge does not close inside the ruler."""
    smooth = ndimage.median_filter(prof, size=5)
    centre = int(np.argmin(np.abs(t)))
    core = np.abs(t) < 0.5 * t.max()
    peak = smooth[core].max()
    out = {}
    for side, idx in (("left", range(centre, -1, -1)), ("right", range(centre, len(t)))):
        outer = (t < -0.8 * t.max()) if side == "left" else (t > 0.8 * t.max())
        sky = np.median(prof[outer])
        noise = 1.4826 * np.median(np.abs(prof[outer] - sky))
        level = sky + contrast * (peak - sky)
        last_above, below_run = centre, 0
        for i in idx:
            if smooth[i] > level:
                last_above, below_run = i, 0
            else:
                below_run += 1
                if below_run > gap_px:
                    break
        significant = noise > 0 and (peak - sky) > 5 * noise
        out[side] = (last_above, sky, level, significant, below_run > gap_px)
    (lo, sky_l, lev_l, ok_l, closed_l), (hi, sky_r, lev_r, ok_r, closed_r) = out["left"], out["right"]
    detected = ok_l and ok_r and closed_l and closed_r
    return t[lo], t[hi], (sky_l, sky_r), (lev_l, lev_r), detected


rows = []
fig_all, axes_all = plt.subplots(len(TARGETS), 2, figsize=(11, 3.0 * len(TARGETS)))
for row_axes, (key, label, name, centre, half_deg, width_deg, factor, gap_deg) in zip(axes_all, TARGETS):
    hdu = fits.open(R / name)[0]
    data = np.nan_to_num(np.asarray(hdu.data, dtype=float))
    wcs = WCS(hdu.header).celestial
    scale = float(proj_plane_pixel_scales(wcs).mean())
    cx, cy = wcs.world_to_pixel_values(*centre)
    _, bkg, sd = sigma_clipped_stats(data, sigma=3, maxiters=10)
    angle = axis_angle(data, cx, cy, 0.5 * half_deg / scale, bkg, sd)
    result = {"clave": key, "banda": label, "unidad": "arcmin" if factor == 60 else "grados"}
    for ax, (axis_name, a) in zip(row_axes, [("mayor", angle), ("menor", angle + np.pi / 2)]):
        t, prof = profile(data, cx, cy, a, int(half_deg / scale), max(1, int(width_deg / scale)))
        for c in CONTRASTS:  # sensitivity to the chosen contrast
            lo_c, hi_c, _, _, det_c = edges(t, prof, int(gap_deg / scale), c)
            result[f"eje_{axis_name}_contraste{int(c * 100)}"] = (
                round(float((hi_c - lo_c) * scale * factor), 2) if det_c else None)
        lo, hi, skies, levels, detected = edges(t, prof, int(gap_deg / scale), 0.10)
        length = (hi - lo) * scale * factor
        p1 = wcs.pixel_to_world_values(cx + lo * np.cos(a), cy + lo * np.sin(a))
        p2 = wcs.pixel_to_world_values(cx + hi * np.cos(a), cy + hi * np.sin(a))
        result[f"eje_{axis_name}"] = round(float(length), 2) if detected else None
        result[f"extremos_{axis_name}"] = [[round(float(v), 5) for v in p1], [round(float(v), 5) for v in p2]]
        ax.plot(t * scale * factor, prof, lw=0.8, color="0.25")
        x_unit = scale * factor
        for (x0, x1), sky, level, first in [((t[0], 0), skies[0], levels[0], True), ((0, t[-1]), skies[1], levels[1], False)]:
            ax.hlines(sky, x0 * x_unit, x1 * x_unit, color="tab:blue", ls=":", lw=1, label="cielo local" if first else None)
            ax.hlines(level, x0 * x_unit, x1 * x_unit, color="tab:red", ls="--", lw=1,
                      label="cielo + 10 % del contraste" if first else None)
        if detected:
            for edge in (lo, hi):
                ax.axvline(edge * scale * factor, color="tab:green", lw=1.2)
        unit = "′" if factor == 60 else "°"
        direction = "dirección de momentos" if axis_name == "mayor" else "dirección perpendicular"
        ax.set_title(f"{label} – {direction}: " + (f"{length:.2f}{unit}" if detected else "sin borde claro"),
                     fontsize=9)
        ax.set_xlabel(f"Distancia al centro ({unit})", fontsize=8)
        ax.set_ylabel("Brillo (mediana de la franja)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, loc="upper right")
    a, b = result["eje_mayor"], result["eje_menor"]
    if a is not None and b is not None and b > a:  # moments chose the shorter direction
        for k in [k for k in result if k.startswith("eje_mayor")]:
            kk = k.replace("mayor", "menor")
            result[k], result[kk] = result[kk], result[k]
        result["extremos_mayor"], result["extremos_menor"] = result["extremos_menor"], result["extremos_mayor"]
        result["nota"] = "major/minor swapped: the profile across the moment axis was longer"
    rows.append(result)

fig_all.suptitle("Medida tipo regla: perfiles de brillo en dos direcciones perpendiculares (bordes en verde)", y=1.0)
fig_all.tight_layout()
save(fig_all, R / "medidas_perfiles.png")
json.dump(rows, open(R / "medidas_perfiles.json", "w"), indent=2, ensure_ascii=False)
for r in rows:
    print(f"{r['clave']:10s} mayor={r['eje_mayor']} [5%: {r['eje_mayor_contraste5']}, 20%: {r['eje_mayor_contraste20']}]"
          f"  menor={r['eje_menor']} [5%: {r['eje_menor_contraste5']}, 20%: {r['eje_menor_contraste20']}]  ({r['unidad']})")
