"""MCP server for the Aladin / CDS ecosystem (SIMBAD, VizieR, HiPS, SAMP)."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Keep every cache inside the project folder. This must run before astropy,
# astroquery or matplotlib are imported, because they resolve these paths at
# import time (astropy only honours XDG_* when the "astropy" subdir exists).
for _var, _sub in (("XDG_CACHE_HOME", ".cache"), ("XDG_CONFIG_HOME", ".config")):
    _base = PROJECT_ROOT / _sub
    (_base / "astropy").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(_var, str(_base))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
