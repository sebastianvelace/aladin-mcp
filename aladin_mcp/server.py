"""MCP server exposing SIMBAD, VizieR, HiPS images, size measurement, CMD plots and Aladin SAMP."""

import asyncio
import json
from typing import Annotated, Any

from pydantic import Field

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import cds, imaging, plotting, samp
from .config import SURVEYS

mcp = MCPServer(
    "aladin_mcp",
    instructions=(
        "Tools for an astronomy workshop with the CDS ecosystem: SIMBAD lookups, VizieR "
        "catalogues, HiPS survey images (aliases DSS, AKARI, PLANCK, FERMI), approximate "
        "angular-size measurement, colour-magnitude diagrams, and Aladin Desktop control "
        "via SAMP. Files are written under the project's output/ folder."
    ),
)

READ_ONLY_NET = ToolAnnotations(readOnlyHint=True, openWorldHint=True, idempotentHint=True)
LOCAL_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False,
                              idempotentHint=True)


async def _call(fn, *args) -> str:
    """Run blocking astroquery code off the event loop; turn failures into readable errors."""
    try:
        result = await asyncio.to_thread(fn, *args)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2)
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@mcp.tool(annotations=READ_ONLY_NET)
async def simbad_query(
    nombre: Annotated[str, Field(description="Object name as SIMBAD knows it, e.g. 'NGC 4755', 'LMC', 'Jewel Box'.")],
) -> str:
    """Look up an object in SIMBAD: coordinates, object type, magnitudes, parallax,
    published distances and angular size (galdim) when available. Tries the CDS
    server first and falls back to the Harvard mirror."""
    def run():
        info = cds.simbad_lookup(nombre)
        if info is None:
            raise ValueError(f"SIMBAD has no object called '{nombre}'. Try another name "
                             "(e.g. 'NGC 4755' or 'Jewel Box').")
        return info
    return await _call(run)


@mcp.tool(annotations=READ_ONLY_NET)
async def vizier_query(
    catalogo: Annotated[str, Field(description="VizieR catalogue or table ID, e.g. 'J/AJ/138/1003'.")],
    columnas: Annotated[list[str] | None, Field(description="Columns to return. None = default columns; ['**'] = all columns.")] = None,
    filtros: Annotated[dict[str, str] | None, Field(description="VizieR column constraints, e.g. {'Vmag': '<15', 'B-V': '-0.5..2'}.")] = None,
    max_filas: Annotated[int, Field(ge=1, le=200000, description="Maximum rows per table.")] = 50,
    exportar_csv: Annotated[bool, Field(description="Save each table as CSV under output/vizier/.")] = True,
) -> str:
    """Query a VizieR catalogue. Returns table metadata, column units, a 10-row
    sample and (optionally) the CSV path of each table, ready for plot_cmd."""
    return await _call(cds.vizier_fetch, catalogo, columnas, filtros, max_filas, exportar_csv)


@mcp.tool(annotations=LOCAL_WRITE.model_copy(update={"openWorldHint": True}))
async def get_survey_image(
    objetivo_o_coordenadas: Annotated[str, Field(description="Object name ('LMC') or coordinates in degrees ('80.89 -69.76') or sexagesimal ('05:23:34 -69:45:22').")],
    hips_id: Annotated[str, Field(description="HiPS ID (e.g. 'CDS/P/DSS2/color') or alias: " + ", ".join(f"{k} -> {v.hips_id}" for k, v in SURVEYS.items()))] = "DSS",
    fov_grados: Annotated[float, Field(gt=0, le=180, description="Field of view in degrees (LMC needs ~15-20).")] = 1.0,
    ancho_px: Annotated[int, Field(ge=64, le=4000, description="Image width in pixels.")] = 800,
    alto_px: Annotated[int | None, Field(ge=64, le=4000, description="Height in pixels; default = width.")] = None,
    proyeccion: Annotated[str, Field(description="Projection code: TAN, SIN, CAR, AIT...")] = "TAN",
) -> str:
    """Download a survey cutout with CDS hips2fits (NASA SkyView as fallback), save it
    as FITS + PNG under output/images/ and return both paths plus pixel scale."""
    return await _call(imaging.fetch_image, objetivo_o_coordenadas, hips_id, fov_grados,
                       ancho_px, alto_px, proyeccion)


@mcp.tool(annotations=LOCAL_WRITE)
async def measure_angular_size(
    fits: Annotated[str, Field(description="Path to a FITS file (e.g. from get_survey_image).")],
    umbral: Annotated[float, Field(gt=0, description="Threshold in noise sigmas above background. Lower = larger size.")] = 3.0,
    suavizado_px: Annotated[float | None, Field(ge=0, description="Gaussian smoothing sigma in pixels; default 1% of image size.")] = None,
    distancia_kpc: Annotated[float | None, Field(gt=0, description="Optional distance to convert to physical size (LMC ~50).")] = None,
) -> str:
    """Approximate angular diameter of the main emission in a FITS image using its WCS.
    Smooths, thresholds at background + umbral*sigma, keeps the central connected region
    and reports equivalent-circle and ellipse diameters. The response explains the method
    and its limitations; always report them alongside the number."""
    return await _call(imaging.measure_size, fits, umbral, suavizado_px, distancia_kpc)


@mcp.tool(annotations=LOCAL_WRITE)
async def plot_cmd(
    csv: Annotated[str, Field(description="Path to a CSV (e.g. from vizier_query).")],
    col_mag: Annotated[str, Field(description="Magnitude column, e.g. 'Vmag'.")],
    col_color: Annotated[str, Field(description="Colour column ('B-V') or difference of two columns ('Bmag-Vmag').")],
    titulo: Annotated[str, Field(description="Plot title.")] = "Colour-magnitude diagram",
    salida: Annotated[str | None, Field(description="Output PNG path; default output/plots/<title>.png.")] = None,
) -> str:
    """Plot apparent magnitude (inverted vertical axis) against colour index and save a PNG."""
    return await _call(plotting.plot_cmd, csv, col_mag, col_color, titulo, salida)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
async def aladin_send(
    comandos: Annotated[str, Field(description="Aladin script, commands separated by ';' or newlines. "
                                   "Examples: 'get hips(CDS/P/DSS2/color); LMC; zoom 20deg', "
                                   "'get VizieR(J/AJ/138/1003) LMC 5deg', 'NGC 4755; zoom 30arcmin'.")],
) -> str:
    """Send script commands to a running Aladin Desktop via SAMP (mtype script.aladin.send).
    If no SAMP hub is active, explains how to enable it in Aladin."""
    return await _call(samp.send, comandos)


@mcp.tool(annotations=READ_ONLY_NET)
async def hips_search(
    palabra: Annotated[str, Field(description="Keyword in the HiPS ID or title, e.g. 'AKARI', 'Planck', 'DSS2'.")],
    max_resultados: Annotated[int, Field(ge=1, le=200)] = 30,
) -> str:
    """Find HiPS image surveys and their exact IDs in the CDS MocServer (falls back to
    the IVOA Registry). Use it to verify an ID before get_survey_image."""
    return await _call(cds.hips_search, palabra, max_resultados)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
