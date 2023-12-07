from pathlib import Path

from icecream import ic
import numpy as np
import pandas as pd
import pygmt

from .gmt_fig import fig_tomos
from .gmt_make_data import make_topos, makecpt, series, tomo_grid
from .panel import vpanel_clip_data, vpanel_makecpt


# plot v plane
def plot_vs_vpanel(
    vs, *, idt, moho, line, path, hregion, dep, fname, lab=None, ave=False
):
    """
    gmt plot vplane of vs contain abso and ave.
    The abscissa is determined by `idt` which should be x or y.
    """
    lregion = _profile_range(idt, line, dep)
    # topo and borders
    topo = "ETOPO1"
    topo_data = f"data/txt/tects/{topo}.grd"
    topo = make_topos(topo, hregion)
    borders = _profile_borders(path, topo_data, moho, lab, idt)

    # make cpt files
    cpts = [f"temp/{c}" for c in ["crust.cpt", "lithos.cpt", "Vave.cpt"]]
    vpanel_makecpt(*cpts)

    # vs grid
    grid = vs[[idt, "z", "v"]]
    grid.columns = ["x", "y", "z"]
    vs_grd = "temp/temp.grd"
    tomo_grid(grid, lregion, vs_grd, blockmean=[0.5, 1])
    tomos = [{"grid": vs_grd, "cmap": cpts[-1]}]
    suffix = "_ave"
    title = f"ave Sv({idt})"
    if not ave:
        ic("Clipping moho from vs.grd...")
        # cut tomo_moho from vs_grd
        data = vpanel_clip_data(vs_grd, borders[1], lregion)
        # notice the order of grdimage: 1-lithos, 2-crust
        tomos = [
            {"grid": vs_grd, "cmap": cpts[1]},
            {"grid": data, "cmap": cpts[0]},
        ]
        ic("Distincted crust data!")
        suffix = "_vel"
        title = f"Sv({idt})"

    fname = f"{fname}_{idt}{suffix}.png"
    gmt_plot_vs_vpanel(topo, tomos, lregion, borders, line, title, fname, ave)


def plot_vs_hpanel(grd, region, fname, *, eles, ave):
    """
    gmt plot hplane of vs
    """
    # topo file
    topo = make_topos("ETOPO1", region)

    # make cpt file
    if ave:
        cptfile = makecpt([-5, 5, 0.1], cmap="jet", reverse=True)
    else:
        # series = [2.5, 5.5, 0.1]
        grid = pygmt.grd2xyz(grd)
        cptfile = makecpt(series(grid, method=2), cmap="jet", reverse=True)

    tomo = {"grid": grd, "cmap": cptfile}

    # gmt plot hplane
    gmt_plot_vs_hpanel(topo, tomo, fname, eles)


# gmt plot v plane
def gmt_plot_vs_vpanel(topo, tomos, lregion, borders, line, title, fn, ave):
    ic("figing...")
    # gmt plot
    fig = pygmt.Figure()
    # define figure configuration
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
    )
    ltopo = {"region": lregion[:2] + [0, 1200]}
    kwgs = {"projection": "X6i/0.5i", "lines": [borders[0]], "line_pen": "4"}
    fig = fig_tomos(fig, ltopo, [], [f"sW+t{title}", "ya400"], **kwgs)
    # fig = fig_vtopo(fig, borders[0], lregion[:2] + [0, 2000], title)
    fig.shift_origin(yshift="-5.5")
    ltopo["region"] = lregion
    kwgs = {
        "projection": "X6i/2i",
        "lines": borders[1:],
        "line_pen": "1p,black,-",
    }
    fig = fig_tomos(fig, ltopo, tomos, **kwgs)
    fig.shift_origin(yshift="-2")
    if ave:
        fig.colorbar(
            cmap=tomos[0]["cmap"],
            position="JBC+w3i/0.10i+o0c/-0.5i+h",
            frame="xa2f2",
        )
    else:
        # notice tomos is [lithos, crust]
        fig.colorbar(
            cmap=tomos[1]["cmap"],
            position="JBC+w2.8i/0.1i+o-1.5i/-0.5i+h",
            frame="xa+lCrust",
        )
        # fig.shift_origin(yshift="-1")
        fig.colorbar(
            cmap=tomos[0]["cmap"],
            position="JBC+w2.8i/0.1i+o1.5i/-0.5i+h",
            frame="xa+lMantle",
        )
    fig.shift_origin(yshift="-5", xshift="2i")
    kwgs = {
        "lines": [line],
        "line_pen": "fat,red",
        "tect": 0,
        "eles": ["basalt", "volcano"],
    }
    fig = fig_tomos(fig, topo, [], **kwgs)

    fig.savefig(fn)


