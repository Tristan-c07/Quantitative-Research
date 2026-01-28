# -*- coding: utf-8 -*-
"""
把 my_jq_strategy/strategy + my_jq_strategy/lib 打成一个 zip，供平台上传。
"""
import os, zipfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = DIST / "joinquant_strategy.zip"

INCLUDE_DIRS = ["strategy", "lib"]

def main():
    DIST.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for d in INCLUDE_DIRS:
            base = ROOT / d
            for p in base.rglob("*"):
                if p.is_file():
                    arc = p.relative_to(ROOT)
                    z.write(p, arcname=str(arc))
    print(f"OK: {OUT}")

if __name__ == "__main__":
    main()
