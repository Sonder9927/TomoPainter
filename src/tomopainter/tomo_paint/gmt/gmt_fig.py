from pathlib import Path

import pandas as pd

from .gmt_make_data import area_clip


def fig_tomos(fig, topo, tomos, frame=None, **kwargs):
    if frame is None:
        frame = "a"
    tomo_param = {"nan_transparent": True}
    # basemap and topo
    fig.basemap(
        region=topo["region"],
        projection=kwargs.get("projection") or _hscale(topo["region"]),
        frame=frame,
    )
    if gra := topo.get("gra"):
        fig.grdimage(
            grid=topo["grd"],
            cmap=topo["cpt"],
            shading=gra,
        )
        tomo_param["shading"] = gra
    # plot tomos
    if kwargs.get("clip"):
        for tomo in tomos:
            tomo["grid"] = area_clip(tomo["grid"], region=topo["region"])
            fig.grdimage(**tomo, **tomo_param)
    else:
        for tomo in tomos:
            fig.grdimage(**tomo, **tomo_param)

    # plot tects and elements like sta basalt valcano
    if (tect := kwargs.get("tect")) is not None:
        _fig_tects(fig, tect)
        # eles = [] if (ee := kwargs.get("eles")) is None else ee
        # fig = fig_tect_and_sta(fig, tect, eles)
    if (eles := kwargs.get("eles")) is not None:
        fig_elements(fig, sorted(eles))

    # plot lines
    lines = kwargs.get("lines")
    if lines is not None:
        for line in lines:
            fig.plot(data=line, pen=kwargs["line_pen"])
    return fig


def fig_elements(fig, elements):
    txt = Path("data/txt")
    fig_element_funcs = {
        "sta": _fig_stations,
        "basalt": _fig_basalts,
        "valcano": _fig_valcanos,
    }
    for e in elements:
        fig_element_funcs[e](fig, txt)


def _fig_tects(fig, tn):
    txt = Path("data/txt")
    fig.coast(shorelines="1/0.5p,black")
    # tectonics
    geo_data = ["China_tectonic.dat", "CN-faults.gmt", "find.gmt"]
    pens = ["1p,black,-", "0.5p,black,-"]
    fig.plot(data=txt / f"tects/{geo_data[tn]}", pen=pens[0])
    fig.plot(data=txt / "tects/small_faults.gmt", pen=pens[1])
    # fig.plot(data="data/txt/tects/small_faults_finding.gmt", pen="red,-")


def _fig_basalts(fig, txt):
    from .gmt_make_data import makecpt

    basalts = pd.read_csv(txt / "tects/China_basalts_data.csv")
    # filter by age
    basalts = basalts[basalts["age"] < 10]
    cc = "temp/temp.cpt"
    cc = makecpt([0, 10], cmap="hot", reverse=True)
    fig.plot(data=basalts[["x", "y", "age"]], style="c0.2c", cmap=cc)
    fig.colorbar(cmap=cc, position="JMR", frame="a")


def _fig_stations(fig, txt):
    stas = pd.read_csv(txt / "station.csv", usecols=[1, 2])
    fig.plot(data=stas, style="t0.15c", fill="darkblue")


def _fig_valcanos(fig, txt):
    # nushan
    fig.plot(x=118.09, y=32.8, style="ksquaroid/0.4c", fill="magenta")
    # xinchang
    fig.plot(x=120.88, y=29.5, style="ksquaroid/0.4c", fill="magenta")
    # # xilong
    # fig.plot(x=119.44, y=30.45, style="ksquaroid/0.4c", fill="magenta")


def fig_tect_and_sta(fig, tect, elements):
    txt = Path("data/txt")
    fig.coast(shorelines="1/0.5p,black")
    # basalts
    if "basalt" in elements:
        basalts = pd.read_csv(txt / "tects/China_basalts_data.csv")
        # filter by age
        basalts = basalts[basalts["age"] < 10]
        cc = "temp/temp.cpt"
        cc = makecpt([0, 10], cmap="hot", reverse=True)
        fig.plot(data=basalts[["x", "y", "age"]], style="c0.2c", cmap=cc)
        fig.colorbar(cmap=cc, position="JMR+w4c/0.2c+o0.5c/0c", frame="a")

    # plot valcano
    if "valcano" in elements:
        # nushan
        fig.plot(x=118.09, y=32.8, style="ksquaroid/0.4c", fill="magenta")
        # xinchang
        fig.plot(x=120.88, y=29.5, style="ksquaroid/0.4c", fill="magenta")
        # # xilong
        # fig.plot(x=119.44, y=30.45, style="ksquaroid/0.4c", fill="magenta")

    # stations
    if "sta" in elements:
        stas = pd.read_csv(txt / "station.csv", usecols=[1, 2])
        fig.plot(data=stas, style="t0.15c", fill="darkblue")

    # tectonics
    geo_data = ["China_tectonic.dat", "CN-faults.gmt", "find.gmt"]
    tect_pens = ["1p,black,-", "0.5p,black,-"]
    fig.plot(data=txt / f"tects/{geo_data[tect]}", pen=tect_pens[0])
    fig.plot(data=txt / "tects/small_faults.gmt", pen=tect_pens[1])
    # fig.plot(data="data/txt/tects/small_faults_finding.gmt", pen="red,-")
    return fig


def _hscale(region: list) -> str:
    # projection
    x = (region[0] + region[1]) / 2
    y = (region[2] + region[3]) / 2
    return f"m{x}/{y}/0.3i"
