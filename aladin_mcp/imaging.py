"""Survey image download (hips2fits, SkyView fallback), PNG rendering and size measurement."""

import re
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import Angle
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.visualization import AsinhStretch, ImageNormalize, PercentileInterval
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from scipy import ndimage

from .cds import resolve_target
from .config import HIPS2FITS_SERVERS, OUTPUT_DIR, SURVEYS, TIMEOUT
from .mirrors import MirrorPool, describe_error

hips2fits_pool = MirrorPool("hips2fits", HIPS2FITS_SERVERS)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def _survey_for(hips: str):
    key = hips.strip().upper()
    if key in SURVEYS:
        return SURVEYS[key]
    for survey in SURVEYS.values():
        if survey.hips_id.lower() == hips.strip().lower():
            return survey
    return None


def _image_data(hdul: fits.HDUList):
    for hdu in hdul:
        if hdu.data is not None and hdu.data.ndim >= 2:
            return hdu
    raise ValueError("The FITS file has no image data.")


def fetch_image(target: str, hips: str, fov_deg: float, width_px: int, height_px: int | None,
                projection: str) -> dict:
    coord, resolved = resolve_target(target)
    survey = _survey_for(hips)
    hips_id = survey.hips_id if survey else hips
    height_px = height_px or width_px
    errors = []
    source = None
    used = hips_id
    hdul = None

    def run(server: str):
        from astroquery.hips2fits import hips2fitsClass
        client = hips2fitsClass()
        client.server = server
        client.timeout = TIMEOUT
        return client.query(hips=hips_id, width=width_px, height=height_px,
                            projection=projection, ra=coord.ra, dec=coord.dec,
                            fov=Angle(fov_deg * u.deg), format="fits")

    try:
        hdul, server = hips2fits_pool.run(run)
        source = f"hips2fits ({server}) HiPS={hips_id}"
    except Exception as exc:
        errors.append(str(exc))

    if hdul is None and survey is not None:
        # SkyView (NASA) serves the same surveys from independent infrastructure.
        try:
            from astroquery.skyview import SkyView
            SkyView.TIMEOUT = max(TIMEOUT, 60)
            images = SkyView.get_images(
                position=f"{coord.ra.deg} {coord.dec.deg}", survey=[survey.skyview],
                coordinates="J2000", projection=projection.capitalize(),
                pixels=f"{width_px},{height_px}", width=fov_deg * u.deg,
                deedger="skyview.process.Deedger",  # match plate backgrounds
                height=fov_deg * height_px / width_px * u.deg)
            hdul = images[0]
            used = survey.skyview
            source = f"NASA SkyView fallback, survey='{used}' (hips2fits failed)"
        except Exception as exc:
            errors.append(f"SkyView: {describe_error(exc)}")

    if hdul is None:
        raise RuntimeError("Could not download the image.\n" + "\n".join(errors))

    out_dir = OUTPUT_DIR / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{_slug(target)}_{_slug(used)}_{fov_deg:g}deg"
    fits_path = base.with_suffix(".fits")
    hdu = _image_data(hdul)
    hdu.header["HISTORY"] = f"aladin-mcp source: {source}"
    fits.HDUList([fits.PrimaryHDU(hdu.data, hdu.header)]).writeto(fits_path, overwrite=True)

    wcs = WCS(hdu.header).celestial
    scale = proj_plane_pixel_scales(wcs).mean() * 3600
    title = f"{target} - {used}" + (f" ({survey.band})" if survey else "")
    png_path = render_png(hdu.data, wcs, title, base.with_suffix(".png"))
    return {
        "fits": str(fits_path), "png": str(png_path), "fuente": source,
        "centro": {"ra_deg": round(coord.ra.deg, 6), "dec_deg": round(coord.dec.deg, 6),
                   "resuelto_por": resolved},
        "fov_deg": fov_deg, "pixeles": list(hdu.data.shape[-2:][::-1]),
        "escala_arcsec_por_pixel": round(float(scale), 3),
        "avisos": errors if errors else None,
    }


def _to_display(data: np.ndarray):
    """Return (image, cmap) ready for imshow: RGB cubes become HxWx3 in [0,1]."""
    if data.ndim == 3 and data.shape[0] == 3:
        planes = []
        for plane in data:
            lo, hi = np.nanpercentile(plane, [0.5, 99.5])
            planes.append(np.clip((plane - lo) / (hi - lo or 1), 0, 1))
        return np.dstack(planes), None
    img = data if data.ndim == 2 else data[0]
    norm = ImageNormalize(img, interval=PercentileInterval(99.5), stretch=AsinhStretch(0.1))
    return norm(np.nan_to_num(img, nan=np.nanmedian(img))), "gray"


def render_png(data, wcs, title, path: Path, contour_mask=None) -> Path:
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(projection=wcs)
    img, cmap = _to_display(data)
    ax.imshow(img, origin="lower", cmap=cmap)
    if contour_mask is not None:
        ax.contour(contour_mask, levels=[0.5], colors="cyan", linewidths=1.2)
    ax.coords[0].set_axislabel("RA (J2000)")
    ax.coords[1].set_axislabel("Dec (J2000)")
    ax.coords.grid(color="white", alpha=0.25, linestyle=":")
    ax.set_title(title, fontsize=10)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