def gmt_plot_vs_hpanel(topo, tomo, fname, eles):
    # define figure configuration
    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        # MAP_TITLE_OFFSET="0.25p",
        # MAP_DEGREE_SYMBOL="none",
        MAP_FRAME_WIDTH="0.1c",
        FONT_ANNOT_PRIMARY="10p,Times-Roman",
        FONT_TITLE="13p,Times-Roman",
        # FONT="10",
    )

    text = Path(fname).stem.split("_")[-2]
    fig = fig_tomos(fig, topo, [tomo], **eles)
    fig.text(
        x=topo["region"][0],
        y=topo["region"][-1],
        fill="white",
        justify="LT",
        font="9p",
        text=text,
        offset="j0.1",
    )
    # fig.colorbar(cmap=cpt, position="jBC+w5c/0.3c+o0i/-1c+h+m", frame="a2f4")
    fig.colorbar(cmap=tomo["cmap"], frame=["a", "y"])
    # plot colorbar
    # fig.colorbar(
    #     cmap=cpt, position="jMR+v+w10c/0.3c+o-1.5c/0c+m", frame="xa0.2f0.2"
    # )
    # fig.colorbar(
    #     cmap=cpt, position="jTC+w10c/0.3c+o0i/-4c+h", frame="xa0.2f0.2"
    # )
    # fig.colorbar(
    #     cmap=cpt, position="jML+w10c/0.3c+o-1.5i/0i+v", frame="xa0.2f0.2"
    # )

    fig.savefig(fname)


def _profile_range(idt, line, dep) -> list[float]:
    ic(line, idt)
    if idt == "x":
        idtn = 0
    elif idt == "y":
        idtn = 1
    else:
        raise KeyError("Please select `x` or `y` for abscissa of vplane")
    return sorted([line[0][idtn], line[1][idtn]]) + [dep, 0]


def _profile_borders(path, topo_data, moho, lab, idt):
    protopo: pd.DataFrame = pygmt.grdtrack(
        points=path,
        grid=topo_data,
        newcolname="newz",
        verbose="w",
        coltypes="g",
    )  # pyright: ignore
    protopo.columns = ["x", "y", "n", "z"]
    protopo = protopo[[idt, "z"]]
    # moho
    promoho = moho[[idt, "z"]]
    promoho.columns = ["x", "y"]

    borders = [protopo, promoho]

    if lab is not None:
        prolab = lab[[idt, "z"]]
        prolab.columns = ["x", "y"]
        borders.append(prolab)
    return borders


def lab_by_vel_gra(grd):
    df: pd.DataFrame = pygmt.grd2xyz(grd)  # pyright: ignore
    dfx = df.x.unique()
    xmin = df.x.min()
    df["x"] = (df["x"] - xmin) * 111
    z_matrix = df.pivot(index="y", columns="x", values="z").to_numpy()
    gra = np.gradient(z_matrix, axis=0)
    gra_df = pd.DataFrame(gra, index=df.y.unique(), columns=df.x.unique())
    deps = gra_df.idxmax()
    return pd.DataFrame({"x": dfx, "y": deps})
