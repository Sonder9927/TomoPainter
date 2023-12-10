from ctypes import ArgumentError
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError


class DataQueryer:
    def __init__(self, dbfile) -> None:
        self.dbf = Path(dbfile)
        self.scripts = Path("src/sqlscripts")
        self.conn = sqlite3.connect(self.dbf)
        self._per_dep()

    def phase(self, method: str, period: int, col: str) -> pd.DataFrame:
        if period not in self.periods:
            raise ArgumentError(f"argument {period} is out of range.")
        return self.query(
            "phase", usecols=[col], where=[f"{method=}", f"{period=}"]
        )

    def swave(self, col, *, depth=None) -> pd.DataFrame:
        where = None if depth is None else [f"{depth=}"]
        return self.query("swave", usecols=[col], where=where)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.commit()
        self.conn.close()

    def init_database(self, data_dir, region, spacing=0.5) -> None:
        """initilize data by SQL"""
        if self.dbf.exists():
            self.dbf.unlink()
        data = Path(data_dir)
        # re-connent
        self.conn = sqlite3.connect(self.dbf)
        _conn_write_data(self.conn, data, region, spacing, self.scripts)
        self._per_dep()

    def query(
        self,
        table: str,
        *,
        usecols: None | list[str] = None,
        avecols: None | list[str] = None,
        where: None | list[str] = None,
        ave: bool = False,
    ) -> pd.DataFrame:
        cols = None
        if usecols is not None:
            cols = ["g.x", "g.y"] + [f"t.{col}" for col in usecols]
        cols_str = "*" if cols is None else ", ".join(cols)
        sql_cmd = f"""
            SELECT {cols_str}
            FROM grid g
            JOIN {table} t
              ON g.id = t.grid_id
        """
        if where is not None:
            sql_cmd += f"WHERE {' AND '.join(where)};"
        df = pd.read_sql(sql_cmd, self.conn).dropna()
        if df.empty:
            raise EmptyDataError(
                f"""
                    DataFrame is empth with {where},
                    or cleaned all data when `.dropna()`.
                    try query with argument `usecols`.
                """
            )
        if ave:
            if usecols is None:
                raise ArgumentError("Set `usecols` if `ave` was True")
            if not avecols:
                avecols = usecols
            for col in avecols:
                avg = df[col].mean()
                df[col] = (df[col] - avg) / avg * 100
        return df

    def table_columns(self, table) -> list[str]:
        cols_info = (
            self.conn.cursor()
            .execute(f"PRAGMA table_info({table});")
            .fetchall()
        )
        return [col[1] for col in cols_info]

    def _per_dep(self):
        cursor = self.conn.cursor()
        ant = _select_distinct(cursor, "phase", "period", "method='ant'")
        tpwt = _select_distinct(cursor, "phase", "period", "method='tpwt'")
        self.periods = {"ant": ant, "tpwt": tpwt}

        # self.depths = _select_distinct(cursor, "swave", "depth")
        rj = _select_distinct(cursor, "swave", "depth", "rj_vs IS NOT NULL")
        mc = _select_distinct(cursor, "swave", "depth", "mc_vs IS NOT NULL")
        self.depths = {"rj": rj, "mc": mc}

    # def test_query(self, table):
    #     return pd.read_sql(f"select *\nfrom {table}", self.conn)


def _conn_write_data(conn, data, region, spacing, scripts):
    cursor = conn.cursor()
    # create tables and set on foreign key
    with open(scripts / "create_tables.sql", "rt") as f:
        create_tables = f.read()
    cursor.executescript(create_tables)
    # create phase table with different dcheck
    # which we'd better dont know before execute `rglob("dcheck")`
    dchecks = sorted([dd.name for dd in data.rglob(r"dcheck*/")])
    create_phase_sql = f"""
        CREATE TABLE phase (
          -- id INT PRIMARY KEY,
          grid_id INT,
          method VARCHAR(4),
          period INT,
          vel FLOAT,
          std FLOAT,
          {', '.join([rf'"{dcheck}" FLOAT' for dcheck in dchecks])},
          FOREIGN KEY (grid_id) REFERENCES grid(id)
        );
    """
    cursor.execute(create_phase_sql)

    # write data into tables
    args = {"con": conn, "index": False, "if_exists": "append"}
    # write main table `grids(id,x,y)`
    grid_df = _grid_df(region, spacing)
    grid_df.to_sql("grid", **args)
    phase_df = _phase_df(data, grid_df)
    _check_columns(cursor, "phase", phase_df).to_sql("phase", **args)
    swave_df = _swave_df(data, grid_df)
    _check_columns(cursor, "swave", swave_df).to_sql("swave", **args)
    vs_df = swave_df[["grid_id", "depth", "mc_vs"]]
    vs_df = vs_df.dropna()
    vs_df.columns = ["id", "depth", "vs"]
    lab = calc_lab(vs_df)
    model_df = _model_df(data, grid_df)
    # lab = pd.DataFrame({"grid_id": [1, 2], "lab": [2.2, 3.3]})
    model_df = model_df.merge(lab, on=["grid_id"], how="left")
    _check_columns(cursor, "model", model_df).to_sql("model", **args)
    # table_funcs = {"model": _model_df, "phase": _phase_df, "swave": _swave_df}
    # for tb, fn in table_funcs.items():
    #     _check_columns(cursor, tb, fn(data, grid_df)).to_sql(tb, **args)


