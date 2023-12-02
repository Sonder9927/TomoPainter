# Author: Sonder Merak
# Version: 0.2
# Description: plot diff between tpwt and ant results.


import pandas as pd
import pygmt

from .gmt_fig import fig_tomos
from .gmt_make_data import area_clip, diff_make, make_topos


def gmt_plot_diff(diff: pd.DataFrame, grds, region, cpt, fname, eles):
    topo = make_topos("ETOPO1", region)
    diff = area_clip(diff)["z"]
    # gmt plot
    fig = pygmt.Figure()
    # define figure configuration
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
    )
    per = fname.stem.split("_")[-1]
    with fig.subplot(
        nrows=2,
        ncols=2,
        figsize=("15c", "14.5c"),
        autolabel=True,
        margins="0.5c/0.3c",
        title=f"{per}s deference",
    ):
        kws = {"projection": "M?"}
        kws |= eles
        # ant
        with fig.set_panel(panel=0):
            tomo = {"grid": grds["ant"], "cmap": cpt}
            fig = fig_tomos(fig, topo, [tomo], **kws)
            fig.text(
                x=region[1],
                y=region[-1],
                fill="white",
                justify="RT",
                font="15p",
                text="ANT",
                offset="j0.1",
            )
        # tpwt
        with fig.set_panel(panel=1):
            tomo["grid"] = grds["tpwt"]
            fig = fig_tomos(fig, topo, [tomo], **kws)
            fig.text(
                x=region[1],
                y=region[-1],
                fill="white",
                justify="RT",
                font="15p",
                text="TPWT",
                offset="j0.1",
            )
            fig.colorbar(
                cmap=cpt, position="JMR+w6c/0.4c+o0.5c/0c", frame="xa0.05f0.05"
            )
        # diff
        with fig.set_panel(panel=2):
            cdf = "data/txt/cptfiles/vs_dif.cpt"
            tomo = {"grid": grds["diff"], "cmap": cdf}
            kws["sta"] = None
            fig = fig_tomos(fig, topo, [tomo], **kws)
        # statistics
        with fig.set_panel(panel=3):
            fig.histogram(
                data=diff,
                projection="X?",
                region=[-150, 150, 0, 30],
                series=[-150, 150, 20],
                cmap=cdf,
                histtype=1,  # for frequency percent
                pen="1p,black",
            )
            fig.text(
                x=150,
                y=30,
                justify="RT",
                font="12.5p",
                text=f"mean={round(diff.mean(),2)}m/s",
                offset="j0.1",
            )
            fig.text(
                x=150,
                y=28,
                justify="RT",
                font="12p",
                text=f"std = {round(diff.std(),2)}m/s",
                offset="j0.1",
            )
            fig.colorbar(
                cmap=cdf, position="JMR+o0.5c/0c+w6c/0.4c", frame="xa50f50"
            )

            # per = Path(grds["tpwt"]).stem.split("_")[-1]
            # use "X?" as projection
    # vel colorbar
    # fig.shift_origin(yshift="9c")
    # fig.colorbar(cmap=cpt, position="jBC+w8c/0.4c+o0c/-1.5c+m", frame="xa")
    fig.savefig(str(fname))


def plot_diff(grid_ant, grid_tpwt, region, fig_name, eles):
    # cpt file
    cpt = "temp/tomo.cpt"
    # grd file
    grds = {
        "ant": "temp/vel_ant.grd",
        "tpwt": "temp/vel_tpwt.grd",
        "diff": "temp/vel_diff.grd",
    }

    diff = diff_make(grid_ant, grid_tpwt, region, cpt, grds)
    gmt_plot_diff(diff, grds, region, cpt, fig_name, eles)
