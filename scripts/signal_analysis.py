"""
OFI信号分析：IC、RankIC、分组收益
评估OFI因子对未来收益率的预测能力
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple

from src.pipeline_io import load_config, load_universe


def compute_ofi_from_tick(df: pd.DataFrame, levels: int = 5) -> pd.DataFrame:
    """从tick数据计算OFI"""
    if not isinstance(df['ts'], pd.DatetimeIndex):
        df['ts'] = pd.to_datetime(df['ts'])
    
    df['minute'] = df['ts'].dt.floor('min')
    
    # 计算tick级OFI
    ofi_sum = 0
    for i in range(1, levels + 1):
        a_col_p, a_col_v = f'a{i}_p', f'a{i}_v'
        b_col_p, b_col_v = f'b{i}_p', f'b{i}_v'
        
        if all(c in df.columns for c in [a_col_p, a_col_v, b_col_p, b_col_v]):
            # 计算价格和量的变化
            delta_bid_v = df[b_col_v].diff()
            delta_ask_v = df[a_col_v].diff()
            
            # OFI = delta_bid_v (价格不变或上升) - delta_ask_v (价格不变或下降)
            ofi_level = delta_bid_v - delta_ask_v
            ofi_sum += ofi_level
    
    df['ofi_tick'] = ofi_sum
    
    # 聚合到分钟
    ofi_minute = df.groupby('minute')['ofi_tick'].sum()
    
    return ofi_minute


def compute_minute_returns(df: pd.DataFrame) -> pd.Series:
    """计算分钟收益率"""
    if not isinstance(df['ts'], pd.DatetimeIndex):
        df['ts'] = pd.to_datetime(df['ts'])
    
    df['minute'] = df['ts'].dt.floor('min')
    
    # 每分钟最后一笔的中间价
    close = (df.groupby('minute').last()['a1_p'] + 
             df.groupby('minute').last()['b1_p']) / 2
    
    # 未来收益率
    ret = close.shift(-1) / close - 1
    
    return ret.dropna()


def load_ofi_and_labels(ofi_dir: Path, label_dir: Path, symbol: str, date: str, 
                        processed_dir: Path, raw_dir: Path) -> pd.DataFrame:
    """从tick数据计算OFI和labels"""
    
    # 尝试从processed目录加载
    tick_path = processed_dir / symbol / date / "part.parquet"
    
    if not tick_path.exists():
        return None
    
    try:
        # 加载tick数据
        df = pd.read_parquet(tick_path)
        
        # 计算OFI
        ofi = compute_ofi_from_tick(df, levels=5)
        
        # 计算收益率
        ret = compute_minute_returns(df)
        
        # 合并
        merged = pd.DataFrame({'ofi': ofi, 'ret': ret})
        merged = merged.dropna()
        
        return merged
        
    except Exception as e:
        print(f"  Error loading {symbol} {date}: {str(e)[:80]}")
        return None


def calculate_ic(ofi: pd.Series, ret: pd.Series) -> Dict:
    """
    计算IC和RankIC
    
    Returns:
        dict with ic, rank_ic, n_obs
    """
    if len(ofi) < 10:  # 至少需要10个观测
        return {'ic': np.nan, 'rank_ic': np.nan, 'n_obs': len(ofi)}
    
    # Pearson相关系数
    ic, p_value = stats.pearsonr(ofi, ret)
    
    # Spearman相关系数（更稳健）
    rank_ic, rank_p_value = stats.spearmanr(ofi, ret)
    
    return {
        'ic': ic,
        'rank_ic': rank_ic,
        'n_obs': len(ofi),
        'ic_p_value': p_value,
        'rank_ic_p_value': rank_p_value
    }


def calculate_quantile_returns(ofi: pd.Series, ret: pd.Series, n_groups: int = 5) -> Dict:
    """
    按OFI分组，计算各组的平均收益
    
    Args:
        ofi: OFI序列
        ret: 未来收益率序列
        n_groups: 分组数量
        
    Returns:
        dict with group returns and statistics
    """
    if len(ofi) < n_groups * 2:
        return None
    
    # 创建DataFrame
    df = pd.DataFrame({'ofi': ofi, 'ret': ret})
    
    # 按OFI分组（qcut会自动处理相同值）
    try:
        df['group'] = pd.qcut(df['ofi'], q=n_groups, labels=False, duplicates='drop')
    except ValueError:
        # 如果qcut失败（比如唯一值太少），用普通分组
        df['group'] = pd.cut(df['ofi'], bins=n_groups, labels=False)
    
    # 计算各组平均收益
    group_stats = df.groupby('group')['ret'].agg(['mean', 'std', 'count'])
    
    # 计算多空收益（最高组 - 最低组）
    long_short = group_stats.loc[group_stats.index.max(), 'mean'] - group_stats.loc[group_stats.index.min(), 'mean']
    
    # 检查单调性
    returns = group_stats['mean'].values
    is_monotonic = all(returns[i] <= returns[i+1] for i in range(len(returns)-1)) or \
                   all(returns[i] >= returns[i+1] for i in range(len(returns)-1))
    
    return {
        'group_returns': group_stats['mean'].to_dict(),
        'group_counts': group_stats['count'].to_dict(),
        'long_short': long_short,
        'is_monotonic': is_monotonic
    }


def analyze_symbol(symbol: str, ofi_dir: Path, label_dir: Path, start: str, end: str) -> pd.DataFrame:
    """分析单个标的的IC和分组收益"""
    
    results = []
    
    # 遍历所有日期
    symbol_ofi_dir = ofi_dir / symbol
    if not symbol_ofi_dir.exists():
        return pd.DataFrame()
    
    for file_path in sorted(symbol_ofi_dir.glob("*.parquet")):
        date = file_path.stem
        
        # 过滤日期范围
        if date < start or date > end:
            continue
        
        # 加载数据
        df = load_ofi_and_labels(ofi_dir, label_dir, symbol, date)
        
        if df is None or len(df) < 10:
            continue
        
        # 计算IC
        ic_stats = calculate_ic(df['ofi'], df['ret'])
        
        # 计算分组收益
        quantile_stats = calculate_quantile_returns(df['ofi'], df['ret'], n_groups=5)
        
        result = {
            'symbol': symbol,
            'date': date,
            **ic_stats
        }
        
        if quantile_stats:
            result.update({
                'long_short': quantile_stats['long_short'],
                'is_monotonic': quantile_stats['is_monotonic'],
                **{f'g{k}_ret': v for k, v in quantile_stats['group_returns'].items()},
                **{f'g{k}_count': v for k, v in quantile_stats['group_counts'].items()}
            })
        
        results.append(result)
    
    return pd.DataFrame(results)


def generate_report(all_results: pd.DataFrame, output_dir: Path):
    """生成分析报告"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. IC/RankIC汇总表
    print("\n=== IC/RankIC Summary ===")
    
    ic_summary = all_results.groupby('symbol').agg({
        'ic': ['mean', 'std', 'count'],
        'rank_ic': ['mean', 'std'],
        'n_obs': 'mean'
    })
    
    # 计算t统计量
    for symbol in all_results['symbol'].unique():
        sym_data = all_results[all_results['symbol'] == symbol]
        
        # IC的t-stat
        ic_values = sym_data['ic'].dropna()
        if len(ic_values) > 1:
            t_stat = ic_values.mean() / (ic_values.std() / np.sqrt(len(ic_values)))
            ic_summary.loc[symbol, ('ic', 't_stat')] = t_stat
        
        # RankIC的t-stat
        rank_ic_values = sym_data['rank_ic'].dropna()
        if len(rank_ic_values) > 1:
            t_stat = rank_ic_values.mean() / (rank_ic_values.std() / np.sqrt(len(rank_ic_values)))
            ic_summary.loc[symbol, ('rank_ic', 't_stat')] = t_stat
    
    print(ic_summary)
    
    # 2. 保存详细结果
    csv_path = output_dir / "day3_signal_detail.csv"
    all_results.to_csv(csv_path, index=False)
    print(f"\nSaved detailed results to: {csv_path}")
    
    # 3. 生成可视化
    generate_visualizations(all_results, ic_summary, output_dir)
    
    # 4. 生成Markdown报告
    generate_markdown_report(all_results, ic_summary, output_dir)


