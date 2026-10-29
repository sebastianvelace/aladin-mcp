"""Point 4 corrections: download Mellinger RGB, Fermi 1-4 and Planck 030 GHz around the LMC.

All from NASA SkyView (the CDS hips2fits service was unreachable on 2026-10-29).
Run: .venv/bin/python resultados/scripts/p4_descargas_extra.py
"""

from pathlib import Path

import aladin_mcp  # noqa: F401  (keeps caches inside the project)
import astropy.units as u
import numpy as np
from astropy.io import fits
from astroquery.skyview import SkyView

OUT = Path(__file__).resolve().parents[2] / "resultados" / "punto4"
POS = "80.894167 -69.756111"  # SIMBAD centre of the LMC
FOV = 20 * u.deg
SkyView.TIMEOUT = 180


def get(survey: str, pixels: int = 600) -> fits.PrimaryHDU:
    hdul = SkyView.get_images(position=POS, survey=[survey], coordinates="J2000", projection="Tan",
                              pixels=f"{pixels},{pixels}", width=FOV, height=FOV)[0]
    hdu = hdul[0]
    hdu.header["HISTORY"] = f"aladin-mcp source: NASA SkyView survey='{survey}'"
    return hdu


def save(hdu: fits.PrimaryHDU, name: str) -> None:
    # Some SkyView headers (Mellinger) carry a tab in a COMMENT card, which is not valid FITS
    # and astropy cannot fix. Rewrite commentary cards with non-printable characters as spaces.
    header = fits.Header()
    for card in hdu.header.cards:
        if card.keyword in ("COMMENT", "HISTORY", ""):
            text = "".join(c if 32 <= ord(c) < 127 else " " for c in str(card.value))
            header.add_comment(text) if card.keyword == "COMMENT" else header.add_history(text)
        else:
            header.append(card)
    fits.PrimaryHDU(hdu.data, header).writeto(OUT / name, overwrite=True)


# Mellinger all-sky optical mosaic: one FITS per channel, plus a luminance image to measure.
channels = {}
for colour in ("Red", "Green", "Blue"):
    hdu = get(f"Mellinger {colour}")
    save(hdu, f"LMC_optico_Mellinger{colour}_20deg.fits")
    channels[colour] = hdu
lum = np.mean([channels[c].data.astype(float) for c in ("Red", "Green", "Blue")], axis=0)
hdr = channels["Red"].header.copy()
hdr["HISTORY"] = "Luminance = mean of Mellinger Red, Green and Blue"
save(fits.PrimaryHDU(lum.astype(np.float32), hdr), "LMC_optico_Mellinger_luminancia_20deg.fits")
print("Mellinger ok", flush=True)

for band in (1, 2, 3, 4):
    save(get(f"Fermi {band}", 400), f"LMC_gamma_Fermi{band}_20deg.fits")
    print(f"Fermi {band} ok", flush=True)

save(get("Planck 030 I", 400), "LMC_radio_Planck030GHz_20deg.fits")
print("Planck 030 ok", flush=True)
