import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS


def make_wcs(size: int, scale_deg: float, ra: float = 80.0, dec: float = -69.0) -> WCS:
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [size / 2 + 0.5, size / 2 + 0.5]
    w.wcs.cdelt = [-scale_deg, scale_deg]
    return w


@pytest.fixture
def disk_fits(tmp_path):
    """Noise image (sigma 1) with a uniform disk of known radius at the centre."""

    def build(radius_px: float, size: int = 200, scale_deg: float = 0.05, offset=(0, 0), extra=None):
        rng = np.random.default_rng(0)
        data = rng.normal(0.0, 1.0, (size, size))
        yy, xx = np.mgrid[:size, :size]
        cy, cx = size / 2 + offset[0], size / 2 + offset[1]
        data[np.hypot(xx - cx, yy - cy) <= radius_px] += 50.0
        if extra:  # (y, x, radius) of a second source
            ey, ex, er = extra
            data[np.hypot(xx - ex, yy - ey) <= er] += 50.0
        path = tmp_path / "disk.fits"
        fits.PrimaryHDU(data, make_wcs(size, scale_deg).to_header()).writeto(path)
        return path

    return build
