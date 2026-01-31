"""
OFI信号分析脚本 - 从tick数据直接计算
计算IC、RankIC、分组收益率
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import yaml
from typing import Dict, List

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_config() -> Dict:
    """加载配置文件"""
    with open("configs/data.yaml", 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    
    return {
        'processed_dir': Path("data/processed/ticks"),
        'output_dir': Path("outputs/reports"),
        'start': content['data']['start'],
        'end': content['data']['end']
    }


def load_universe() -> List[str]:
    """加载universe"""
    with open("configs/universe.yaml", 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    
    if isinstance(content, dict) and "universe" in content:
        return content["universe"]
    return content


def compute_ofi_from_tick(df: pd.DataFrame, levels: int = 5) -> pd.DataFrame:
    """从tick数据计算分钟级OFI"""
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'ts' in df.columns:
            df['ts'] = pd.to_datetime(df['ts'])
            df = df.set_index('ts')
    
    # 分钟标签
    df['minute'] = df.index.floor('min')
    
    # 计算tick级OFI
    ofi_sum = 0
    for i in range(1, levels + 1):
        a_col_p, a_col_v = f'a{i}_p', f'a{i}_v'
        b_col_p, b_col_v = f'b{i}_p', f'b{i}_v'
        
        if all(c in df.columns for c in [a_col_p, a_col_v, b_col_p, b_col_v]):
            # 计算量的变化
            delta_bid_v = df[b_col_v].diff()
            delta_ask_v = df[a_col_v].diff()
            
            # OFI = delta_bid_v - delta_ask_v
            ofi_level = delta_bid_v - delta_ask_v
            ofi_sum += ofi_level
    
    df['ofi_tick'] = ofi_sum
    
    # 聚合到分钟
    ofi_minute = df.groupby('minute').agg({
        'ofi_tick': 'sum',
        'a1_p': 'last',
        'b1_p': 'last'
    })
    
    return ofi_minute


def compute_minute_returns(ofi_df: pd.DataFrame) -> pd.Series:
    """从OFI DataFrame计算分钟收益率"""
    # 中间价
    close = (ofi_df['a1_p'] + ofi_df['b1_p']) / 2
    
    # 未来收益率
    ret = close.shift(-1) / close - 1
    
    return ret


def load_and_compute(symbol: str, date: str, processed_dir: Path) -> pd.DataFrame:
    """加载tick数据并计算OFI和收益率"""
    tick_path = processed_dir / symbol / date / "part.parquet"
    
    if not tick_path.exists():
        return None
    
    try:
        # 加载tick数据
        df = pd.read_parquet(tick_path)
        
        # 计算OFI
        ofi_df = compute_ofi_from_tick(df, levels=5)
        
        # 计算收益率
        ofi_df['ret'] = compute_minute_returns(ofi_df)
        
        # 只保留ofi和ret
        result = ofi_df[['ofi_tick', 'ret']].dropna()
        result.columns = ['ofi', 'ret']
        
        return result
        
    except Exception as e:
        print(f"  Error: {str(e)[:80]}")
        return None


def calculate_ic(df: pd.DataFrame) -> Dict:
    """计算IC和RankIC"""
    if len(df) < 10:
        return None
    
    # Pearson相关系数 (IC)
    ic, ic_pval = stats.pearsonr(df['ofi'], df['ret'])
    
    # Spearman相关系数 (RankIC)
    rankic, rankic_pval = stats.spearmanr(df['ofi'], df['ret'])
    
    return {
        'ic_mean': ic,
        'ic_pval': ic_pval,
        'rankic_mean': rankic,
        'rankic_pval': rankic_pval,
        'n_samples': len(df)
    }


def calculate_quantile_returns(df: pd.DataFrame, n_quantiles: int = 5) -> Dict:
    """计算分位数组的平均收益"""
    if len(df) < n_quantiles * 2:
        return None
    
    try:
        # 根据OFI分组
        df = df.copy()
        df['group'] = pd.qcut(df['ofi'], q=n_quantiles, labels=False, duplicates='drop')
    except ValueError:
        # qcut失败，用cut
        df['group'] = pd.cut(df['ofi'], bins=n_quantiles, labels=False)
    
    # 各组统计
    group_stats = df.groupby('group')['ret'].agg(['mean', 'std', 'count'])
    
    # 多空收益
    if len(group_stats) >= 2:
        long_short = group_stats.loc[group_stats.index.max(), 'mean'] - \
                     group_stats.loc[group_stats.index.min(), 'mean']
    else:
        long_short = np.nan
    
    return {
        'group_returns': group_stats['mean'].to_dict(),
        'group_counts': group_stats['count'].to_dict(),
        'long_short': long_short
    }


def generate_visualizations(symbol: str, quantile_returns: Dict, output_dir: Path):
    """生成分组收益图表"""
    if quantile_returns is None:
        return
    
    group_returns = quantile_returns['group_returns']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    groups = sorted(group_returns.keys())
    returns = [group_returns[g] for g in groups]
    
    ax.bar(groups, returns, alpha=0.7)
    ax.set_xlabel('OFI Quantile Group')
    ax.set_ylabel('Average Return')
    ax.set_title(f'{symbol} - OFI Quantile Group Returns')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / f"day3_ofi_quantile_{symbol}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Chart saved to {output_path}")


def generate_report(summary_df: pd.DataFrame, output_dir: Path):
    """生成Markdown报告"""
    report_path = output_dir / "day3_ofi_signal.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# OFI Signal Analysis Report\n\n")
        f.write("## IC Summary\n\n")
        
        f.write("| Symbol | IC | IC p-value | RankIC | RankIC p-value | Samples |\n")
        f.write("|--------|-------|------------|--------|----------------|----------|\n")
        
        for _, row in summary_df.iterrows():
            f.write(f"| {row['symbol']} | {row['ic_mean']:.4f} | {row['ic_pval']:.4f} | "
                   f"{row['rankic_mean']:.4f} | {row['rankic_pval']:.4f} | {int(row['n_samples'])} |\n")
        
        f.write("\n## Overall Statistics\n\n")
        f.write(f"- Mean IC: {summary_df['ic_mean'].mean():.4f}\n")
        f.write(f"- Mean RankIC: {summary_df['rankic_mean'].mean():.4f}\n")
        f.write(f"- IC t-stat: {summary_df['ic_mean'].mean() / summary_df['ic_mean'].std() * np.sqrt(len(summary_df)):.2f}\n")
        f.write(f"- RankIC t-stat: {summary_df['rankic_mean'].mean() / summary_df['rankic_mean'].std() * np.sqrt(len(summary_df)):.2f}\n")
        
        f.write("\n## Quantile Group Visualizations\n\n")
        f.write("See individual symbol charts in this directory.\n")
    
    print(f"\nReport saved to {report_path}")


def main():
    # 加载配置
    config = load_config()
    processed_dir = config['processed_dir']
    output_dir = config['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载universe
    universe = load_universe()
    
    print(f"Analyzing OFI signal for {len(universe)} symbols...")
    print(f"Computing OFI from tick data...\n")
    
    all_results = []
    
    for symbol in universe:
        print(f"Processing {symbol}...")
        
        # 收集该标的的所有数据
        symbol_data = []
        
        # 遍历日期目录
        symbol_dir = processed_dir / symbol
        if not symbol_dir.exists():
            print(f"  No data directory")
            continue
        
        for date_dir in sorted(symbol_dir.iterdir()):
            if date_dir.is_dir():
                date = date_dir.name
                merged = load_and_compute(symbol, date, processed_dir)
                
                if merged is not None and len(merged) > 0:
                    symbol_data.append(merged)
        
        if not symbol_data:
            print(f"  No valid data\n")
            continue
        
        # 合并所有日期
        all_data = pd.concat(symbol_data, ignore_index=True)
        print(f"  Total records: {len(all_data)}")
        
        # 计算IC
        ic_results = calculate_ic(all_data)
        if ic_results:
            ic_results['symbol'] = symbol
            all_results.append(ic_results)
            print(f"  IC: {ic_results['ic_mean']:.4f}, RankIC: {ic_results['rankic_mean']:.4f}")
        
        # 计算分组收益
        quantile_returns = calculate_quantile_returns(all_data, n_quantiles=5)
        if quantile_returns:
            print(f"  Long-Short: {quantile_returns['long_short']:.6f}")
        
        # 生成图表
        generate_visualizations(symbol, quantile_returns, output_dir)
        print()
    
    # 汇总结果
    if all_results:
        summary_df = pd.DataFrame(all_results)
        summary_path = output_dir / "day3_ofi_ic_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"IC summary saved to {summary_path}")
        
        # 生成Markdown报告
        generate_report(summary_df, output_dir)
    else:
        print("No results to summarize.")


if __name__ == "__main__":
    main()