def generate_visualizations(all_results: pd.DataFrame, ic_summary: pd.DataFrame, output_dir: Path):
    """生成可视化图表"""
    
    symbols = all_results['symbol'].unique()
    n_symbols = len(symbols)
    
    # 图1：IC时序图
    fig, axes = plt.subplots(n_symbols, 1, figsize=(12, 3*n_symbols))
    if n_symbols == 1:
        axes = [axes]
    
    for idx, symbol in enumerate(symbols):
        sym_data = all_results[all_results['symbol'] == symbol].copy()
        sym_data['date'] = pd.to_datetime(sym_data['date'])
        sym_data = sym_data.sort_values('date')
        
        axes[idx].plot(sym_data['date'], sym_data['ic'], label='IC', alpha=0.7, linewidth=0.8)
        axes[idx].plot(sym_data['date'], sym_data['rank_ic'], label='RankIC', alpha=0.7, linewidth=0.8)
        axes[idx].axhline(0, color='red', linestyle='--', linewidth=0.5)
        axes[idx].set_title(f'{symbol} - IC Time Series')
        axes[idx].set_ylabel('IC')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / "day3_ic_timeseries.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved IC time series plot")
    
    # 图2：分组收益图
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, symbol in enumerate(symbols):
        sym_data = all_results[all_results['symbol'] == symbol]
        
        # 提取分组收益列
        group_cols = [col for col in sym_data.columns if col.startswith('g') and col.endswith('_ret')]
        
        if group_cols:
            # 计算平均分组收益
            group_returns = []
            for col in sorted(group_cols):
                group_returns.append(sym_data[col].mean())
            
            groups = list(range(len(group_returns)))
            axes[idx].bar(groups, group_returns, alpha=0.7)
            axes[idx].axhline(0, color='red', linestyle='--', linewidth=0.5)
            axes[idx].set_title(f'{symbol} - Avg Group Returns')
            axes[idx].set_xlabel('OFI Quantile Group')
            axes[idx].set_ylabel('Avg Forward Return')
            axes[idx].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / "day3_group_returns.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved group returns plot")
    
    # 图3：IC分布直方图
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, symbol in enumerate(symbols):
        sym_data = all_results[all_results['symbol'] == symbol]
        
        axes[idx].hist(sym_data['ic'].dropna(), bins=30, alpha=0.6, label='IC', edgecolor='black')
        axes[idx].hist(sym_data['rank_ic'].dropna(), bins=30, alpha=0.6, label='RankIC', edgecolor='black')
        axes[idx].axvline(0, color='red', linestyle='--', linewidth=1)
        axes[idx].set_title(f'{symbol} - IC Distribution')
        axes[idx].set_xlabel('IC Value')
        axes[idx].set_ylabel('Frequency')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / "day3_ic_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved IC distribution plot")


