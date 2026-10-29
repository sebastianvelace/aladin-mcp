"""Point 5 backup: real Gaia DR3 colour-magnitude diagram of NGC 4755 (Jewel Box).

Queries the ESA Gaia archive directly (independent of CDS). Cluster centre from SIMBAD.
Members selected by parallax and proper motion around the cluster's median values.
Run: .venv/bin/python resultados/scripts/p5_gaia_cmd.py
"""

from pathlib import Path

import aladin_mcp  # noqa: F401  (keeps caches inside the project)
import matplotlib.pyplot as plt
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
# Synchronous jobs are capped at 2000 rows regardless of ROW_LIMIT; use async.
stars = Gaia.launch_job_async(query).get_results().to_pandas()
stars.to_csv(OUT / "NGC4755_GaiaDR3_cono6arcmin.csv", index=False)

# Iterative membership: start from a broad parallax window, then use the medians.
sel = stars["parallax"].between(0.3, 0.7) & (stars["parallax_error"] < 0.1)
for _ in range(3):
    pmra0, pmdec0, plx0 = stars.loc[sel, ["pmra", "pmdec", "parallax"]].median()
    dpm = np.hypot(stars["pmra"] - pmra0, stars["pmdec"] - pmdec0)
    sel = (dpm < 0.5) & ((stars["parallax"] - plx0).abs() < 3 * np.hypot(stars["parallax_error"], 0.03))
members = stars[sel].copy()
members.to_csv(OUT / "NGC4755_GaiaDR3_miembros.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 8))
ax.scatter(stars["bp_rp"], stars["phot_g_mean_mag"], s=4, color="0.75", label=f"field stars in 6' ({len(stars)})")
ax.scatter(members["bp_rp"], members["phot_g_mean_mag"], s=14, c=members["bp_rp"], cmap="coolwarm",
           vmin=0, vmax=2.5, edgecolors="k", linewidths=0.3, label=f"likely members ({len(members)})")
ax.invert_yaxis()
ax.set_xlabel("Gaia colour BP - RP (mag)")
ax.set_ylabel("Gaia apparent magnitude G (mag)")
ax.set_title("NGC 4755 (Jewel Box) - Gaia DR3 colour-magnitude diagram")
ax.legend(loc="lower left", fontsize=8)
ax.grid(alpha=0.3)
fig.savefig(OUT / "NGC4755_GaiaDR3_CMD.png", dpi=130, bbox_inches="tight")

print(f"stars={len(stars)} members={len(members)} pm=({pmra0:.3f},{pmdec0:.3f}) mas/yr plx={plx0:.4f} mas")
print("brightest members:\n", members.nsmallest(12, "phot_g_mean_mag")[["source_id", "phot_g_mean_mag", "bp_rp", "parallax", "ruwe"]].to_string())
print("reddest bright members:\n", members[members.phot_g_mean_mag < 10].nlargest(3, "bp_rp")[["phot_g_mean_mag", "bp_rp"]].to_string())
