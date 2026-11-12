"""Detect and track sunspot groups on daily SDO/HMI continuum images and estimate the solar rotation period.

Usage: python track_sunspots.py <sdo_dir> <out_dir>
"""
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import get_body, GeocentricTrueEcliptic
from astropy.time import Time
from PIL import Image
from scipy import ndimage

SDO_DIR = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

LIMB_FRACTION = 0.92      # ignore spots too close to the limb (strong foreshortening)
DARK_FACTOR = 0.82        # pixel darker than 82 % of the local quiet-Sun level
MIN_PIXELS = 4
GROUP_DILATION = 9        # px; merges umbrae of one group
MAX_DLON = 7.0            # deg; linking tolerance after predicting the motion
MAX_DLAT = 3.0
SYNODIC_GUESS = 13.2      # deg/day, only used to predict the next position


def solar_b0_deg(t: Time) -> float:
    """Heliographic latitude of the disk centre (Meeus, Astronomical Algorithms, ch. 29)."""
    jd = t.jd
    k = math.radians(73.6667 + 1.3958333 * (jd - 2396758.0) / 36525.0)
    i = math.radians(7.25)
    sun = get_body("sun", t).transform_to(GeocentricTrueEcliptic(equinox=t))
    lam = sun.lon.rad
    return math.degrees(math.asin(math.sin(lam - k) * math.sin(i)))


def earth_orbital_rate_deg_per_day(t: Time) -> float:
    a = get_body("sun", t - 0.5).transform_to(GeocentricTrueEcliptic(equinox=t)).lon.deg
    b = get_body("sun", t + 0.5).transform_to(GeocentricTrueEcliptic(equinox=t)).lon.deg
    return (b - a) % 360.0


def find_disk(img: np.ndarray):
    mask = img > 0.25 * np.percentile(img, 99)
    mask = ndimage.binary_fill_holes(mask)
    lab, n = ndimage.label(mask)
    largest = 1 + int(np.argmax(ndimage.sum(mask, lab, range(1, n + 1))))
    disk = lab == largest
    cy, cx = ndimage.center_of_mass(disk)
    radius = math.sqrt(disk.sum() / math.pi)
    return cx, cy, radius


def detect_groups(img: np.ndarray, cx: float, cy: float, r: float):
    yy, xx = np.indices(img.shape)
    rho = np.hypot(xx - cx, yy - cy) / r
    inner = rho < LIMB_FRACTION
    background = ndimage.median_filter(img, size=41)
    dark = inner & (img < DARK_FACTOR * background)
    dark = ndimage.binary_opening(dark, iterations=1) | (inner & (img < 0.6 * background))
    lab, n = ndimage.label(dark)
    sizes = ndimage.sum(dark, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.flatnonzero(sizes >= MIN_PIXELS))
    grouped, ng = ndimage.label(ndimage.binary_dilation(keep, iterations=GROUP_DILATION))
    groups = []
    for g in range(1, ng + 1):
        member = keep & (grouped == g)
        weight = np.where(member, background - img, 0.0)
        y, x = ndimage.center_of_mass(weight)
        groups.append({"x": x, "y": y, "area_px": int(member.sum())})
    return groups


def to_heliographic(x: float, y: float, cx: float, cy: float, r: float, b0: float):
    """Orthographic projection; image north is up (Helioviewer images are rotated so P = 0)."""
    xs, ys = (x - cx) / r, (cy - y) / r
    zs = math.sqrt(max(0.0, 1 - xs * xs - ys * ys))
    b0r = math.radians(b0)
    lat = math.asin(ys * math.cos(b0r) + zs * math.sin(b0r))
    lon = math.atan2(xs, zs * math.cos(b0r) - ys * math.sin(b0r))
    return math.degrees(lat), math.degrees(lon)


meta = json.loads((SDO_DIR / "metadata.json").read_text())
t0 = Time(meta[0]["obs_date"].replace(" ", "T"))
detections = []
for frame, item in enumerate(meta):
    t = Time(item["obs_date"].replace(" ", "T"))
    img = np.asarray(Image.open(SDO_DIR / item["file"]).convert("L"), dtype=float)
    cx, cy, r = find_disk(img)
    b0 = solar_b0_deg(t)
    for g in detect_groups(img, cx, cy, r):
        lat, lon = to_heliographic(g["x"], g["y"], cx, cy, r, b0)
        detections.append({
            "frame": frame, "file": item["file"], "date": item["obs_date"], "t_days": (t - t0).to_value("day"),
            "x": g["x"], "y": g["y"], "area_px": g["area_px"], "lat": lat, "lon_cm": lon,
            "disk_cx": cx, "disk_cy": cy, "disk_r": r, "b0": b0,
        })

