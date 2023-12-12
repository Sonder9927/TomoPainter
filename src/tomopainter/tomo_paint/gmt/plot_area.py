from pathlib import Path

import numpy as np
import pandas as pd
import pygmt

from .gmt_fig import fig_tomos
from .gmt_make_data import make_topos, makecpt, tomo_grid


def plot_area_map(regions, fig_name):
    grd = pygmt.datasets.load_earth_relief(resolution="01m", region=regions[0])
    vicinity = {
        "topo": {"region": regions[0]},
        "tomos": [{"grid": grd, "cmap": makecpt([-3000, 2500], cmap="globe")}],
    }
    area = make_topos("ETOPO1", regions[1])
    gmt_fig_area(vicinity, area, fig_name)


def plot_model(df, region, cpt, fn):
    """plot model by idt with ave"""
    # topo file
    topo = make_topos("ETOPO1", region)
    tomo = {
        "grid": "temp/tomo.grd",
        "cmap": makecpt(cpt["series"], cmap=cpt["cmap"], reverse=True),
    }
    tomo_grid(df, region, tomo["grid"])
    # gmt plot
    _gmt_fig_model(topo, tomo, fn)


# def plot_misfit(df, region, series, fig_name: Path) -> None:
#     """plot misfit"""
#     topo = make_topos("ETOPO1", region)
#     tomo = {
#         "grid": "temp/tomo.grd",
#         "cmap": makecpt(series, cmap="hot", reverse=True),
#     }
#     tomo_grid(df, region, tomo["grid"])
#     gmt_fig_misfit(topo, tomo, fig_name)


def _gmt_fig_model(topo, tomo, fn):
    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
        FONT="10",
    )
    kwgs = {"tect": 0, "clip": True}
    fig = fig_tomos(fig, topo, [tomo], **kwgs)
    fig.colorbar(cmap=tomo["cmap"], frame=["a", f"x+l{fn.stem}", "y"])
    fig.savefig(str(fn))


def old_plot_model(region, fn):
    topo = make_topos("ETOPO1", region)
    tomos = _model_tomos(region)
    _old_gmt_fig_model(topo, tomos, fn)


def _model_tomos(region):
    from tomopainter.rose import xyz_ave

    tomos = [
        {"grid": f"temp/{i}.grd", "cmap": f"temp/{i}.cpt"}
        for i in ["sed", "poisson", "rj_moho", "mc_moho"]
    ]
    sed = pd.read_csv(
        "data/txt/tects/sedthk.xyz",
        header=None,
        delim_whitespace=True,
        names=["x", "y", "z"],
    )
    sed["z"] = sed["z"] / sed["z"].mean()
    tomo_grid(sed, region, tomos[0]["grid"])
    makecpt([0, 2, 0.05], tomos[0]["cmap"], cmap="jet", reverse=True)
    moho = pd.read_csv(
        "data/moho.lst",
        header=None,
        usecols=[0, 1, 2],
        names=["x", "y", "z"],
        delim_whitespace=True,
    )
    moho = moho[["y", "x", "z"]]
    moho.columns = ["x", "y", "z"]
    tomo_grid(moho, region, tomos[1]["grid"])
    makecpt([27, 35, 0.1], tomos[1]["cmap"], cmap="jet", reverse=True)
    return tomos


def _old_gmt_fig_model(topo, tomos, fn):
    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
        FONT="10",
    )
    with fig.subplot(
        nrows=1, ncols=3, figsize=("23c", "8c"), autolabel=True, margins="0.5c"
    ):
        kwgs = {"projection": "M?", "tect": 0, "clip": True}
        with fig.set_panel(panel=0):
            fig = fig_tomos(fig, topo, [tomos[0]], **kwgs)
            cpt = tomos[0]["cmap"]
            fig.colorbar(cmap=cpt, frame=["a", "x+lSedthk", "y"])
        with fig.set_panel(panel=1):
            fig = fig_tomos(fig, topo, [tomos[1]], **kwgs)
            cpt = tomos[1]["cmap"]
            fig.colorbar(cmap=cpt, frame=["a", "x+lMoho", "y"])
        with fig.set_panel(panel=2):
            fig = fig_tomos(fig, topo, [tomos[2]], **kwgs)
            cpt = tomos[2]["cmap"]
            fig.colorbar(cmap=cpt, frame=["a", "x+lPoisson", "y"])
    fig.savefig(fn)


def gmt_fig_area(vici, area, fn):
    from tomopainter.rose import idt_profiles

    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
        FONT="10",
    )
    with fig.subplot(
        nrows=1, ncols=2, figsize=("15c", "8c"), autolabel=True, margins="0.5c"
    ):
        kwgs = {"projection": "M?", "tect": 0, "eles": ["sta", "volcano"]}
        with fig.set_panel(panel=0):
            fig = fig_tomos(fig, **vici, **kwgs)
            fig.text(
                textfiles="data/txt/tects/viciTectName.txt",
                angle=True,
                font=True,
                justify=True,
            )
            fig = _plot_area_boundary(fig, area["region"])
            cpt = vici["tomos"][0]["cmap"]
            fig.colorbar(cmap=cpt, frame=["a", "x+lElevation", "y+lm"])

        with fig.set_panel(panel=1):
            lines = idt_profiles("data/txt/profile.json", idt=False)
            kwgs |= {"tect": 1, "lines": lines, "line_pen": "thick,brown"}
            kwgs["eles"] = ["basalt", "volcano"]
            fig = fig_tomos(fig, area, [], **kwgs)
            fig.text(
                textfiles="data/txt/tects/areaTectName.txt",
                angle=True,
                font=True,
                justify=True,
                pen="0.5p,-",
            )
            cpt = area["cpt"]
            # fig.colorbar(cmap=cpt, frame=["a", "x+lElevation", "y+lm"])
    fig.savefig(fn)


