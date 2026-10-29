"""Point 5: write the worksheet estimates onto the photo of page 2, like filling it by hand.

The grid corners were located on pagina2.jpg; cell centres follow a bilinear map between
them because the phone photo is slightly skewed. Dots are blue so the faint grey marks
already on the printed sheet stay distinguishable.
Run: .venv/bin/python resultados/scripts/p5_hoja_sobre_foto.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "resultados" / "punto5"
CLASSES = ["O", "B", "A", "F1", "F2", "G", "K1", "K2", "M"]
# Grid corners on pagina2.jpg (pixels): top-left, top-right, bottom-left, bottom-right.
TL, TR, BL, BR = np.array([672.5, 377.5]), np.array([1010.0, 369.0]), np.array([681.0, 737.5]), np.array([1031.0, 734.0])


def to_page(u: float, v: float) -> np.ndarray:
    """u in [0, 9] across colour columns, v in [0, 10] down brightness rows."""
    a, b = u / 9, v / 10
    return (1 - a) * (1 - b) * TL + a * (1 - b) * TR + (1 - a) * b * BL + a * b * BR


table = pd.read_csv(OUT / "pagina2_tabla_estrellas_cuadrado.csv")
counts = table.groupby(["color_estimado", "brillo_estimado"]).size()

page = Image.open(OUT / "pagina2.jpg").convert("RGB")
draw = ImageDraw.Draw(page)
for (cls, brightness), k in counts.items():
    col, row = CLASSES.index(cls), brightness - 1
    per_line, n_lines = min(k, 4), (k + 3) // 4
    for i in range(k):  # up to 4 per line, the block centred in the cell
        du = 0.5 + 0.2 * (i % 4 - (per_line - 1) / 2)
        dv = 0.5 + 0.25 * (i // 4 - (n_lines - 1) / 2)
        x, y = to_page(col + du, row + dv)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(20, 60, 200))
page.save(OUT / "hoja_de_trabajo_sobre_la_foto.jpg", quality=95)
page.crop((640, 360, 1050, 790)).resize((820, 860), Image.LANCZOS).save(OUT / "hoja_de_trabajo_sobre_la_foto_ampliada.png")
print(counts.unstack(fill_value=0).to_string())
