# src/io_lob.py
from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import numpy as np


PX_COLS = [f"a{k}_p" for k in range(1, 6)] + [f"b{k}_p" for k in range(1, 6)]
VOL_COLS = [f"a{k}_v" for k in range(1, 6)] + [f"b{k}_v" for k in range(1, 6)]
BASE_COLS = ["code", "date", "time", "current", "volume", "money"]
OPTIONAL_COLS = ["maybe_truncated"]

REQUIRED_COLS = BASE_COLS + PX_COLS + VOL_COLS

def _clean_time_to_digits(s: pd.Series) -> pd.Series:
    # time 可能是 float(20210324093000.0)，也可能带非数字
    x = s.astype(str)
    x = x.str.replace(".0", "", regex=False)
    x = x.str.replace(r"\D+", "", regex=True)
    return x

def _parse_ts(df: pd.DataFrame) -> pd.Series:
    """
    兼容两类常见格式：
    1) time = YYYYMMDDHHMMSS  (14位)
    2) time = YYYYMMDDHHMMSSfff (17位，毫秒3位) => 补成6位微秒解析
    若 time 不是这两类，则 fallback: 用 date + (time当作HHMMSS 或 HHMMSSfff) —— 但你这份看起来是第一类。
    """
    t = _clean_time_to_digits(df["time"])

    # 优先：如果已经是带日期的14/17位
    lens = t.str.len()
    ts = pd.Series(pd.NaT, index=df.index)

    mask14 = lens == 14
    if mask14.any():
        ts.loc[mask14] = pd.to_datetime(t.loc[mask14], format="%Y%m%d%H%M%S", errors="coerce")

    mask17 = lens == 17
    if mask17.any():
        # 补成微秒6位：fff -> fff000
        t17 = t.loc[mask17].str.cat(["000"] * mask17.sum())
        ts.loc[mask17] = pd.to_datetime(t17, format="%Y%m%d%H%M%S%f", errors="coerce")

    # fallback：time不是14/17位时，用 date + time(HHMMSS…)
    rest = ts.isna()
    if rest.any():
        d = df.loc[rest, "date"].astype(str).str.replace(r"\D+", "", regex=True)
        tt = t.loc[rest]
        # 常见：HHMMSS(6) 或 HHMMSSfff(9)
        tt = tt.str.zfill(6)
        comb = d + tt
        # 如果 comb 是 14 位 => YYYYMMDDHHMMSS
        ts.loc[rest] = pd.to_datetime(comb, format="%Y%m%d%H%M%S", errors="coerce")

    return ts


def read_raw_lob_csv(path: Path, default_symbol: str | None = None, default_date: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, compression="gzip")
    df.columns = [c.strip().lower() for c in df.columns]

    # ---- 关键：如果缺 code/date，用路径信息补 ----
    if "code" not in df.columns:
        if default_symbol is None:
            raise ValueError(f"Missing 'code' in {path.name} and no default_symbol provided")
        df.insert(0, "code", default_symbol)

    if "date" not in df.columns:
        if default_date is None:
            raise ValueError(f"Missing 'date' in {path.name} and no default_date provided")
        df.insert(1, "date", default_date)

    # ---- 现在再做 required columns 检查（但 code/date 已经兜住）----
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path.name}: {missing}")

    df["code"] = df["code"].astype(str)
    df["date"] = df["date"].astype(str)

    ts = _parse_ts(df)
    if ts.isna().any():
        bad = int(ts.isna().sum())
        raise ValueError(f"Unparsed timestamps: {bad} rows in {path}")

    df.insert(0, "ts", ts)
    df = df.sort_values("ts", kind="mergesort")

    num_cols = ["current", "volume", "money"] + PX_COLS + VOL_COLS
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if "maybe_truncated" not in df.columns:
        df["maybe_truncated"] = np.nan
    
    px_cols = [f"a{k}_p" for k in range(1, 6)] + [f"b{k}_p" for k in range(1, 6)]
    valid = df[px_cols].notna().all(axis=1) & (df[px_cols] > 0).all(axis=1)
    df = df.loc[valid].copy()

    return df



def raw_path(root: Path, year: int, symbol: str, date_str: str) -> Path:
    return root / str(year) / symbol / f"{date_str}.csv.gz"


def processed_path(root: Path, symbol: str, date_str: str) -> Path:
    return root / "ticks" / symbol / date_str / "part.parquet"

def convert_one_day(raw_file: Path, processed_root: Path) -> Path:
    # raw_file: .../raw_ticks/2021/159915.XSHE/2021-01-04.csv.gz
    symbol = raw_file.parent.name                      # 159915.XSHE
    date_str = raw_file.stem.split(".")[0]             # 2021-01-04  (stem: "2021-01-04.csv")
    # 注意：你的文件名是 2021-01-04.csv.gz，所以 stem 是 "2021-01-04.csv"
    # split(".")[0] 才能拿到 2021-01-04

    df = read_raw_lob_csv(raw_file, default_symbol=symbol, default_date=date_str)

    # 这里用兜底后的字段
    symbol = df["code"].iloc[0]
    date_str = df["date"].iloc[0]

    out = processed_path(processed_root, symbol, date_str)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out

