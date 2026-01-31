"""
数据质量检查脚本
- 分钟覆盖率
- Book异常率
- OFI分布稳定性
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict

from src.pipeline_io import load_config, load_universe, iter_daily_files


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


def check_minute_coverage(df: pd.DataFrame) -> Dict:
    """检查分钟覆盖率"""
    if 'ts' not in df.columns:
        return {'n_minutes': 0, 'expected': 240, 'coverage': 0.0}
    
    df['ts'] = pd.to_datetime(df['ts'])
    df['minute'] = df['ts'].dt.floor('min')
    n_minutes = df['minute'].nunique()
    expected = 240  # A股连续竞价约240分钟
    coverage = n_minutes / expected
    
    return {
        'n_minutes': n_minutes,
        'expected': expected,
        'coverage': coverage
    }


def check_book_anomalies(df: pd.DataFrame) -> Dict:
    """检查订单簿异常"""
    total = len(df)
    if total == 0:
        return {
            'spread_negative': 0.0,
            'mid_negative': 0.0,
            'bid_ge_ask': 0.0,
            'total_rows': 0
        }
    
    anomalies = {}
    
    # 检查spread <= 0
    if 'a1_p' in df.columns and 'b1_p' in df.columns:
        spread = df['a1_p'] - df['b1_p']
        anomalies['spread_negative'] = (spread <= 0).sum() / total
        
        # 检查mid <= 0
        mid = (df['a1_p'] + df['b1_p']) / 2
        anomalies['mid_negative'] = (mid <= 0).sum() / total
        
        # 检查bid >= ask
        anomalies['bid_ge_ask'] = (df['b1_p'] >= df['a1_p']).sum() / total
    else:
        anomalies['spread_negative'] = np.nan
        anomalies['mid_negative'] = np.nan
        anomalies['bid_ge_ask'] = np.nan
    
    anomalies['total_rows'] = total
    
    return anomalies


def load_ofi_data(ofi_dir: Path, symbol: str, date: str) -> pd.DataFrame:
    """加载OFI数据"""
    ofi_path = ofi_dir / symbol / f"{date}.parquet"
    if not ofi_path.exists():
        return None
    
    try:
        return pd.read_parquet(ofi_path)
    except Exception:
        return None


def check_ofi_distribution(ofi_df: pd.DataFrame) -> Dict:
    """检查OFI分布统计"""
    if ofi_df is None or 'ofi' not in ofi_df.columns:
        return {
            'mean': np.nan,
            'std': np.nan,
            'q25': np.nan,
            'q50': np.nan,
            'q75': np.nan,
            'min': np.nan,
            'max': np.nan
        }
    
    ofi = ofi_df['ofi'].dropna()
    
    return {
        'mean': ofi.mean(),
        'std': ofi.std(),
        'q25': ofi.quantile(0.25),
        'q50': ofi.quantile(0.50),
        'q75': ofi.quantile(0.75),
        'min': ofi.min(),
        'max': ofi.max()
    }


def main():
    cfg = load_config("configs/data.yaml")
    universe = load_universe(cfg.data.universe_file)
    
    print(f"Checking data quality for {len(universe)} symbols...")
    
    # 创建输出目录
    output_dir = Path("outputs/data_quality")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有统计信息
    results = []
    ofi_stats_by_symbol = {sym: [] for sym in universe}
    
    total_files = 0
    processed = 0
    
    for sym in universe:
        print(f"\nProcessing {sym}...")
        sym_count = 0
        
        for sym, date, path, src in iter_daily_files(
            cfg.data.processed_dir, cfg.data.raw_dir, sym, 
            cfg.data.start, cfg.data.end
        ):
            total_files += 1
            
            try:
                # 加载tick数据
                df = load_daily(path, src)
                
                # 检查分钟覆盖率
                coverage = check_minute_coverage(df)
                
                # 检查book异常
                anomalies = check_book_anomalies(df)
                
                # 加载OFI数据
                ofi_df = load_ofi_data(cfg.ofi.output_dir, sym, date)
                ofi_dist = check_ofi_distribution(ofi_df)
                
                # 记录结果
                result = {
                    'symbol': sym,
                    'date': date,
                    'source': src,
                    **coverage,
                    **anomalies,
                    'ofi_mean': ofi_dist['mean'],
                    'ofi_std': ofi_dist['std'],
                    'ofi_q25': ofi_dist['q25'],
                    'ofi_q50': ofi_dist['q50'],
                    'ofi_q75': ofi_dist['q75'],
                    'ofi_min': ofi_dist['min'],
                    'ofi_max': ofi_dist['max']
                }
                results.append(result)
                
                # 收集OFI统计用于可视化
                if not np.isnan(ofi_dist['mean']):
                    ofi_stats_by_symbol[sym].append({
                        'date': pd.to_datetime(date),
                        'mean': ofi_dist['mean'],
                        'std': ofi_dist['std']
                    })
                
                processed += 1
                sym_count += 1
                
                if processed % 100 == 0:
                    print(f"  Processed {processed}/{total_files} files...")
                    
            except Exception as e:
                print(f"  [ERROR] {sym} {date}: {str(e)[:80]}")
                continue
        
        print(f"  {sym}: {sym_count} days processed")
    
    print(f"\nTotal processed: {processed}/{total_files}")
    
    # 保存汇总CSV
    df_results = pd.DataFrame(results)
    csv_path = output_dir / "day3_panel_summary.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"\nSaved summary to: {csv_path}")
    
    # 生成统计报告
    print("\n=== Data Quality Summary ===")
    print(f"\nMinute Coverage:")
    print(df_results.groupby('symbol')['coverage'].describe())
    
    print(f"\nBook Anomalies (mean %):")
    for col in ['spread_negative', 'mid_negative', 'bid_ge_ask']:
        if col in df_results.columns:
            print(f"  {col}: {df_results[col].mean()*100:.4f}%")
    
    # 可视化OFI分布
    print("\nGenerating OFI distribution plot...")
    
    fig, axes = plt.subplots(len(universe), 2, figsize=(14, 4*len(universe)))
    if len(universe) == 1:
        axes = axes.reshape(1, -1)
    
    for idx, sym in enumerate(universe):
        stats = ofi_stats_by_symbol[sym]
        if not stats:
            continue
        
        stats_df = pd.DataFrame(stats).set_index('date').sort_index()
        
        # 左图：均值时序
        axes[idx, 0].plot(stats_df.index, stats_df['mean'], linewidth=0.8)
        axes[idx, 0].axhline(0, color='red', linestyle='--', linewidth=0.5)
        axes[idx, 0].set_title(f'{sym} - OFI Mean Over Time')
        axes[idx, 0].set_ylabel('OFI Mean')
        axes[idx, 0].grid(True, alpha=0.3)
        
        # 右图：标准差时序
        axes[idx, 1].plot(stats_df.index, stats_df['std'], linewidth=0.8, color='orange')
        axes[idx, 1].set_title(f'{sym} - OFI Std Over Time')
        axes[idx, 1].set_ylabel('OFI Std')
        axes[idx, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    png_path = output_dir / "day3_ofi_distribution.png"
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    print(f"Saved plot to: {png_path}")
    
    # 生成Markdown报告
    md_path = output_dir / "day3_quality_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Day3 数据质量报告\n\n")
        f.write(f"生成时间: {pd.Timestamp.now()}\n\n")
        
        f.write("## 1. 总体统计\n\n")
        f.write(f"- 检查文件数: {total_files}\n")
        f.write(f"- 成功处理: {processed}\n")
        f.write(f"- 标的数量: {len(universe)}\n")
        f.write(f"- 标的列表: {', '.join(universe)}\n\n")
        
        f.write("## 2. 分钟覆盖率\n\n")
        cov_summary = df_results.groupby('symbol')['coverage'].agg(['mean', 'min', 'max', 'count'])
        f.write(cov_summary.to_markdown())
        f.write("\n\n")
        
        f.write("## 3. Book异常率 (平均%)\n\n")
        f.write("| 异常类型 | 比例 |\n")
        f.write("|---------|------|\n")
        for col in ['spread_negative', 'mid_negative', 'bid_ge_ask']:
            if col in df_results.columns:
                ratio = df_results[col].mean() * 100
                f.write(f"| {col} | {ratio:.4f}% |\n")
        f.write("\n")
        
        f.write("## 4. OFI分布稳定性\n\n")
        f.write("![OFI Distribution](day3_ofi_distribution.png)\n\n")
        
        f.write("### 按标的统计\n\n")
        ofi_summary = df_results.groupby('symbol')[['ofi_mean', 'ofi_std']].agg(['mean', 'std'])
        f.write(ofi_summary.to_markdown())
        f.write("\n\n")
        
        f.write("## 5. 数据质量建议\n\n")
        
        # 检查异常
        low_coverage = df_results[df_results['coverage'] < 0.9]
        if len(low_coverage) > 0:
            f.write(f"⚠️ **警告**: {len(low_coverage)} 个文件的分钟覆盖率 < 90%\n\n")
        
        high_anomaly = df_results[df_results['spread_negative'] > 0.01]
        if len(high_anomaly) > 0:
            f.write(f"⚠️ **警告**: {len(high_anomaly)} 个文件的spread异常率 > 1%\n\n")
        
        # OFI异常值检测
        ofi_mean_outliers = df_results[np.abs(df_results['ofi_mean']) > df_results['ofi_mean'].std() * 5]
        if len(ofi_mean_outliers) > 0:
            f.write(f"⚠️ **警告**: {len(ofi_mean_outliers)} 个文件的OFI均值异常（超过5倍标准差）\n\n")
        
        if len(low_coverage) == 0 and len(high_anomaly) == 0 and len(ofi_mean_outliers) == 0:
            f.write("✅ 数据质量良好，未发现明显异常。\n\n")
    
    print(f"Saved markdown report to: {md_path}")
    print("\n✅ Quality check completed!")


if __name__ == "__main__":
    main()
