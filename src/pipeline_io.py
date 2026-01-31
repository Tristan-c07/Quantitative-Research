from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, Optional, List
import pandas as pd
import yaml


@dataclass(frozen=True)
class DataConfig:
    processed_dir: Path
    raw_dir: Path
    universe_file: Path
    start: str
    end: str

@dataclass(frozen=True)
class OfiConfig:
    levels: int
    bar: str
    agg: str
    output_dir: Path
    overwrite: bool

@dataclass(frozen=True)
class Config:
    data: DataConfig
    ofi: OfiConfig


def load_config(path: str | os.PathLike) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)

    data = y["data"]
    feat = y["feature"]["ofi"]

    return Config(
        data=DataConfig(
            processed_dir=Path(data["processed_dir"]),
            raw_dir=Path(data["raw_dir"]),
            universe_file=Path(data["universe_file"]),
            start=data["start"],
            end=data["end"],
        ),
        ofi=OfiConfig(
            levels=int(feat["levels"]),
            bar=str(feat["bar"]),
            agg=str(feat["agg"]),
            output_dir=Path(feat["output_dir"]),
            overwrite=bool(feat.get("overwrite", False)),
        ),
    )


def load_universe(universe_file: Path) -> List[str]:
    content = yaml.safe_load(universe_file.read_text(encoding="utf-8"))
    
    # 提取品种列表
    if isinstance(content, dict) and "universe" in content:
        syms = content["universe"]
    elif isinstance(content, list):
        syms = content
    else:
        raise ValueError(f"Expected 'universe' key or list in {universe_file}")
    
    # 清洗并返回
    syms = [s.strip() for s in syms if isinstance(s, str) and s.strip()]
    return sorted(list(dict.fromkeys(syms)))


def iter_daily_files(
    processed_dir: Path, raw_dir: Path, symbol: str, start: str, end: str
) -> Iterable[Tuple[str, str, Path, str]]:
    pdir = processed_dir / symbol
    rdir = raw_dir / symbol

    candidates = []
    
    # 处理 processed 数据：支持两种格式
    # 1. symbol/date.parquet
    # 2. symbol/date/part.parquet
    if pdir.exists():
        # 直接文件格式
        candidates += [(p, "processed") for p in pdir.glob("*.parquet")]
        # 目录格式
        for date_dir in pdir.iterdir():
            if date_dir.is_dir():
                parquet_file = date_dir / "part.parquet"
                if parquet_file.exists():
                    candidates.append((parquet_file, "processed"))
    
    # 处理 raw 数据：支持两种格式
    # 1. symbol/date.csv.gz
    # 2. symbol/date/part.csv.gz
    if rdir.exists():
        # 直接文件格式
        candidates += [(p, "raw") for p in rdir.glob("*.csv.gz")]
        # 目录格式
        for date_dir in rdir.iterdir():
            if date_dir.is_dir():
                csv_file = date_dir / "part.csv.gz"
                if csv_file.exists():
                    candidates.append((csv_file, "raw"))

    for p, src in sorted(candidates, key=lambda x: x[0].name):
        # 从路径中提取日期：优先从父目录名获取
        if p.parent.name != symbol:
            date = p.parent.name
        else:
            date = p.stem.replace(".csv", "")
        
        if start <= date <= end:
            yield symbol, date, p, src
