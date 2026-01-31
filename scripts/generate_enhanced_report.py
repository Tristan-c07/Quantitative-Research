"""
增强版信号分析报告生成
添加分组收益详细统计
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def generate_enhanced_report():
    """生成增强版报告"""
    
    # 读取IC汇总
    ic_df = pd.read_csv("outputs/reports/day3_ofi_ic_summary.csv")
    
    print("Generating enhanced report...")
    
    report_path = Path("outputs/reports/day3_ofi_signal_enhanced.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# OFI信号分析报告（增强版）\n\n")
        f.write("## 1. 信息系数（IC）汇总\n\n")
        
        f.write("### 1.1 各标的IC统计\n\n")
        f.write("| 标的 | IC | IC p值 | RankIC | RankIC p值 | 样本数 |\n")
        f.write("|------|-------|---------|---------|------------|--------|\n")
        
        for _, row in ic_df.iterrows():
            f.write(f"| {row['symbol']} | {row['ic_mean']:.4f} | {row['ic_pval']:.4e} | "
                   f"{row['rankic_mean']:.4f} | {row['rankic_pval']:.4e} | {int(row['n_samples']):,} |\n")
        
        f.write("\n### 1.2 整体统计\n\n")
        
        ic_mean = ic_df['ic_mean'].mean()
        ic_std = ic_df['ic_mean'].std()
        ic_tstat = ic_mean / ic_std * np.sqrt(len(ic_df))
        
        rankic_mean = ic_df['rankic_mean'].mean()
        rankic_std = ic_df['rankic_mean'].std()
        rankic_tstat = rankic_mean / rankic_std * np.sqrt(len(ic_df))
        
        f.write(f"- **平均IC**: {ic_mean:.4f} ± {ic_std:.4f}\n")
        f.write(f"- **IC t统计量**: {ic_tstat:.2f}\n")
        f.write(f"- **平均RankIC**: {rankic_mean:.4f} ± {rankic_std:.4f}\n")
        f.write(f"- **RankIC t统计量**: {rankic_tstat:.2f}\n")
        f.write(f"- **总样本数**: {int(ic_df['n_samples'].sum()):,}\n\n")
        
        # 解读
        f.write("### 1.3 结果解读\n\n")
        
        if rankic_mean > 0.05:
            f.write("✅ **RankIC显著为正**：OFI对下一分钟收益率有较强的预测能力\n\n")
        elif rankic_mean > 0.02:
            f.write("✔️ **RankIC为正**：OFI对下一分钟收益率有一定的预测能力\n\n")
        else:
            f.write("❌ **RankIC较弱**：OFI的预测能力有限\n\n")
        
        if abs(rankic_tstat) > 2:
            f.write(f"✅ **统计显著性强**：t统计量 = {rankic_tstat:.2f}，远超显著性阈值(±2)\n\n")
        else:
            f.write(f"❌ **统计显著性弱**：t统计量 = {rankic_tstat:.2f}，未达到显著性阈值(±2)\n\n")
        
        # IC vs RankIC
        f.write("### 1.4 IC vs RankIC对比\n\n")
        f.write(f"- IC: {ic_mean:.4f} (Pearson相关系数，衡量线性关系)\n")
        f.write(f"- RankIC: {rankic_mean:.4f} (Spearman相关系数，衡量单调关系)\n\n")
        
        if rankic_mean > ic_mean:
            f.write("**RankIC > IC**：表明OFI与收益率更多是单调关系而非线性关系，建议使用排序类策略\n\n")
        else:
            f.write("**IC >= RankIC**：表明OFI与收益率的线性关系较强\n\n")
        
        # 分组收益图表
        f.write("## 2. 分位数组收益率\n\n")
        f.write("按OFI大小将样本分为5组，观察各组的平均收益率：\n\n")
        
        for symbol in ic_df['symbol']:
            f.write(f"### {symbol}\n\n")
            f.write(f"![{symbol}分组收益](day3_ofi_quantile_{symbol}.png)\n\n")
        
        # 使用建议
        f.write("## 3. 策略建议\n\n")
        
        f.write("基于以上分析，对OFI因子的使用建议如下：\n\n")
        
        if rankic_mean > 0.05 and abs(rankic_tstat) > 2:
            f.write("### ✅ 推荐使用\n\n")
            f.write("1. **因子有效性**：RankIC显著为正，预测能力强\n")
            f.write("2. **策略类型**：建议使用分组策略或排序策略\n")
            f.write("3. **持仓周期**：1分钟（基于当前分析）\n")
            f.write("4. **风险提示**：\n")
            f.write("   - 注意交易成本（高频交易）\n")
            f.write("   - 监控滑点影响\n")
            f.write("   - 考虑组合构建以降低个股风险\n\n")
        elif rankic_mean > 0.02:
            f.write("### ⚠️ 谨慎使用\n\n")
            f.write("1. **因子有效性**：RankIC为正但不够强\n")
            f.write("2. **改进方向**：\n")
            f.write("   - 考虑与其他因子组合\n")
            f.write("   - 尝试不同的OFI计算方法（如不同深度）\n")
            f.write("   - 调整持仓周期\n")
            f.write("3. **风险提示**：单独使用可能效果不佳\n\n")
        else:
            f.write("### ❌ 不推荐使用\n\n")
            f.write("1. **因子有效性**：预测能力不足\n")
            f.write("2. **改进方向**：\n")
            f.write("   - 重新审视OFI计算逻辑\n")
            f.write("   - 考虑数据质量问题\n")
            f.write("   - 尝试其他订单流特征\n\n")
        
        # 下一步工作
        f.write("## 4. 后续分析方向\n\n")
        f.write("1. **分层分析**：\n")
        f.write("   - 按市场状态分层（高波动/低波动）\n")
        f.write("   - 按时段分层（开盘/收盘/午间）\n\n")
        f.write("2. **衰减分析**：\n")
        f.write("   - 观察OFI对未来1/3/5/10分钟收益的预测能力衰减\n\n")
        f.write("3. **组合优化**：\n")
        f.write("   - 与其他因子（成交量、波动率）组合\n")
        f.write("   - 构建多因子模型\n\n")
        f.write("4. **回测验证**：\n")
        f.write("   - 完整的回测框架\n")
        f.write("   - 考虑交易成本、滑点\n")
        f.write("   - 计算夏普比率、最大回撤等指标\n\n")
    
    print(f"Enhanced report saved to {report_path}")
    
    # 生成汇总图表
    generate_summary_charts(ic_df)


def generate_summary_charts(ic_df: pd.DataFrame):
    """生成汇总图表"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. IC条形图
    ax = axes[0, 0]
    symbols = ic_df['symbol']
    x = np.arange(len(symbols))
    width = 0.35
    
    ax.bar(x - width/2, ic_df['ic_mean'], width, label='IC', alpha=0.8)
    ax.bar(x + width/2, ic_df['rankic_mean'], width, label='RankIC', alpha=0.8)
    ax.set_xlabel('标的')
    ax.set_ylabel('相关系数')
    ax.set_title('各标的IC与RankIC对比')
    ax.set_xticks(x)
    ax.set_xticklabels(symbols, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    
    # 2. IC分布
    ax = axes[0, 1]
    ax.hist(ic_df['ic_mean'], bins=10, alpha=0.7, label='IC', edgecolor='black')
    ax.hist(ic_df['rankic_mean'], bins=10, alpha=0.7, label='RankIC', edgecolor='black')
    ax.set_xlabel('相关系数')
    ax.set_ylabel('频数')
    ax.set_title('IC分布')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. IC vs RankIC散点图
    ax = axes[1, 0]
    ax.scatter(ic_df['ic_mean'], ic_df['rankic_mean'], s=100, alpha=0.6)
    for i, symbol in enumerate(ic_df['symbol']):
        ax.annotate(symbol, (ic_df.iloc[i]['ic_mean'], ic_df.iloc[i]['rankic_mean']),
                   fontsize=8, alpha=0.7)
    ax.set_xlabel('IC')
    ax.set_ylabel('RankIC')
    ax.set_title('IC vs RankIC')
    ax.grid(True, alpha=0.3)
    
    # 添加对角线
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),
        np.max([ax.get_xlim(), ax.get_ylim()]),
    ]
    ax.plot(lims, lims, 'k--', alpha=0.5, zorder=0)
    
    # 4. 样本数
    ax = axes[1, 1]
    ax.bar(symbols, ic_df['n_samples'], alpha=0.7, edgecolor='black')
    ax.set_xlabel('标的')
    ax.set_ylabel('样本数')
    ax.set_title('各标的样本数')
    ax.set_xticklabels(symbols, rotation=45, ha='right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path("outputs/reports/day3_ofi_ic_summary.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Summary chart saved to {output_path}")


if __name__ == "__main__":
    generate_enhanced_report()
