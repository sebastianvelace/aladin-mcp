"""Offline tests: they need no network and run even while the CDS is down."""

import asyncio

import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from aladin_mcp import cds, config, imaging, plotting, samp
from aladin_mcp.mirrors import MirrorPool, ServiceUnavailable

from conftest import make_wcs


# ---------------------------------------------------------------- mirrors

def test_mirror_pool_falls_back_and_promotes_the_working_mirror():
    calls = []

    def fn(server):
        calls.append(server)
        if server == "down":
            raise TimeoutError("timed out")
        return f"ok from {server}"

    pool = MirrorPool("test", ["down", "up"])
    assert pool.run(fn) == ("ok from up", "up")
    calls.clear()
    pool.run(fn)
    assert calls == ["up"], "the working mirror must be tried first next time"


def test_mirror_pool_reports_every_failure():
    pool = MirrorPool("svc", ["a", "b"])
    with pytest.raises(ServiceUnavailable) as err:
        pool.run(lambda s: (_ for _ in ()).throw(ConnectionError("connection refused")))
    assert "- a:" in str(err.value) and "- b:" in str(err.value)


# ---------------------------------------------------------------- targets

@pytest.mark.parametrize("text, ra, dec", [
    ("80.894 -69.756", 80.894, -69.756),
    ("05:23:34.6 -69:45:22", 80.894167, -69.756111),
])
def test_resolve_target_parses_coordinates_without_simbad(text, ra, dec, monkeypatch):
    monkeypatch.setattr(cds, "simbad_lookup", lambda name: pytest.fail("must not query SIMBAD"))
    coord, how = cds.resolve_target(text)
    assert how == "coordinates"
    assert coord.ra.deg == pytest.approx(ra, abs=1e-4)
    assert coord.dec.deg == pytest.approx(dec, abs=1e-4)


def test_clean_returns_none_for_masked_and_nan():
    assert cds.clean(np.ma.masked) is None
    assert cds.clean(np.float64("nan")) is None
    assert cds.clean(np.float32(1.5)) == 1.5
    assert cds.clean(b" OpC ") == "OpC"


# ---------------------------------------------------------------- survey fallback

def test_dss_alias_uses_mellinger_for_wide_fields_and_dss2_for_small_ones():
    dss = config.SURVEYS["DSS"]
    assert imaging.skyview_surveys(dss, 20) == ("Mellinger Red", "Mellinger Green", "Mellinger Blue")
    assert imaging.skyview_surveys(dss, config.WIDE_FIELD_DEG) == dss.skyview_wide
    assert imaging.skyview_surveys(dss, 0.33) == ("DSS2 Red",)
    assert imaging.skyview_surveys(config.SURVEYS["AKARI"], 20) == ("AKARI WIDE-L",)


def test_clean_header_makes_mellinger_style_headers_writable(tmp_path):
    # astropy will not create a card with a tab, but parses one from raw text, as SkyView sends it.
    raw = make_wcs(10, 0.1).to_header().tostring()
    tab_card = "COMMENT Reference:   PASP 121, 1180, 2009\tSurvey website.".ljust(80)
    header = fits.Header.fromstring(raw.replace("END" + " " * 77, tab_card + "END".ljust(80)))
    with pytest.raises(fits.VerifyError):
        fits.PrimaryHDU(np.zeros((10, 10)), header).writeto(tmp_path / "bad.fits")
    fits.PrimaryHDU(np.zeros((10, 10)), imaging.clean_header(header)).writeto(tmp_path / "ok.fits")
    assert "PASP 121" in str(fits.getheader(tmp_path / "ok.fits")["COMMENT"])


