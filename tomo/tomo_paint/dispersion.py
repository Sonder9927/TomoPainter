from pathlib import Path

import pandas as pd

from .gmt import plot_dispersion_curve


def gmt_plot_dispersion_curves(mmf):
    """
    plot dispersion curves of tpwt and ant
    """
    dc_periods = {
        "ant": [8, 10, 12, 14, 16, 18],
        "overlap": [20, 25, 30],
        "tpwt": [35, 40, 45, 50, 60, 70, 80, 90, 100, 111, 125, 143],
    }
    gp = Path("grids")
    merged_ant = merge_periods_data(gp, "ant", "vel")
    merged_tpwt = merge_periods_data(gp, "tpwt", "vel")
    merged_data = pd.merge(merged_ant, merged_tpwt, on=["x", "y"], how="left")
    mm = pd.read_csv(mmf)
    misfit = mm[["x", "y", "misfit"]]
    merged_data = pd.merge(merged_data, misfit, on=["x", "y"], how="left")
    # # clip
    # sta = pd.read_csv(
    #     r"src/txt/station.lst",
    #     usecols=[1, 2],
    #     index_col=None,
    #     header=None,
    #     delim_whitespace=True,
    # )
    # boundary = info_filter.points_boundary(sta, region)
    # merged_inner = info_filter.points_inner(merged_data, boundary=boundary)
    merged_inner = merged_data[
        (merged_data["x"] == 122.0) & (merged_data["y"] == 32.5)
    ]
    save_path = Path("images") / "dispersion_curves"
    if not save_path.exists():
        save_path.mkdir()
    for _, vs in merged_inner.iterrows():
        plot_dispersion_curve(vs.to_dict(), dc_periods, save_path)


def merge_periods_data(gp: Path, method: str, idt: str):
    merged_data = None
    for f in gp.glob(f"{method}_grids/*{idt}*"):
        per = f.stem.split("_")[-1]
        col_name = f"{method}_{per}"
        data = pd.read_csv(
            f, header=None, delim_whitespace=True, names=["x", "y", col_name]
        )
        if merged_data is None:
            merged_data = data
        else:
            merged_data = pd.merge(
                merged_data, data, on=["x", "y"], how="left"
            )
    return merged_data
