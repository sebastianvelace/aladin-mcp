"""Shared helpers for the Spanish-labelled figures in resultados/."""

import aladin_mcp  # noqa: F401  (keeps caches inside the project)
import matplotlib.pyplot as plt
import numpy as np
from astropy.visualization import AsinhStretch, ImageNormalize, PercentileInterval

DPI = 180


def sky_axes(fig, wcs, position=111):
    ax = fig.add_subplot(position, projection=wcs)
    ax.coords[0].set_axislabel("Ascensión recta (J2000)")
    ax.coords[1].set_axislabel("Declinación (J2000)")
    ax.coords.grid(color="white", alpha=0.25, linestyle=":")
    return ax


def show(ax, data, cmap="gray"):
    img = np.nanmean(data, axis=0) if data.ndim == 3 else data
    img = np.nan_to_num(img, nan=np.nanmedian(img))
    norm = ImageNormalize(img, interval=PercentileInterval(99.5), stretch=AsinhStretch(0.1))
    ax.imshow(img, origin="lower", cmap=cmap, norm=norm)


def save(fig, path):
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
