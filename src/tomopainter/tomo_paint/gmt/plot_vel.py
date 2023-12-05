import pandas as pd
import pygmt

from .gmt_fig import fig_tomos
from .gmt_make_data import area_clip, make_topos, makecpt, series, tomo_grid


def gmt_plot_vel(topo, grd, cptinfo, fname, eles):
    # gmt plot
    fig = pygmt.Figure()
    # define figure configuration
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
    )

    tomo = {"grid": grd, "cmap": cptinfo["cmap"]}
    fig = fig_tomos(fig, topo, [tomo], **eles)
    per = fname.stem.split("_")[-1]
    fig.text(
        x=topo["region"][0],
        y=topo["region"][-1],
        fill="white",
        justify="LT",
        font="9p",
        text=f"{per}s",
        offset="j0.1",
    )
    fig.colorbar(
        cmap=cptinfo["cmap"],
        position="jBC+w4.5c/0.3c+o0c/-1c+m",
        frame="xa",
    )

    fig.savefig(str(fname))


def plot_vel(grid, region, fig_name, eles, cptconfig) -> None:
    # sourcery skip: default-mutable-arg
    # position of stations
    # make vel grid and get vel grid generated by `surface`
    vel_grd = "temp/vel_tpwt.grd"
    tomo_grid(grid, region, vel_grd)

    # cpt file
    cptinfo = {"series": series(grid, method=1)}
    cptinfo |= cptconfig

    cptinfo["cmap"] = makecpt(**cptinfo)
    # make cpt file

    topo = make_topos("ETOPO1", region)

    # gmt plot
    gmt_plot_vel(topo, vel_grd, cptinfo, fig_name, eles)


def plot_as(velf, stdf, region, fn, eles) -> None:
    grd = pd.read_csv(
        velf, delim_whitespace=True, names=["x", "y", "z"], header=None
    )
    grd_clip = area_clip(grd)
    mm = grd_clip["z"].mean()
    grd["z"] = (grd["z"] - mm) / mm * 100
    vel_grd = "temp/temp_vel.grd"
    tomo_grid(grd, region, vel_grd)
    std_grd = "temp/temp_std.grd"
    tomo_grid(stdf, region, std_grd)
    # gmt plot
    gmt_plot_as(region, vel_grd, std_grd, fn, eles)


def gmt_plot_as(region, vel, std, fn, eles):
    per = fn.stem.split("_")[-1]
    topo = make_topos("ETOPO1", region)
    cpt = "temp/temp.cpt"
    fig = pygmt.Figure()
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18",
    )
    with fig.subplot(
        nrows=1, ncols=2, figsize=("15c", "8c"), autolabel=True, margins="0.5c"
    ):
        # copy eles
        kws = {"projection": "M?"}
        kws |= eles
        with fig.set_panel(panel=0):
            makecpt([-2.5, 2.5], cpt, cmap="jet", reverse=True)
            tomos = [{"grid": vel, "cmap": cpt}]
            fig = fig_tomos(fig, topo, tomos, **kws)
            fig.text(
                x=region[0],
                y=region[-1],
                fill="white",
                justify="LT",
                font="15p",
                text=f"{per}s",
                offset="j0.1",
            )
            fig.colorbar(
                frame=["a1f1", 'x+l"TPWT Phase velocity anomaly"', "y+l%"]
            )
        with fig.set_panel(panel=1):
            makecpt([0, 121], cpt, cmap="hot", reverse=True)
            tomos = [{"grid": std, "cmap": cpt}]
            kws["clip"] = False
            fig = fig_tomos(fig, topo, tomos, **kws)
            fig.colorbar(
                frame=["a20f20", 'x+l"TPWT standard deviation"', "y+lm/s"]
            )
    fig.savefig(str(fn))
