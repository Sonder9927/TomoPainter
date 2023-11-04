import json
from pathlib import Path

from icecream import ic
import numpy as np
import pandas as pd
import pygmt

from .grid import GridPhv
from .points import points_boundary, points_inner

# from tpwt_r import Point


def read_xyz(file: Path) -> pd.DataFrame:
    return pd.read_csv(
        file, delim_whitespace=True, usecols=[0, 1, 2], names=["x", "y", "z"]
    )


def vel_info_per(data_file: Path, points: list) -> dict:
    data = read_xyz(data_file)
    data_inner = points_inner(data, points)

    # sourcery skip: inline-immediately-returned-variable
    grid_per = {
        "vel_avg": data_inner.z.mean(),
        "vel_max": data_inner.z.max(),
        "vel_min": data_inner.z.min()
        # "inner_num": len(data_inner.index)
    }

    return grid_per


def standard_deviation_per(ant: Path, tpwt: Path, region, stas) -> float:
    from src.pygmt_plot.gmt import gmt_blockmean_surface_grdsample

    temp = "temp/temp.grd"
    gmt_blockmean_surface_grdsample(ant, temp, temp, region)
    ant_xyz = pygmt.grd2xyz(temp)
    gmt_blockmean_surface_grdsample(tpwt, temp, temp, region)
    tpwt_xyz = pygmt.grd2xyz(temp)
    if ant_xyz is None or tpwt_xyz is None:
        raise ValueError(
            f"""
            Cannot calculate standard deviation with \n
            ant: {ant}\n
            and\n
            tpwt: {tpwt}
            """
        )

    # make diff
    diff = tpwt_xyz
    diff["z"] = (tpwt_xyz["z"] - ant_xyz["z"]) * 1000  # 0.5 X 0.5 grid

    boundary = points_boundary(stas)
    data_inner = points_inner(diff, boundary=boundary)
    std = data_inner.z.std(ddof=0)

    return std


def vel_info(target: str, periods=None):
    region = [115, 122.5, 27.9, 34.3]
    sta_file = "src/txt/station.lst"
    stas = pd.read_csv(
        sta_file, delim_whitespace=True, usecols=[1, 2], names=["x", "y"]
    )
    boundary = points_boundary(stas[["x", "y"]], region)  # default is clock
    # po = clock_sorted(boundary_points)  # no need

    gd = Path("grids")
    if periods is None:
        pg = gd.glob("*t_grids/*.grid")
        periods = sorted(list({int(i.stem.split("_")[-1]) for i in pg}))

    gps = [GridPhv(per) for per in periods]
    jsd = {}
    for gp in gps:
        ant = gp.grid_file("ant", "vel")
        tpwt = gp.grid_file("tpwt", "vel")

        ant_info = vel_info_per(ant, boundary) if ant is not None else {}
        tpwt_info = vel_info_per(tpwt, boundary) if tpwt is not None else {}

        js_per = {}

        ic.disable()
        if all([ant, tpwt]):
            vel_avg_diff = abs(ant_info["vel_avg"] - tpwt_info["vel_avg"])
            vel_avg_diff = "{:.2f} m/s".format(vel_avg_diff * 1000)
            js_per["avg_diff"] = vel_avg_diff
            st = standard_deviation_per(ant, tpwt, region, stas)
            vel_standart_deviation = "{:.2f} m/s".format(st)
            js_per["standard_deviation"] = vel_standart_deviation
            ic(gp.period, vel_avg_diff, vel_standart_deviation)
        else:
            ic(gp.period, "Data info lacked.")
        js_per |= {"ant": ant_info, "tpwt": tpwt_info}

        jsd[str(gp.period)] = js_per

    with open(target, "w+", encoding="UTF-8") as f:
        json.dump(jsd, f)


def calc_lab(vs, mm, mlf, limits: list):
    data = vs.merge(mm[["x", "y", "moho"]], on=["x", "y"], how="left")
    data["moho"] = -data["moho"]
    df = data[(data["z"] < limits[0]) & (data["z"] > limits[1])]
    dt = df.groupby(["x", "y"], group_keys=False).apply(_gradient)
    result = (
        dt.groupby(["x", "y"])
        .apply(_target_gra)
        .dropna()
        .reset_index(drop=True)
    )
    result.rename(columns={"z": "lab"}, inplace=True)
    lab_range = [result["lab"].min(), result["lab"].max()]
    ic(lab_range)
    result.to_csv(mlf, index=None)


def _gradient(group):
    group["gra"] = np.gradient(group["v"], group["z"])
    return group


def _target_gra(group):
    max_idx = group["gra"].idxmax() if any(group["gra"] < 0) else None
    return (
        group.loc[max_idx, ["x", "y", "moho", "z"]]
        if max_idx is not None
        else None
    )