METHOD = (
    "1) Collapse to one plane (mean of R,G,B for colour HiPS). "
    "2) Gaussian smoothing (sigma = suavizado_px) to wash out stars and noise. "
    "3) Background level and noise from 3-sigma-clipped statistics of the whole frame. "
    "4) Threshold = background + umbral x noise. "
    "5) Keep the connected region that contains the image centre (or the largest one). "
    "6) Diameters from that region using the WCS pixel scale: equivalent-circle diameter "
    "2*sqrt(area/pi), and major/minor axes of the ellipse with the same second moments."
)

LIMITATIONS = (
    "Approximate, threshold-dependent estimate: a lower umbral gives a larger diameter. "
    "If the object fills the frame the 'background' includes its own emission and the size is "
    "underestimated: use a FOV 2-3x the expected size. A region touching the edge is only a "
    "lower limit. Low-resolution surveys (Planck ~5', Fermi ~1 deg PSF) blur and enlarge "
    "sources, and in Planck/Fermi the Milky Way foreground can merge with the target. "
    "Different wavelengths trace different components (stars, dust, gas, cosmic rays), so "
    "the 'diameter' is not expected to agree between surveys."
)


def measure_size(fits_path: str, umbral: float, suavizado_px: float | None,
                 distancia_kpc: float | None, return_arrays: bool = False) -> dict:
    """Measure the main emission. With return_arrays=True no PNG is written and the result
    carries the image, chosen region and WCS (keys _data, _region, _wcs) for custom figures."""
    path = Path(fits_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"FITS not found: {path}")
    with fits.open(path) as hdul:
        hdu = _image_data(hdul)
        data = np.asarray(hdu.data, dtype=float)
        header = hdu.header.copy()
    wcs = WCS(header).celestial
    raw = data
    img = np.nanmean(data, axis=0) if data.ndim == 3 else data
    img = np.where(np.isfinite(img), img, np.nanmedian(img))

    sigma_px = suavizado_px if suavizado_px is not None else max(1.0, 0.01 * min(img.shape))
    smooth = ndimage.gaussian_filter(img, sigma_px)
    _, background, noise = sigma_clipped_stats(smooth, sigma=3.0, maxiters=10)
    threshold = background + umbral * noise
    mask = smooth > threshold
    labels, n = ndimage.label(mask)
    if n == 0:
        raise ValueError(f"No pixel above the threshold (umbral={umbral}). Lower umbral.")
    cy, cx = img.shape[0] // 2, img.shape[1] // 2
    chosen = labels[cy, cx]
    how = "region containing the image centre"
    if chosen == 0:
        sizes = ndimage.sum(mask, labels, range(1, n + 1))
        chosen = int(np.argmax(sizes)) + 1
        how = "largest region (the centre was below the threshold)"
    region = labels == chosen

    scale_deg = float(proj_plane_pixel_scales(wcs).mean())
    ys, xs = np.nonzero(region)
    area_px = region.sum()
    eig = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))))[::-1]
    # For a uniform ellipse, variance along an axis = (semi-axis)^2 / 4.
    major_deg = 4 * np.sqrt(eig[0]) * scale_deg
    minor_deg = 4 * np.sqrt(eig[1]) * scale_deg
    equiv_deg = 2 * np.sqrt(area_px / np.pi) * scale_deg
    touches = bool(region[0].any() or region[-1].any() or region[:, 0].any() or region[:, -1].any())

    warnings_ = []
    history = " ".join(str(h) for h in header.get("HISTORY", []))
    if "SkyView" in history and "DSS" in history:
        warnings_.append("Image comes from the SkyView DSS mosaic, whose photographic plates have "
                         "unmatched backgrounds: the threshold can follow a plate edge instead of "
                         "the object. Check the diagnostic PNG; prefer the CDS HiPS (hips2fits).")
    if touches:
        warnings_.append("The region touches the image edge: the diameter is a LOWER LIMIT. "
                         "Download with a larger fov_grados.")
    if area_px / region.size > 0.6:
        warnings_.append("The region covers >60% of the frame; the background estimate is "
                         "probably contaminated. Use a larger FOV.")
    if how.startswith("largest"):
        warnings_.append("The image centre is below the threshold, so the largest region was "
                         "used: it may be a different source. Check the diagnostic PNG.")

    png = None
    if not return_arrays:
        png = path.with_name(path.stem + f"_medida_u{umbral:g}.png")
        render_png(raw, wcs, f"{path.stem}: threshold = bkg + {umbral:g} sigma", png, region)

    result = {
        "diametro_equivalente_deg": round(float(equiv_deg), 3),
        "diametro_equivalente_arcmin": round(float(equiv_deg * 60), 1),
        "eje_mayor_deg": round(float(major_deg), 3),
        "eje_menor_deg": round(float(minor_deg), 3),
        "region_elegida": how,
        "fraccion_de_la_imagen": round(float(area_px / region.size), 3),
        "toca_el_borde": touches,
        "fondo": float(background), "ruido": float(noise), "umbral_valor": float(threshold),
        "suavizado_px": sigma_px,
        "escala_arcsec_por_pixel": round(scale_deg * 3600, 3),
        "png_diagnostico": str(png) if png else None,
        "avisos": warnings_ or None,
        "metodo": METHOD,
        "limitaciones": LIMITATIONS,
    }
    if distancia_kpc:
        result["diametro_fisico_kpc"] = round(float(distancia_kpc * np.radians(equiv_deg)), 2)
    if return_arrays:
        result.update({"_data": raw, "_region": region, "_wcs": wcs})
    return result
