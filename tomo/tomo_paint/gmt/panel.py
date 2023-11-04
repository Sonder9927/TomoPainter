import pandas as pd
import pygmt

from .gmt_make_data import makecpt


def vpanel_makecpt(ccrust: str, clithos, cVave):
    # crust
    makecpt([3, 4, 0.05], ccrust)
    # lithos
    makecpt([4.32 - 0.15, 4.32 + 0.2, 0.01], clithos)
    # ave
    makecpt([-4, 4, 0.05], cVave)


def vpanel_clip_data(grid, border, region):
    from tomo.rose import points_inner

    # read grid data and cut into parts
    data: pd.DataFrame = pygmt.grd2xyz(grid=grid)  # pyright: ignore
    bbot, bup = border["y"].min(), border["y"].max()
    data_whole = data[data["y"] > bbot]
    data_upon = data_whole[data_whole["y"] >= bup]
    data_around = data_whole[data_whole["y"] < bup]
    # make clip boundary
    df1 = pd.DataFrame({"x": [region[0]], "y": [region[-1]]})
    df2 = pd.DataFrame({"x": [region[1]], "y": [region[-1]]})
    boundary = pd.concat([df1, border, df2], ignore_index=True)
    # clip
    data_inner = points_inner(data_around, boundary=boundary.to_numpy())
    # concat data
    data_upon = pd.concat([data_upon, data_inner], ignore_index=True)
    data_upon = data_upon.sort_values(by=["x", "y"]).reset_index(drop=True)
    region_upon = region.copy()
    region_upon[-2] = bbot
    return pygmt.xyz2grd(data=data_upon, region=region_upon, spacing=0.01)
