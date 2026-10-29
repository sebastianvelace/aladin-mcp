"""SIMBAD, VizieR and HiPS-discovery queries with mirror fallback."""

import math
import re
import warnings
from pathlib import Path

import numpy as np
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u

from .config import (MOCSERVER_URLS, OUTPUT_DIR, REGTAP_URL, SIMBAD_SERVERS,
                     TIMEOUT, VIZIER_SERVERS)
from .mirrors import MirrorPool, describe_error

warnings.filterwarnings("ignore", module="astroquery")

simbad_pool = MirrorPool("SIMBAD", SIMBAD_SERVERS)
vizier_pool = MirrorPool("VizieR", VIZIER_SERVERS)


def clean(value):
    """Turn masked/NaN/numpy scalars into plain JSON-friendly values."""
    if value is None or value is np.ma.masked:
        return None
    if isinstance(value, (np.floating, float)):
        return None if math.isnan(value) else round(float(value), 6)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (bytes, np.bytes_)):
        value = value.decode()
    if isinstance(value, (str, np.str_)):
        return str(value).strip() or None
    return value


def _adql_str(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


# ---------------------------------------------------------------- SIMBAD

class TimeoutSession(requests.Session):
    """requests.Session with a default timeout on every request."""

    def request(self, *args, **kwargs):
        kwargs.setdefault("timeout", TIMEOUT)
        return super().request(*args, **kwargs)


def _simbad_client(server: str):
    from astroquery.simbad import Simbad

    # Simbad's `timeout` argument is the TAP execution time, not an HTTP timeout,
    # and setting it contacts the default (CDS) server. Leave it unset and give
    # the client a session that times out, before the TAPService is created.
    sb = Simbad()
    sb._session = TimeoutSession()
    sb.server = server
    return sb


def simbad_lookup(name: str) -> dict | None:
    def run(server: str):
        sb = _simbad_client(server)
        # Flux fields are NOT added here on purpose: astroquery joins them with
        # an INNER JOIN, so objects without that flux (e.g. NGC 4755 has no V)
        # vanish from the result. Fluxes and distances are queried separately.
        sb.add_votable_fields("otype", "plx_value", "plx_err", "galdim_majaxis",
                              "galdim_minaxis", "galdim_angle", "sp_type")
        basic = sb.query_object(name)
        if len(basic) == 0:
            return None
        row = basic[0]
        main_id = _adql_str(str(row["main_id"]))
        otype = sb.query_tap(
            "SELECT o.description FROM basic b JOIN otypedef o ON o.otype = b.otype "
            f"WHERE b.main_id = {main_id}")
        fluxes = sb.query_tap(
            "SELECT f.filter, f.flux, f.flux_err FROM flux f JOIN basic b ON f.oidref = b.oid "
            f"WHERE b.main_id = {main_id} ORDER BY filter")
        dists = sb.query_tap(
            "SELECT TOP 15 d.dist, d.unit, d.minus_err, d.plus_err, d.method, d.bibcode "
            "FROM mesDistance d JOIN basic b ON d.oidref = b.oid "
            f"WHERE b.main_id = {main_id} ORDER BY bibcode DESC")
        return row, otype, fluxes, dists

    result, server = simbad_pool.run(run)
    if result is None:
        return None
    row, otype, fluxes, dists = result

    coord = SkyCoord(row["ra"] * u.deg, row["dec"] * u.deg)
    plx = clean(row["plx_value"])
    out = {
        "nombre_principal": clean(row["main_id"]),
        "ra_deg": clean(row["ra"]),
        "dec_deg": clean(row["dec"]),
        "ra_hms": coord.ra.to_string(u.hourangle, sep=":", precision=2, pad=True),
        "dec_dms": coord.dec.to_string(u.deg, sep=":", precision=1, alwayssign=True, pad=True),
        "tipo_objeto": {
            "codigo": clean(row["otype"]),
            "descripcion": clean(otype["description"][0]) if len(otype) else None,
        },
        "tipo_espectral": clean(row["sp_type"]),
        "magnitudes": {clean(f["filter"]): {"mag": clean(f["flux"]), "error": clean(f["flux_err"])}
                       for f in fluxes},
        "paralaje_mas": plx,
        "paralaje_error_mas": clean(row["plx_err"]),
        "distancia_desde_paralaje_pc": round(1000.0 / plx, 1) if plx and plx > 0 else None,
        "nota_paralaje": "1/parallax is a naive estimate (ignores the Gaia zero-point and "
                         "inversion bias); prefer the published distances below." if plx else None,
        "mediciones_distancia": [
            {"valor": clean(d["dist"]), "unidad": clean(d["unit"]),
             "err_menos": clean(d["minus_err"]), "err_mas": clean(d["plus_err"]),
             "metodo": clean(d["method"]), "referencia": clean(d["bibcode"])}
            for d in dists
        ],
        "tamano_angular": None,
        "servidor": server,
    }
    major = clean(row["galdim_majaxis"])
    if major is not None:
        out["tamano_angular"] = {
            "eje_mayor_arcmin": major,
            "eje_menor_arcmin": clean(row["galdim_minaxis"]),
            "angulo_posicion_deg": clean(row["galdim_angle"]),
        }
    if not out["magnitudes"]:
        out["nota_magnitudes"] = "SIMBAD has no integrated magnitudes for this object."
    return out


def resolve_target(target: str) -> tuple[SkyCoord, str]:
    """Accept coordinates ('80.89 -69.76', '05:23:34 -69:45:22') or an object name."""
    text = target.strip()
    nums = re.split(r"[\s,]+", text)
    if len(nums) == 2:
        try:
            return SkyCoord(float(nums[0]) * u.deg, float(nums[1]) * u.deg), "coordinates"
        except ValueError:
            pass
    if re.match(r"^[\d+\-.:hmsd\s]+$", text):
        try:
            return SkyCoord(text, unit=(u.hourangle, u.deg)), "coordinates"
        except ValueError:
            pass
    info = simbad_lookup(text)
    if info is None:
        raise ValueError(f"SIMBAD does not know the object '{target}'. "
                         "Check the name or pass coordinates in degrees, e.g. '80.89 -69.76'.")
    return SkyCoord(info["ra_deg"] * u.deg, info["dec_deg"] * u.deg), f"SIMBAD: {info['nombre_principal']}"


# ---------------------------------------------------------------- VizieR

def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def vizier_fetch(catalog: str, columns: list[str] | None, filters: dict[str, str] | None,
                 max_rows: int, export_csv: bool, preview_rows: int = 10) -> dict:
    from astroquery.vizier import Vizier

    def run(server: str):
        # vizier_server must be passed explicitly: its default argument is
        # evaluated at import time, so conf.set_temp() has no effect.
        viz = Vizier(columns=columns or ["*"], column_filters=filters or {},
                     row_limit=max_rows, timeout=TIMEOUT, vizier_server=server)
        return viz.get_catalogs(catalog)

    tables, server = vizier_pool.run(run)
    if len(tables) == 0:
        raise ValueError(f"VizieR returned no table for '{catalog}'. Check the catalog ID "
                         "(e.g. 'J/AJ/138/1003') and that the filters/columns exist.")

    out_dir = OUTPUT_DIR / "vizier"
    result = {"catalogo": catalog, "servidor": server, "tablas": []}
    for table in tables:
        name = table.meta.get("name", catalog)
        info = {
            "tabla": name,
            "descripcion": table.meta.get("description"),
            "filas": len(table),
            "truncada": len(table) >= max_rows,
            "columnas": [{"nombre": c, "unidad": str(table[c].unit) if table[c].unit else None,
                          "descripcion": table[c].description} for c in table.colnames],
            "muestra": [{c: clean(r[c]) for c in table.colnames} for r in table[:preview_rows]],
        }
        if export_csv:
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"{_safe_name(name)}.csv"
            table.to_pandas().to_csv(path, index=False)
            info["csv"] = str(path)
        result["tablas"].append(info)
    return result


# ---------------------------------------------------------------- HiPS discovery

def hips_search(keyword: str, max_results: int) -> dict:
    pattern = f"*{keyword.strip('*')}*"
    params = {"ID": pattern, "dataproduct_type": "image", "fmt": "json",
              "fields": "ID,obs_title,em_min,em_max", "casesensitive": "false",
              "MAXREC": str(max_results)}
    errors = []
    for url in MOCSERVER_URLS:
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            records = resp.json()
            return {"fuente": url, "verificado_con_casing_exacto": True,
                    "resultados": [{"hips_id": r.get("ID"), "titulo": r.get("obs_title")}
                                   for r in records[:max_results]]}
        except Exception as exc:
            errors.append(f"- {url}: {describe_error(exc)}")

    # Fallback: IVOA Registry. CDS HiPS are registered as ivo://CDS/P/...
    like = keyword.strip("*").lower().replace("'", "''")
    query = ("SELECT ivoid, res_title FROM rr.resource WHERE ivoid LIKE 'ivo://cds/p/%' "
             f"AND (ivoid LIKE '%{like}%' OR LOWER(res_title) LIKE '%{like}%') ORDER BY ivoid")
    try:
        resp = requests.post(REGTAP_URL, data={"LANG": "ADQL", "FORMAT": "csv", "QUERY": query,
                                               "MAXREC": str(max_results)}, timeout=TIMEOUT)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()[1:]
    except Exception as exc:
        errors.append(f"- {REGTAP_URL}: {describe_error(exc)}")
        raise RuntimeError("MocServer and IVOA Registry both failed:\n" + "\n".join(errors))
    rows = []
    for line in lines[:max_results]:
        ivoid, _, title = line.partition(",")
        rows.append({"hips_id": ivoid.removeprefix("ivo://").replace("cds/p/", "CDS/P/", 1),
                     "titulo": title.strip('"')})
    return {"fuente": "IVOA Registry (MocServer unreachable)", "verificado_con_casing_exacto": False,
            "nota": "The registry lowercases IDs; hips2fits may need the original casing.",
            "errores_mocserver": errors, "resultados": rows}
