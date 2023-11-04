import pygmt
import numpy as np


def data_from_vs(vs: dict, pers):
    x = vs.pop("x", None)
    y = vs.pop("y", None)
    misfit = vs.pop("misfit", None)
    ant = sorted(
        [[p, vs[f"ant_{p}"]] for p in pers["ant"]]
        + [[p, vs[f"ant_{p}"]] for p in pers["overlap"]]
    )
    tpwt = sorted(
        [[p, vs[f"tpwt_{p}"]] for p in pers["tpwt"]]
        + [[p, vs[f"tpwt_{p}"]] for p in pers["overlap"]]
    )
    dc = sorted(
        [[p, vs[f"ant_{p}"]] for p in pers["ant"]]
        + [[p, vs[f"tpwt_{p}"]] for p in pers["tpwt"]]
        + [
            [p, (vs[f"ant_{p}"] + vs[f"tpwt_{p}"]) / 2]
            for p in pers["overlap"]
        ]
    )
    return x, y, misfit, {"ant": ant, "tpwt": tpwt, "dc": dc}


def plot_dispersion_curve(vs, periods, fsp) -> None:
    x, y, m, dcs = data_from_vs(vs, periods)
    x_y = f"{x:.2f}_{y:.2f}"
    fig_name = str(fsp / f"dispersion_curve_{x_y}.png")

    fig = pygmt.Figure()
    region = [0, 150, 2.9, 4.3]
    pygmt.config(
        MAP_FRAME_TYPE="plain",
        MAP_TITLE_OFFSET="0.25p",
        MAP_DEGREE_SYMBOL="none",
        FONT_TITLE="18p,1,black",
        FONT_LABEL="8p,1,black",
    )

    fig.basemap(
        region=region,
        projection="X8c/4c",
        frame=["WeSn", r'xa20f5+l"Period (Sec)"', r'ya0.5f0.1+l"Vel (km/s)"'],
    )
    # plot dc
    fig.plot(data=np.array(dcs["dc"]), pen="0.8p,red")
    fig.plot(
        data=np.array(dcs["ant"]), pen="0.3p", style="t0.15c", fill="gold"
    )
    fig.plot(
        data=np.array(dcs["tpwt"]), pen="0.3p", style="i0.15c", fill="green"
    )
    fig.text(
        text=f"External misfit({x:.1f}, {y:.2f}) = {m:.2f}",
        position="BR",
        font="10p,Helvetica-Bold",
        offset="-3p/6p",
    )

    fig.savefig(fig_name)
