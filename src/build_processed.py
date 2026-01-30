# src/build_processed.py
from __future__ import annotations
from pathlib import Path
import argparse
from src.io_lob import convert_one_day, processed_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_root", type=str, default="data/raw/ticks")
    ap.add_argument("--processed_root", type=str, default="data/processed")
    ap.add_argument("--symbol", type=str, default="ALL")   # ALL 或 159915.XSHE
    ap.add_argument("--year", type=str, default="ALL")     # ALL 或 2021 或 2021,2022
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    raw_root = Path(args.raw_root)
    processed_root = Path(args.processed_root)

    # years 列表
    if args.year == "ALL":
        years = sorted([p.name for p in raw_root.iterdir() if p.is_dir()])
    else:
        years = [y.strip() for y in args.year.split(",")]

    total = 0
    skipped = 0
    failed = 0

    for y in years:
        year_dir = raw_root / str(y)
        if not year_dir.exists():
            continue

        # symbols 列表
        if args.symbol == "ALL":
            symbols = sorted([p.name for p in year_dir.iterdir() if p.is_dir()])
        else:
            symbols = [args.symbol]

        for sym in symbols:
            sym_dir = year_dir / sym
            if not sym_dir.exists():
                continue

            files = sorted(sym_dir.glob("*.csv.gz"))
            if not files:
                continue

            for f in files:
                date_str = f.stem.split(".")[0]  # 2021-01-04
                out = processed_path(processed_root, sym, date_str)
                if out.exists() and (not args.overwrite):
                    skipped += 1
                    continue
                try:
                    convert_one_day(f, processed_root)
                    total += 1
                    if total % 200 == 0:
                        print(f"[OK {total}] (skipped={skipped}, failed={failed}) last={sym} {date_str}")
                except Exception as e:
                    failed += 1
                    print(f"[FAIL] {f} -> {e}")

    print(f"Done. OK={total}, skipped={skipped}, failed={failed}")

if __name__ == "__main__":
    main()
