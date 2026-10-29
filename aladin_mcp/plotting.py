"""Colour-magnitude diagrams."""

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import OUTPUT_DIR


def _column(df: pd.DataFrame, spec: str) -> tuple[pd.Series, str]:
    """A column name, or 'A-B' meaning the difference of two columns (e.g. 'Bmag-Vmag')."""
    if spec in df.columns:
        return pd.to_numeric(df[spec], errors="coerce"), spec
    if "-" in spec:
        left, right = (s.strip() for s in spec.split("-", 1))
        if left in df.columns and right in df.columns:
            return (pd.to_numeric(df[left], errors="coerce") -
                    pd.to_numeric(df[right], errors="coerce")), f"{left} - {right}"
    raise KeyError(f"Column '{spec}' not in the CSV. Available columns: {list(df.columns)}")


def plot_cmd(csv: str, col_mag: str, col_color: str, title: str, output: str | None) -> dict:
    path = Path(csv).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    mag, mag_label = _column(df, col_mag)
    color, color_label = _column(df, col_color)
    ok = mag.notna() & color.notna()
    if ok.sum() == 0:
        raise ValueError("No row has both values; check the column names.")

    fig, ax = plt.subplots(figsize=(6, 7))
    ax.scatter(color[ok], mag[ok], s=8, c=color[ok], cmap="coolwarm", edgecolors="none")
    ax.invert_yaxis()  # brighter stars (smaller magnitude) at the top
    ax.set_xlabel(f"Colour index {color_label}")
    ax.set_ylabel(f"Apparent magnitude {mag_label}")
    ax.set_title(f"{title}  (N = {int(ok.sum())})")
    ax.grid(alpha=0.3)

    out = Path(output).expanduser() if output else \
        OUTPUT_DIR / "plots" / (re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_") + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return {
        "png": str(out),
        "puntos_graficados": int(ok.sum()),
        "filas_descartadas_sin_dato": int((~ok).sum()),
        "rango_magnitud": [round(float(mag[ok].min()), 3), round(float(mag[ok].max()), 3)],
        "rango_color": [round(float(color[ok].min()), 3), round(float(color[ok].max()), 3)],
    }
