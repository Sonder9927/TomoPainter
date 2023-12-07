from pathlib import Path

import pandas as pd
import pygmt
from tomopainter.tomo_paint.gmt.gmt_make_data import make_topos, makecpt


def test_plot_age():
    region = [115, 122.5, 27.9, 34.3]
    area = make_topos("ETOPO1", region, cmap="geo")
    fn = "temp/temp.png"

    fig = pygmt.Figure()
    fig = test_fig_tomos(fig, area)
    cpt = area["cpt"]
    fig.colorbar(cmap=cpt, frame=["a", "x+lElevation", "y+lm"])
    fig.savefig(fn)


def test_fig_tomos(fig, topo):
    # basemap and topo
    # projection
    x = (topo["region"][0] + topo["region"][1]) / 2
    y = (topo["region"][2] + topo["region"][3]) / 2
    projection = f"m{x}/{y}/0.3i"
    fig.basemap(region=topo["region"], projection=projection, frame="a")

    # plot tects and elements like sta basalt colcano
    fig = test_fig_tect_and_sta(fig, 0)

    return fig


def test_fig_tect_and_sta(fig, tect):
    txt = Path("data/txt")
    fig.coast(shorelines="1/0.5p,black")
    # basalts
    basalts = pd.read_csv(txt / "tects/China_basalts_data.csv")
    # filter by age
    basalts = basalts[basalts["age"] < 10]
    cc = makecpt([0, 10], cmap="hot", reverse=True)
    fig.plot(data=basalts[["x", "y", "age"]], style="c0.2c", cmap=cc)
    fig.colorbar(cmap=cc, position="JMR+w4c/0.2c+o0.5c/0c", frame="a")

    # plot volcano
    # nushan
    fig.plot(x=118.09, y=32.8, style="ksquaroid/0.4c", fill="magenta")
    # xinchang
    fig.plot(x=120.88, y=29.5, style="ksquaroid/0.4c", fill="magenta")
    # # xilong
    # fig.plot(x=119.44, y=30.45, style="ksquaroid/0.4c", fill="magenta")

    # # stations
    # stas = pd.read_csv(txt / "station.csv", usecols=[1, 2])
    # fig.plot(data=stas, style="t0.15c", fill="darkblue")

    # tectonics
    geo_data = ["China_tectonic.dat", "CN-faults.gmt", "find.gmt"]
    tect_pens = ["1p,black,-", "0.5p,black,-"]
    fig.plot(data=txt / f"tects/{geo_data[tect]}", pen=tect_pens[0])
    fig.plot(data=txt / "tects/small_faults.gmt", pen=tect_pens[1])
    # fig.plot(data="data/txt/tects/small_faults_finding.gmt", pen="red,-")
    return fig


if __name__ == "__main__":
    test_plot_age()