# --- link detections into tracks (nearest neighbour with predicted rotation) ---
tracks = []
open_tracks = []
for frame in range(len(meta)):
    current = [d for d in detections if d["frame"] == frame]
    used = set()
    still_open = []
    for tr in open_tracks:
        last = tr[-1]
        dt = current[0]["t_days"] - last["t_days"] if current else 0
        best, best_cost = None, None
        for i, d in enumerate(current):
            if i in used:
                continue
            dlon = d["lon_cm"] - (last["lon_cm"] + SYNODIC_GUESS * dt)
            dlat = d["lat"] - last["lat"]
            if abs(dlon) < MAX_DLON * max(dt, 1) ** 0.5 and abs(dlat) < MAX_DLAT:
                cost = dlon ** 2 + 4 * dlat ** 2
                if best_cost is None or cost < best_cost:
                    best, best_cost = i, cost
        if best is not None:
            used.add(best)
            tr.append(current[best])
            still_open.append(tr)
        elif frame - tr[-1]["frame"] < 2:     # allow one missed frame
            still_open.append(tr)
        else:
            tracks.append(tr)
    for i, d in enumerate(current):
        if i not in used:
            still_open.append([d])
    open_tracks = still_open
tracks += open_tracks

# --- fit each long track ---
omega_earth = earth_orbital_rate_deg_per_day(Time("2014-12-08T00:00:00"))
results = []
good = sorted([tr for tr in tracks if len(tr) >= 5], key=lambda tr: tr[0]["t_days"])
for k, tr in enumerate(good, start=1):
    t = np.array([d["t_days"] for d in tr])
    lon = np.array([d["lon_cm"] for d in tr])
    lat = np.array([d["lat"] for d in tr])
    (slope, icpt), cov = np.polyfit(t, lon, 1, cov=True)
    sig = math.sqrt(cov[0, 0])
    syn_period = 360.0 / slope
    sid_rate = slope + omega_earth
    results.append({
        "track": k, "n_days": len(tr), "first_date": tr[0]["date"][:10], "last_date": tr[-1]["date"][:10],
        "mean_lat": float(lat.mean()), "lon_first": float(lon[0]), "lon_last": float(lon[-1]),
        "synodic_rate": float(slope), "synodic_rate_err": sig,
        "synodic_period": syn_period, "synodic_period_err": 360.0 * sig / slope ** 2,
        "sidereal_rate": sid_rate, "sidereal_period": 360.0 / sid_rate,
        "rms_resid_deg": float(np.std(lon - (slope * t + icpt))),
    })
    for d in tr:
        d["track"] = k

with open(OUT / "detecciones.csv", "w", newline="") as fh:
    keys = ["frame", "file", "date", "t_days", "track", "x", "y", "area_px", "lat", "lon_cm", "b0", "disk_cx", "disk_cy", "disk_r"]
    w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    for d in detections:
        w.writerow({**{k: d.get(k, "") for k in keys}})

