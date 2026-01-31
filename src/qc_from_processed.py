# src/qc_from_processed.py
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

PX_COLS = [f"a{k}_p" for k in range(1, 6)] + [f"b{k}_p" for k in range(1, 6)]

def qc_one_parquet(pq: Path) -> dict:
    df = pd.read_parquet(pq)

    symbol = str(df["code"].iloc[0])
    date_str = str(df["date"].iloc[0])
    n = len(df)

    dup_ratio = df["ts"].duplicated().mean()

    a1 = df["a1_p"]
    b1 = df["b1_p"]
    crossed_ratio = (a1 <= b1).mean()

    px = df[PX_COLS]
    bad_price_cnt = int(((px <= 0) | px.isna()).any(axis=1).sum())

    mid = (a1 + b1) / 2.0
    spread = a1 - b1
    spread_median = float(np.nanmedian(spread))
    rel_spread_median = float(np.nanmedian(spread / mid))

    mt_ratio = float(np.nanmean(pd.to_numeric(df.get("maybe_truncated", np.nan), errors="coerce") > 0))

    return {
        "symbol": symbol,
        "date": date_str,
        "n_rows": n,
        "dup_ts_ratio": float(dup_ratio),
        "crossed_ratio": float(crossed_ratio),
        "bad_price_cnt": bad_price_cnt,
        "spread_median": spread_median,
        "rel_spread_median": rel_spread_median,
        "maybe_truncated_ratio": mt_ratio,
        "ts_min": df["ts"].min(),
        "ts_max": df["ts"].max(),
        "file": str(pq),
    }

def main():
    processed_root = Path("data/processed/ticks")
    out_file = Path("data/features/qc_all.parquet")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    parts = sorted(processed_root.glob("*/*/part.parquet"))
    rows = []
    for i, pq in enumerate(parts, 1):
        try:
            rows.append(qc_one_parquet(pq))
        except Exception as e:
            print(f"[FAIL] {pq} -> {e}")
        if i % 500 == 0:
            print(f"[{i}/{len(parts)}] qc running...")

    qc = pd.DataFrame(rows).sort_values(["symbol", "date"])
    qc.to_parquet(out_file, index=False)
    print(f"Saved: {out_file} rows={len(qc)}")

if __name__ == "__main__":
    main()