def _grid_df(region, spacing) -> pd.DataFrame:
    nodes = [
        [x, y]
        for x in np.arange(region[0], region[1] + spacing, spacing)
        for y in np.arange(region[2], region[3] + spacing, spacing)
    ]
    grid_df = pd.DataFrame(data=nodes, columns=["x", "y"])
    grid_df["id"] = range(len(nodes))
    return grid_df


def _check_columns(cursor, table, df: None | pd.DataFrame) -> pd.DataFrame:
    cols_info = cursor.execute(f"PRAGMA table_info({table});").fetchall()
    target = {col[1] for col in cols_info}
    if df is None:
        return pd.DataFrame(columns=list(target))
    df_cols = set(df.columns)
    for col in target - df_cols:
        df[col] = None
    return df.drop(columns=list(df_cols - target))


def _model_df(gdir: Path, gdf) -> pd.DataFrame:
    """write subtable model(id,sed,rf_moho,mc_moho)"""
    from tomopainter.tomo_paint.gmt import tomo_grid

    rgn = [gdf["x"].min(), gdf["x"].max(), gdf["y"].min(), gdf["y"].max()]
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
    po = tomo_grid(po, rgn)

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
    return model_df


def _model_df_test(gdir: Path, gdf) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "sedthk": [1, 1],
            "rf_moho": [34.1, 35.2],
            "poisson": [1.5, 1.7],
            "mc_misfit": [0.2, 0.52],
            "mc_moho": [34, 35],
        }
    )


def _phase_df(gdir: Path, gdf) -> None | pd.DataFrame:
    phase_df = None
    for mdir in gdir.glob("*/"):
        # data of per method
        method = mdir.name
        dfs = {}
        for gf in mdir.rglob("*.grid"):
            [mtd, idt, period] = gf.stem.split("_")
            if mtd != method:
                raise FileNotFoundError(f"In {method} dir find {mtd}_*.")
            df = pd.read_csv(
                gf, header=None, delim_whitespace=True, names=["x", "y", idt]
            )
            df = gdf.merge(df, on=["x", "y"], how="left")
            df["period"] = period
            df = df[["id", "period", idt]]
            dfs[idt] = pd.concat([dfs[idt], df]) if idt in dfs else df
        # merge all idt dfs of the method
        method_df = None
        for df in dfs.values():
            method_df = (
                df
                if method_df is None
                else method_df.merge(df, on=["id", "period"], how="outer")
            )
        if method_df is None:
            continue
        method_df["method"] = method
        method_df.rename(columns={"id": "grid_id"}, inplace=True)
        # concat all method dfs
        phase_df = (
            method_df if phase_df is None else pd.concat([phase_df, method_df])
        )
    if phase_df is not None:
        phase_df.sort_values(by=["method", "period", "grid_id"], inplace=True)
    return phase_df


def _test_phase_df(gdir: Path, gdf) -> None | pd.DataFrame:
    # return None
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "period": [20, 25],
            "method": ["tpwt", "ant"],
            "velocity": [3.4, 3.5],
            "std": [3.3, 3.2],
            "dcheck1.5": [3.4, 3.4],
        }
    )


def _swave_df(gdir, gdf):
    swave_df = None
    for vsf in gdir.glob("*vs.csv"):
        df = pd.read_csv(vsf)
        df = df.merge(gdf, on=["x", "y"], how="left")
        df["depth"] = abs(df["depth"])
        df = df.drop(columns=["x", "y"])
        df.rename(
            columns={"id": "grid_id", "velocity": vsf.stem}, inplace=True
        )
        swave_df = (
            df
            if swave_df is None
            else swave_df.merge(df, on=["grid_id", "depth"], how="outer")
        )
    if swave_df is not None:
        swave_df.sort_values(by=["grid_id", "depth"], inplace=True)
    return swave_df


def _test_swave_df(gdir: Path, gdf) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grid_id": [0, 1],
            "depth": [20, 25],
            "velocity": [3.4, 3.5],
            "method": ["tpwt", "ant"],
        }
    )


def _select_distinct(cursor, table, target, where: str) -> list:
    if cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
    ).fetchone():
        rows = cursor.execute(
            f"SELECT DISTINCT {target} FROM {table} WHERE {where};"
        ).fetchall()
        return sorted([row[0] for row in rows])
    else:
        return []


def xyz_ave(df):
    avg = df["z"].mean()
    df["z"] = (df["z"] - avg) / avg * 100
    return df


def calc_lab(vs, limits=None):
    limits = limits or [54, 200]
    df = vs[(vs["depth"] > limits[0]) & (vs["depth"] < limits[1])]
    lab_df = df.groupby("id").apply(_max_nagative_gradient)
    lab_df.dropna().reset_index(drop=True)
    lab_df["grid_id"] = lab_df["id"].apply(lambda i: int(i))
    lab_df.rename(columns={"depth": "lab"}, inplace=True)
    return lab_df[["grid_id", "lab"]]


def _max_nagative_gradient(group):
    group["gra"] = np.gradient(group["vs"], group["depth"])
    max_idx = group["gra"].idxmin() if any(group["gra"] < 0) else None
    return group.loc[max_idx, ["id", "depth"]] if max_idx is not None else None