def generate_markdown_report(all_results: pd.DataFrame, ic_summary: pd.DataFrame, output_dir: Path):
    """生成Markdown报告"""
    
    md_path = output_dir / "day3_ofi_signal.md"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Day3 OFI信号分析报告\n\n")
        f.write(f"生成时间: {pd.Timestamp.now()}\n\n")
        
        f.write("## 1. 概述\n\n")
        f.write("本报告评估OFI（订单流失衡）因子对未来1分钟收益率的预测能力。\n\n")
        f.write("**分析方法：**\n")
        f.write("- IC (Information Coefficient): Pearson相关系数\n")
        f.write("- RankIC: Spearman相关系数（更稳健）\n")
        f.write("- 分组分析: 将OFI分为5组，观察各组未来收益\n\n")
        
        f.write("## 2. IC/RankIC汇总\n\n")
        f.write("### 按标的统计\n\n")
        
        # 格式化IC汇总表
        summary_table = ic_summary.copy()
        summary_table.columns = ['_'.join(col).strip() for col in summary_table.columns.values]
        f.write(summary_table.to_markdown())
        f.write("\n\n")
        
        # 解读
        f.write("### 解读\n\n")
        for symbol in all_results['symbol'].unique():
            sym_data = all_results[all_results['symbol'] == symbol]
            ic_mean = sym_data['ic'].mean()
            rank_ic_mean = sym_data['rank_ic'].mean()
            
            # 计算t统计量
            ic_tstat = ic_mean / (sym_data['ic'].std() / np.sqrt(len(sym_data)))
            
            f.write(f"**{symbol}:**\n")
            f.write(f"- IC均值: {ic_mean:.6f} (t-stat: {ic_tstat:.2f})\n")
            f.write(f"- RankIC均值: {rank_ic_mean:.6f}\n")
            
            # 判断显著性
            if abs(ic_tstat) > 2.0:
                f.write(f"- ✅ IC显著 (|t-stat| > 2.0)\n")
            else:
                f.write(f"- ⚠️ IC不显著 (|t-stat| < 2.0)\n")
            
            # 判断方向
            if ic_mean > 0:
                f.write(f"- 方向: 正向（OFI越大，未来收益越高）\n")
            else:
                f.write(f"- 方向: 负向（OFI越大，未来收益越低）\n")
            
            f.write("\n")
        
        f.write("## 3. 分组收益分析\n\n")
        f.write("### 平均分组收益\n\n")
        f.write("将OFI分为5组（Q0最小，Q4最大），观察各组的平均未来收益：\n\n")
        
        # 分组收益表
        group_summary = []
        for symbol in all_results['symbol'].unique():
            sym_data = all_results[all_results['symbol'] == symbol]
            
            row = {'symbol': symbol}
            for i in range(5):
                col = f'g{i}_ret'
                if col in sym_data.columns:
                    row[f'Q{i}'] = sym_data[col].mean()
            
            if 'long_short' in sym_data.columns:
                row['Long-Short'] = sym_data['long_short'].mean()
            
            if 'is_monotonic' in sym_data.columns:
                monotonic_ratio = sym_data['is_monotonic'].mean()
                row['Monotonic%'] = monotonic_ratio
            
            group_summary.append(row)
        
        group_df = pd.DataFrame(group_summary)
        f.write(group_df.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("**说明：**\n")
        f.write("- Q0: OFI最小组\n")
        f.write("- Q4: OFI最大组\n")
        f.write("- Long-Short: Q4 - Q0 (多空收益)\n")
        f.write("- Monotonic%: 分组收益单调的天数占比\n\n")
        
        f.write("## 4. 可视化\n\n")
        f.write("### IC时序图\n\n")
        f.write("![IC Time Series](day3_ic_timeseries.png)\n\n")
        
        f.write("### 分组收益图\n\n")
        f.write("![Group Returns](day3_group_returns.png)\n\n")
        
        f.write("### IC分布图\n\n")
        f.write("![IC Distribution](day3_ic_distribution.png)\n\n")
        
        f.write("## 5. 结论\n\n")
        
        # 统计显著的标的
        significant_symbols = []
        for symbol in all_results['symbol'].unique():
            sym_data = all_results[all_results['symbol'] == symbol]
            ic_tstat = sym_data['ic'].mean() / (sym_data['ic'].std() / np.sqrt(len(sym_data)))
            if abs(ic_tstat) > 2.0:
                significant_symbols.append(symbol)
        
        if significant_symbols:
            f.write(f"✅ **发现显著信号**: {len(significant_symbols)}/{len(all_results['symbol'].unique())} 个标的的OFI因子显著\n\n")
            f.write(f"显著标的: {', '.join(significant_symbols)}\n\n")
        else:
            f.write("⚠️ **未发现显著信号**: 所有标的的IC t统计量绝对值均 < 2.0\n\n")
        
        # 计算整体IC
        overall_ic = all_results['ic'].mean()
        overall_rank_ic = all_results['rank_ic'].mean()
        
        f.write(f"**整体IC**: {overall_ic:.6f}\n\n")
        f.write(f"**整体RankIC**: {overall_rank_ic:.6f}\n\n")
        
        f.write("### 建议\n\n")
        if overall_ic > 0.01 and len(significant_symbols) >= len(all_results['symbol'].unique()) / 2:
            f.write("- OFI因子显示出较强的预测能力，可以考虑构建策略\n")
            f.write("- 建议重点关注IC显著的标的\n")
            f.write("- 需要进一步考虑交易成本和滑点\n")
        elif overall_ic > 0:
            f.write("- OFI因子显示出微弱的预测能力\n")
            f.write("- 建议结合其他因子或优化OFI计算方法\n")
            f.write("- 需要考虑是否能覆盖交易成本\n")
        else:
            f.write("- OFI因子预测能力较弱或方向相反\n")
            f.write("- 建议重新审视OFI的计算方法或参数\n")
            f.write("- 可能需要考虑反向交易或寻找其他因子\n")
    
    print(f"\nSaved markdown report to: {md_path}")


def main():
    cfg = load_config("configs/data.yaml")
    universe = load_universe(cfg.data.universe_file)
    
    print(f"Analyzing OFI signal for {len(universe)} symbols...")
    
    ofi_dir = cfg.ofi.output_dir
    label_dir = Path("data/labels/minute_returns")
    
    # 分析所有标的
    all_results = []
    
    for symbol in universe:
        print(f"\nAnalyzing {symbol}...")
        result_df = analyze_symbol(symbol, ofi_dir, label_dir, cfg.data.start, cfg.data.end)
        
        if len(result_df) > 0:
            all_results.append(result_df)
            print(f"  {len(result_df)} days analyzed")
        else:
            print(f"  No valid data")
    
    if not all_results:
        print("No results to analyze!")
        return
    
    # 合并所有结果
    all_results_df = pd.concat(all_results, ignore_index=True)
    
    print(f"\nTotal records: {len(all_results_df)}")
    
    # 生成报告
    output_dir = Path("outputs/reports")
    generate_report(all_results_df, output_dir)
    
    print("\n✅ Signal analysis completed!")


if __name__ == "__main__":
    main()
