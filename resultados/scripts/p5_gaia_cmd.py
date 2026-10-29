"""Point 5 backup: real Gaia DR3 colour-magnitude diagram of NGC 4755 (Jewel Box).

Queries the ESA Gaia archive directly (independent of CDS). Cluster centre from SIMBAD.
Members selected by parallax and proper motion around the cluster's median values.
Run: .venv/bin/python resultados/scripts/p5_gaia_cmd.py
"""

from pathlib import Path

import aladin_mcp  # noqa: F401  (keeps caches inside the project)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from astroquery.gaia import Gaia

OUT = Path(__file__).resolve().parents[2] / "resultados" / "punto5"
RA, DEC, RADIUS_DEG = 193.415, -60.371111, 0.1  # SIMBAD centre, 6 arcmin radius

query = f"""
SELECT source_id, ra, dec, parallax, parallax_error, pmra, pmdec,
       phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, bp_rp, ruwe
FROM gaiadr3.gaia_source
WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {RA}, {DEC}, {RADIUS_DEG}))
  AND phot_g_mean_mag < 18 AND bp_rp IS NOT NULL AND parallax IS NOT NULL
"""
import pandas as pd  # noqa: E402

CONE = OUT / "NGC4755_GaiaDR3_cono6arcmin.csv"
if CONE.exists():  # reuse the saved query so the figure is reproducible
    stars = pd.read_csv(CONE)
else:
    # Synchronous jobs are capped at 2000 rows regardless of ROW_LIMIT; use async.
    stars = Gaia.launch_job_async(query).get_results().to_pandas()
    stars.to_csv(CONE, index=False)

# Iterative membership: start from a broad parallax window, then use the medians.
sel = stars["parallax"].between(0.3, 0.7) & (stars["parallax_error"] < 0.1)
for _ in range(3):
    pmra0, pmdec0, plx0 = stars.loc[sel, ["pmra", "pmdec", "parallax"]].median()
    dpm = np.hypot(stars["pmra"] - pmra0, stars["pmdec"] - pmdec0)
    sel = (dpm < 0.5) & ((stars["parallax"] - plx0).abs() < 3 * np.hypot(stars["parallax_error"], 0.03))
members = stars[sel].copy()
members.to_csv(OUT / "NGC4755_GaiaDR3_miembros.csv", index=False)

fig, ax = plt.subplots(figsize=(7.5, 8.5))
ax.scatter(stars["bp_rp"], stars["phot_g_mean_mag"], s=4, color="0.75", label=f"Estrellas de campo en 6′ ({len(stars)})")
ax.scatter(members["bp_rp"], members["phot_g_mean_mag"], s=14, c=members["bp_rp"], cmap="coolwarm",
           vmin=0, vmax=2.5, edgecolors="k", linewidths=0.3, label=f"Miembros probables ({len(members)})")
ax.invert_yaxis()
# Turn-off: the brightest blue members are redder than the main sequence below them.
ax.add_patch(Rectangle((0.28, 5.3), 0.36, 2.8, fill=False, ec="darkgreen", lw=1.8, ls="--"))
ax.annotate("Punto de giro: supergigantes B\nque ya salen de la secuencia principal\n(BP−RP 0.35–0.57 frente a ≈ 0.23 más abajo)",
            xy=(0.64, 6.3), xytext=(1.05, 7.6), fontsize=8.5, color="darkgreen",
            arrowprops={"arrowstyle": "->", "color": "darkgreen"})
dru = members.loc[members["bp_rp"] > 2].nsmallest(1, "phot_g_mean_mag")
ax.annotate("Supergigante roja (DU Cru, M2 Iab)", xy=(dru["bp_rp"].iloc[0], dru["phot_g_mean_mag"].iloc[0]),
            xytext=(2.1, 8.6), fontsize=8.5, color="firebrick", arrowprops={"arrowstyle": "->", "color": "firebrick"})
ax.annotate("Secuencia principal", xy=(0.25, 10.5), xytext=(0.9, 11.2), fontsize=8.5,
            arrowprops={"arrowstyle": "->"})
ax.set_xlabel("Índice de color de Gaia BP − RP (mag)")
ax.set_ylabel("Magnitud aparente de Gaia G (mag)")
ax.set_title("NGC 4755 (Caja de Joyas) – diagrama color-magnitud con Gaia DR3")
ax.legend(loc="lower left", fontsize=8)
ax.grid(alpha=0.3)
fig.savefig(OUT / "NGC4755_GaiaDR3_CMD.png", dpi=180, bbox_inches="tight")

print(f"stars={len(stars)} members={len(members)} pm=({pmra0:.3f},{pmdec0:.3f}) mas/yr plx={plx0:.4f} mas")
print("brightest members:\n", members.nsmallest(12, "phot_g_mean_mag")[["source_id", "phot_g_mean_mag", "bp_rp", "parallax", "ruwe"]].to_string())
print("reddest bright members:\n", members[members.phot_g_mean_mag < 10].nlargest(3, "bp_rp")[["phot_g_mean_mag", "bp_rp"]].to_string())
