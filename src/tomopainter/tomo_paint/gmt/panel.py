import pandas as pd
import pygmt

from .gmt_make_data import makecpt


def vpanel_makecpt(dep, ccrust: str, clithos, cVave):
    # crust
    makecpt([3.2, 4, 0.1], ccrust, cmap="jet", reverse=True)
    # lithos
    # makecpt([4.43 - 0.25, 4.43 + 0.17, 0.03], clithos, cpt="cbcRdYlBu.cpt")
    if dep < 90:
        makecpt([4.2, 4.5, 0.03], clithos, cmap="jet", reverse=True)
    else:
        makecpt([4.2, 4.6, 0.03], clithos, cmap="jet", reverse=True)
    # ave
    makecpt([-4, 4, 0.05], cVave, cmap="jet", reverse=True)


def vpanel_clip_data(grid, border, region):
    from tomopainter.rose import points_inner

    # read grid data and cut into parts
    data: pd.DataFrame = pygmt.grd2xyz(grid=grid)  # pyright: ignore
    bbot, bup = border["y"].min(), border["y"].max()
    data_whole = data[data["y"] > bbot]
    data_upon = data_whole[data_whole["y"] >= bup]
    data_around = data_whole[data_whole["y"] < bup]
    # make clip boundary
    df1 = pd.DataFrame({"x": [region[0]], "y": [region[-1]]})
    df2 = pd.DataFrame({"x": [region[1]], "y": [region[-1]]})
    df_border = pd.concat([df1, border, df2], ignore_index=True)
    # clip
    data_inner = points_inner(data_around, df_border)
    # concat data
    data_upon = pd.concat([data_upon, data_inner], ignore_index=True)
    data_upon = data_upon.sort_values(by=["x", "y"]).reset_index(drop=True)
    region_upon = region.copy()
    region_upon[-2] = bbot
    return pygmt.xyz2grd(data=data_upon, region=region_upon, spacing=0.01)
