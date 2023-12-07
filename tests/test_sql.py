from pathlib import Path

from icecream import ic
import pandas as pd

from tomopainter.tomo_paint.gmt import tomo_grid
from tomopainter.rose import DataQueryer


def test_model_df(gdf, rgn) -> pd.DataFrame:
    gdir = Path("data/grids")
    # collect data
    # sed data
    sed = pd.read_csv(gdir / "sedthk.xyz", delim_whitespace=True, header=None)
    sed = tomo_grid(sed, rgn).clip(lower=0)

    # receive function moho
    rf = pd.read_csv(
        gdir / "rf_moho.lst",
        delim_whitespace=True,
        usecols=[0, 1, 2],
        header=None,
    )
    rf.iloc[:, 0], rf.iloc[:, 1] = rf.iloc[:, 1].copy(), rf.iloc[:, 0].copy()
    rf = tomo_grid(rf, rgn)

    # merge poisson
    po = pd.read_csv(
        gdir / "input_vpvs.lst", delim_whitespace=True, header=None
    )
    po = tomo_grid(rf, rgn)

    # merge mcmc misfit & moho
    mc = pd.read_csv(gdir / "mcmc_misfit_moho.csv")

    # merge data
    model_df = gdf
    position = ["x", "y"]
    for df in (sed, rf, po, mc):
        model_df = model_df.merge(df, on=position, how="left")
    model_df = model_df.drop(columns=position)
    # rename column names
    model_df.columns = [
        "grid_id",
        "sedthk",
        "rf_moho",
        "poisson",
        "mc_misfit",
        "mc_moho",
    ]
    model_df.to_csv("model.csv")
    return model_df


def test_df(region):
    with DataQueryer("data/grids.db") as sr:
        grid = sr.query("grid")
    df = test_model_df(grid, region)
    ic(df.head())


def write_db(region):
    with DataQueryer("data/grids.db") as sr:
        sr.init_database("data/grids", region=region)


def read_db():
    with DataQueryer("data/grids.db") as sr:
        df = sr.query("grid")
        ic(df.head())
        df = sr.query("model")
        ic(df.head())


if __name__ == "__main__":
    region = [115.5, 122.5, 27, 35]
    write_db(region)
    read_db()
    # test_df(region)
