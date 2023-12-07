import sqlite3
from pathlib import Path
import pandas as pd


def main():
    target = Path("test.db")
    if target.exists():
        target.unlink()
    sc = "src/sqlscripts/create_tables.sql"
    with open(sc, "rt") as f:
        src = f.read()
    with sqlite3.connect(target) as conn:
        conn.executescript(src)
        conn.execute("insert into grid values (0,1,1)")
        conn.execute("insert into grid values (1,1,2)")
        conn.execute("insert into model values (0,1,2,3,4)")
        conn.execute("insert into model values (1,1.1,2.2,3.3,4.4)")
        try:
            conn.execute("insert into model values (2,1.1,2.2,3.3,4.4)")
        except sqlite3.IntegrityError as e:
            print("Error:")
            print(e)
        model_df = pd.read_sql("select * from model", conn)
        conn.execute("insert into swave values (0,'tpwt',10,3)")
        swave_df = pd.read_sql("select * from swave", conn)
    print(model_df)
    print(swave_df)


if __name__ == "__main__":
    main()
