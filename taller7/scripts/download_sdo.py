"""Download one SDO/HMI continuum image per day (2014-11-25 .. 2014-12-20) via Helioviewer."""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.helioviewer.org/v2"
SCALE = 2.4  # arcsec per pixel
SIZE = 1024

meta = []
day = datetime(2014, 11, 25, 12)
while day <= datetime(2014, 12, 20, 12):
    iso = day.strftime("%Y-%m-%dT%H:%M:%SZ")
    info = json.load(urllib.request.urlopen(f"{API}/getClosestImage/?date={iso}&sourceId=18"))
    params = {
        "date": iso, "imageScale": SCALE, "layers": "[SDO,HMI,HMI,continuum,1,100]",
        "x0": 0, "y0": 0, "width": SIZE, "height": SIZE, "display": "true", "watermark": "false",
    }
    url = f"{API}/takeScreenshot/?" + urllib.parse.urlencode(params)
    target = OUT / f"hmi_{day:%Y%m%d}.png"
    if not target.exists():
        target.write_bytes(urllib.request.urlopen(url, timeout=120).read())
        time.sleep(1)
    meta.append({"file": target.name, "requested": iso, "obs_date": info["date"], "scale_arcsec_px": SCALE})
    print(target.name, info["date"])
    day += timedelta(days=1)

(OUT / "metadata.json").write_text(json.dumps(meta, indent=2))