with open(OUT / "periodos_por_grupo.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
    w.writeheader()
    w.writerows(results)

# --- weighted average and differential rotation fit ---
rates = np.array([r["synodic_rate"] for r in results])
errs = np.array([max(r["synodic_rate_err"], 0.05) for r in results])
lats = np.array([r["mean_lat"] for r in results])
wts = 1 / errs ** 2
mean_syn = float(np.sum(wts * rates) / np.sum(wts))
mean_syn_err = float(1 / math.sqrt(np.sum(wts)))
scatter = float(np.std(rates, ddof=1))
A = np.vstack([np.ones_like(lats), np.sin(np.radians(lats)) ** 2]).T
coef, *_ = np.linalg.lstsq(A * np.sqrt(wts)[:, None], (rates + omega_earth) * np.sqrt(wts), rcond=None)
summary = {
    "n_images": len(meta), "n_detections": len(detections), "n_tracks_used": len(results),
    "earth_orbital_rate_deg_day": omega_earth,
    "mean_synodic_rate": mean_syn, "mean_synodic_rate_err": mean_syn_err, "synodic_rate_scatter": scatter,
    "mean_synodic_period": 360 / mean_syn,
    "mean_synodic_period_err_stat": 360 * mean_syn_err / mean_syn ** 2,
    "mean_synodic_period_err_scatter": 360 * scatter / mean_syn ** 2 / math.sqrt(len(results)),
    "mean_sidereal_rate": mean_syn + omega_earth, "mean_sidereal_period": 360 / (mean_syn + omega_earth),
    "diffrot_A_sidereal": float(coef[0]), "diffrot_B_sidereal": float(coef[1]),
    "equator_sidereal_period_fit": 360 / float(coef[0]),
    "b0_range": [min(d["b0"] for d in detections), max(d["b0"] for d in detections)],
}
(OUT / "resumen.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
for r in results:
    print(f"G{r['track']:>2} {r['first_date']}..{r['last_date']} n={r['n_days']:2d} lat={r['mean_lat']:+6.1f} "
          f"w_syn={r['synodic_rate']:6.2f}±{r['synodic_rate_err']:.2f} T_syn={r['synodic_period']:5.1f} T_sid={r['sidereal_period']:5.1f}")

# --- figures ---
cmap = plt.get_cmap("tab20")
fig, ax = plt.subplots(figsize=(9, 5.5))
for r in results:
    pts = [d for d in detections if d.get("track") == r["track"]]
    t = [d["t_days"] for d in pts]
    ax.plot(t, [d["lon_cm"] for d in pts], "o", color=cmap(r["track"] % 20), ms=4)
    tt = np.array([t[0], t[-1]])
    ax.plot(tt, r["synodic_rate"] * tt + (pts[0]["lon_cm"] - r["synodic_rate"] * t[0]), "-", color=cmap(r["track"] % 20),
            label=f"G{r['track']} ({r['mean_lat']:+.0f}°): {r['synodic_period']:.1f} d")
ax.set_xlabel("Días desde el 25 nov 2014, 12 UT")
ax.set_ylabel("Longitud respecto al meridiano central (°)")
ax.set_title("Desplazamiento de los grupos de manchas (SDO/HMI)")
ax.axhline(0, color="0.6", lw=0.8)
ax.legend(fontsize=7, ncol=2, loc="lower right")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "longitud_vs_tiempo.png", dpi=160)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.errorbar(lats, rates + omega_earth, yerr=errs, fmt="o", label="Grupos medidos (sideral)")
bb = np.linspace(-35, 35, 200)
sb2 = np.sin(np.radians(bb)) ** 2
ax.plot(bb, coef[0] + coef[1] * sb2, label=f"Ajuste: {coef[0]:.2f} {coef[1]:+.2f} sin²b °/día")
ax.plot(bb, 14.71 - 2.39 * sb2, "--", label="Snodgrass & Ulrich (1990): 14.71 − 2.39 sin²b")
ax.set_xlabel("Latitud heliográfica b (°)")
ax.set_ylabel("Velocidad angular sideral (°/día)")
ax.set_title("Rotación diferencial")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "rotacion_diferencial.png", dpi=160)

# montage: every third day with tracked groups labelled
frames = list(range(0, len(meta), 3))[:9]
fig, axes = plt.subplots(3, 3, figsize=(10.5, 10.5))
for ax, f in zip(axes.flat, frames):
    img = np.asarray(Image.open(SDO_DIR / meta[f]["file"]).convert("L"))
    ax.imshow(img, cmap="gray", vmin=0, vmax=255)
    for d in detections:
        if d["frame"] == f and d.get("track"):
            ax.text(d["x"], d["y"] - 22, f"G{d['track']}", color="yellow", fontsize=8, ha="center")
            ax.plot(d["x"], d["y"], "+", color="red", ms=6)
    ax.set_title(meta[f]["obs_date"][:10], fontsize=9)
    ax.axis("off")
fig.suptitle("SDO/HMI continuo: los grupos avanzan de este (izq.) a oeste (der.)")
fig.tight_layout()
fig.savefig(OUT / "mosaico_seguimiento.png", dpi=120)