def plot_rays(regions, df, fig_name):
    topo = make_topos("ETOPO1", regions[0])
    tr = _read_coord(df, sta=True)
    tr["evt"] = tr.apply(lambda r: [r["ex"], r["ey"]], axis=1)
    tr["sta"] = tr.apply(lambda r: [r["sx"], r["sy"]], axis=1)
    lines = df[["evt", "sta"]].values.tolist()
    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
        FONT="10",
    )
    # fig = fig_htopo(fig, topos, lines, "0.1p")
    fig = fig_tomos(fig, topo, [], lines=lines, line_pen="0.1p")
    fig = _plot_area_boundary(fig, regions[1])
    fig.savefig(fig_name)


def _plot_area_boundary(fig, region):
    [x1, x2, y1, y2] = region
    data = np.array(
        [
            [[x1, y1], [x2, y1]],
            [[x2, y1], [x2, y2]],
            [[x2, y2], [x1, y2]],
            [[x1, y2], [x1, y1]],
        ]
    )
    for ll in data:
        fig.plot(data=ll, pen="thick,red")
    return fig


def plot_evt_sites(df, region: list, fn: str):
    cen = [sum(region[:2]) / 2, sum(region[-2:]) / 2]
    # num = len(df)  # 409
    tr = _read_coord(df, hn=4, sta=None)
    sites = tr[["ex", "ey", "ez", "em"]]
    sites["em"] = sites["em"] * 0.08
    tr["evt"] = tr.apply(lambda r: [r["ex"], r["ey"]], axis=1)
    tr["sta"] = tr["evt"].apply(lambda _: cen)
    lines = df[["evt", "sta"]].values.tolist()

    fig = pygmt.Figure()
    pygmt.config(
        FORMAT_GEO_MAP="+D",
    )
    fig.coast(
        projection=f"E{cen[0]}/{cen[1]}/130/8i",
        region="g",
        shorelines="0.25p,black",
        land="yellow",
        water="white",
        area_thresh=10_000,
        frame="a",
    )
    fig.plot("data/txt/tects/PB2002_plates.dig.txt", pen="1.5p,darkred,.")
    cen = np.array(cen)
    for line in lines:
        fig.plot(data=line, pen="thick,black")
    cc = makecpt([0, 200, 0.01], cmap="rainbow.cpt", reverse=True)
    # pygmt.makecpt([0, 200, 0.01], cmap="rainbow.cpt", reverse="c")
    fig.plot(data=sites, style="c", cmap=cc, pen="white")
    fig.plot(data=[cen], style="t0.6c", fill="red", pen="white")

    for dd in range(60, 300, 60):
        fig.plot(data=[cen], style=f"E{dd}d", pen="0.3p,black")
    for y in [60, 90, 120]:
        fig.text(
            text=y,
            x=cen[0],
            y=cen[1] - y,
            font="15.0p",
            offset="0c/0c",
            fill="white",
        )
    fig.colorbar(
        cmap=cc,
        frame='xa40f20+l"Depth (km)"',
        position="jBC+w20c/0.5c+o0c/-2c+m+h",
        shading=True,
    )

    fig.savefig(fn)


def _read_coord(df, hn=2, sta=None):
    txt = Path("data/txt")
    header = ["x", "y", "z", "m"]
    evt = pd.read_csv(
        txt / "event_mag.lst",
        header=None,
        delim_whitespace=True,
        names=["evt"] + header,
        index_col="evt",
    )
    for i in header[:hn]:
        df[f"e{i}"] = df["evt"].apply(lambda en: evt[i][en])
    if sta:
        sta = pd.read_csv(
            "data/station.lst",
            header=None,
            delim_whitespace=True,
            names=["sta"] + header,
            index_col="sta",
        )
        df["sx"] = df["sta"].apply(lambda sn: sta["x"][sn])
        df["sy"] = df["sta"].apply(lambda sn: sta["y"][sn])

    return df


def gmt_fig_misfit(topo, tomo, fname):
    # gmt plot
    fig = pygmt.Figure()
    # define figure configuration
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        # MAP_TITLE_OFFSET="0.25p",
        # MAP_DEGREE_SYMBOL="none",
        # FONT_TITLE="18",
        FONT="10",
    )
    kwgs = {"tect": 0, "clip": True}
    fig = fig_tomos(fig, topo, [tomo], [f"+t{fname.stem}", "a"], **kwgs)
    # plot colorbar
    fig.colorbar(cmap=tomo["cmap"], position="JRM", frame="xa")

    fig.savefig(str(fname))