def test_fetch_image_keeps_fractional_fov_in_file_names(tmp_path, monkeypatch):
    from astropy.coordinates import SkyCoord

    monkeypatch.setattr(imaging, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(imaging, "resolve_target", lambda t: (SkyCoord(193.4, -60.4, unit="deg"), "test"))
    hdul = fits.HDUList([fits.PrimaryHDU(np.random.default_rng(1).normal(size=(64, 64)),
                                         make_wcs(64, 0.005, 193.4, -60.4).to_header())])
    monkeypatch.setattr(imaging.hips2fits_pool, "run", lambda fn: (hdul, "fake"))
    result = imaging.fetch_image("NGC 4755", "DSS", 0.33, 64, None, "TAN")
    assert result["fits"].endswith("_0.33deg.fits")
    assert result["png"].endswith("_0.33deg.png")


# ---------------------------------------------------------------- size measurement

def test_measure_size_recovers_the_diameter_of_a_disk_without_smoothing(disk_fits):
    radius_px, scale = 30, 0.05
    m = imaging.measure_size(str(disk_fits(radius_px, scale_deg=scale)), 3.0, 0, 50.0, return_arrays=True)
    expected = 2 * radius_px * scale
    assert m["diametro_equivalente_deg"] == pytest.approx(expected, rel=0.01)
    assert m["eje_mayor_deg"] == pytest.approx(expected, rel=0.02)
    assert m["region_elegida"].startswith("region containing")
    assert m["avisos"] is None
    assert m["diametro_fisico_kpc"] == pytest.approx(50 * np.radians(expected), rel=0.01)


@pytest.mark.parametrize("sigma_px", [2, 4, 8])
def test_smoothing_widens_a_sharp_edge_by_two_to_three_sigma(disk_fits, sigma_px):
    # Known bias, documented in LIMITATIONS: the threshold sits far below a bright source's
    # level, so the blurred edge moves outwards by ~2-3 smoothing sigmas in radius.
    radius_px, scale = 30, 0.05
    m = imaging.measure_size(str(disk_fits(radius_px, scale_deg=scale)), 3.0, sigma_px, None,
                             return_arrays=True)
    growth_sigmas = (m["diametro_equivalente_deg"] / scale / 2 - radius_px) / sigma_px
    assert 2.0 <= growth_sigmas <= 3.0


def test_measure_size_flags_regions_touching_the_edge(disk_fits):
    m = imaging.measure_size(str(disk_fits(120)), 3.0, None, None, return_arrays=True)
    assert m["toca_el_borde"] is True
    assert any("LOWER LIMIT" in w for w in m["avisos"])


def test_measure_size_warns_when_the_centre_is_below_threshold(disk_fits):
    path = disk_fits(10, offset=(60, 60))  # source away from the centre
    m = imaging.measure_size(str(path), 3.0, None, None, return_arrays=True)
    assert m["region_elegida"].startswith("largest")
    assert any("different source" in w for w in m["avisos"])


# ---------------------------------------------------------------- CMD plot

def test_plot_cmd_accepts_column_differences(tmp_path):
    csv = tmp_path / "stars.csv"
    pd.DataFrame({"Bmag": [10.0, 12.0, None], "Vmag": [10.2, 11.0, 13.0]}).to_csv(csv, index=False)
    out = plotting.plot_cmd(str(csv), "Vmag", "Bmag-Vmag", "test", str(tmp_path / "cmd.png"))
    assert out["puntos_graficados"] == 2
    assert out["filas_descartadas_sin_dato"] == 1
    assert out["rango_color"] == [-0.2, 1.0]
    assert (tmp_path / "cmd.png").exists()


def test_plot_cmd_lists_columns_when_one_is_missing(tmp_path):
    csv = tmp_path / "stars.csv"
    pd.DataFrame({"Bmag": [10.0], "Vmag": [10.2]}).to_csv(csv, index=False)
    with pytest.raises(KeyError, match="Available columns"):
        plotting.plot_cmd(str(csv), "Vmag", "B-V", "test", None)


# ---------------------------------------------------------------- SAMP and server

def test_aladin_send_explains_how_to_start_a_hub(monkeypatch):
    def no_hub(self, *a, **k):
        raise samp.SAMPHubError("Unable to find a running SAMP Hub")

    monkeypatch.setattr(samp.SAMPIntegratedClient, "connect", no_hub)
    out = samp.send("zoom 10deg")
    assert out["enviado"] is False
    assert "Interop" in out["mensaje"]


def test_server_exposes_the_seven_tools():
    from aladin_mcp.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert names == {"simbad_query", "vizier_query", "get_survey_image", "measure_angular_size",
                     "plot_cmd", "aladin_send", "hips_search"}
