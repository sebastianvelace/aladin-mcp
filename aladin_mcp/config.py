"""Service endpoints, mirrors, timeouts and the verified HiPS aliases."""

import os
from dataclasses import dataclass

from . import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "output"

# Per-request timeout in seconds. CDS can be slow; mirrors are tried in order.
TIMEOUT = float(os.environ.get("ALADIN_MCP_TIMEOUT", "30"))

# astroquery only accepts these two SIMBAD hosts.
SIMBAD_SERVERS = ["simbad.cds.unistra.fr", "simbad.harvard.edu"]

# Note: vizier.cfa.harvard.edu is a gateway to Strasbourg, so it fails when
# CDS itself is unreachable (504 Gateway Time-out).
VIZIER_SERVERS = [
    "vizier.cds.unistra.fr",
    "vizier.cfa.harvard.edu",
    "vizier.iucaa.in",
    "vizier.nao.ac.jp",
]

HIPS2FITS_SERVERS = [
    "https://alasky.cds.unistra.fr/hips-image-services/hips2fits",
    "https://alaskybis.cds.unistra.fr/hips-image-services/hips2fits",
]

MOCSERVER_URLS = [
    "https://alasky.cds.unistra.fr/MocServer/query",
    "https://alaskybis.cds.unistra.fr/MocServer/query",
]

# IVOA Registry (RegTAP) used to verify HiPS IDs when the MocServer is down.
REGTAP_URL = "https://dc.g-vo.org/tap/sync"


@dataclass(frozen=True)
class Survey:
    hips_id: str
    skyview: str  # NASA SkyView fallback survey name
    band: str


# Each hips_id was verified on 2026-10-28:
# - CDS/P/DSS2/color and CDS/P/Fermi/color: exact creator_did read from the
#   HiPS "properties" file (ESASky mirror).
# - AKARI and PLANCK: present in the IVOA Registry as ivo://cds/p/akari/fis/color
#   and ivo://cds/p/planck/r2/hfi/color (the registry lowercases IDs; the
#   casing below is the CDS convention). Use the hips_search tool to recheck.
SURVEYS = {
    "DSS": Survey("CDS/P/DSS2/color", "DSS2 Red", "optical"),
    "AKARI": Survey("CDS/P/AKARI/FIS/Color", "AKARI WIDE-L", "far infrared (65-140 um)"),
    "PLANCK": Survey("CDS/P/PLANCK/R2/HFI/color", "Planck 857 I", "submm/radio (353-857 GHz)"),
    "FERMI": Survey("CDS/P/Fermi/color", "Fermi 5", "gamma rays (0.3-300 GeV)"),
}
