"""
构建标签数据：计算每个标的每天的分钟级未来收益率
使用中间价 (a1_p + b1_p) / 2 计算
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.pipeline_io import load_config, load_universe, iter_daily_files


def compute_minute_returns(df: pd.DataFrame) -> pd.Series:
    """
    计算分钟级未来收益率
    
    Args:
        df: tick级数据，需包含 ts, a1_p, b1_p 列
        
    Returns:
        分钟级未来收益率 Series，index为minute时间
    """
    # 确保时间列是datetime类型
    if not isinstance(df['ts'], pd.DatetimeIndex):
        df['ts'] = pd.to_datetime(df['ts'])
    
    # 向下取整到分钟
    df['minute'] = df['ts'].dt.floor('min') # type: ignore
    
    # 计算每分钟最后一笔的中间价
    close = (df.groupby('minute').last()['a1_p'] + 
             df.groupby('minute').last()['b1_p']) / 2
    
    # 计算未来收益率：ret[t] = (close[t+1] - close[t]) / close[t]
    ret = close.shift(-1) / close - 1
    
    # 去掉最后一个NaN
    ret = ret.dropna()
    
    return ret


def out_path(base: Path, symbol: str, date: str) -> Path:
    """生成输出文件路径"""
    d = base / symbol
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{date}.parquet"


def load_daily(path: Path, source: str) -> pd.DataFrame:
    """加载单日数据"""
    if source == "processed":
        return pd.read_parquet(path)
    if source == "raw":
        try:
            return pd.read_csv(path, compression="gzip")
        except pd.errors.ParserError:
            return pd.read_csv(
                path, 
                compression="gzip",
                on_bad_lines='skip',
                engine='python'
            )
    raise ValueError(f"unknown source={source}")


def main():
    cfg = load_config("configs/data.yaml")
    universe = load_universe(cfg.data.universe_file)
    
    print(f"Universe: {universe}, total={len(universe)}")
    
    # 创建labels输出目录
    output_dir = Path("data/labels/minute_returns")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_done = 0
    total_skip = 0
    total_fail = 0
    
    for sym in universe:
        for sym, date, path, src in iter_daily_files(
            cfg.data.processed_dir, cfg.data.raw_dir, sym, 
            cfg.data.start, cfg.data.end
        ):
            op = out_path(output_dir, sym, date)
            
            # 跳过已存在的文件
            if op.exists():
                total_skip += 1
                continue
            
            try:
                # 加载数据
                df = load_daily(path, src)
                
                # 检查必需列
                if 'a1_p' not in df.columns or 'b1_p' not in df.columns:
                    raise ValueError(f"Missing a1_p or b1_p columns")
                
                # 计算分钟收益率
                ret = compute_minute_returns(df)
                
                # 保存为DataFrame（方便后续处理）
                ret_df = ret.to_frame(name='ret')
                ret_df.to_parquet(op)
                
                total_done += 1
                
                if total_done % 50 == 0:
                    print(f"[OK] done={total_done} skip={total_skip} fail={total_fail}")
                    
            except Exception as e:
                total_fail += 1
                print(f"[FAIL] {sym} {date} src={src} file={path.name} err={type(e).__name__}: {str(e)[:100]}")
    
    print(f"\nFinished. done={total_done} skip={total_skip} fail={total_fail}")
    print(f"Labels saved to: {output_dir}")


if __name__ == "__main__":
    main()
