# OFI Research Log

## 项目概述

本项目专注于Order Flow Imbalance (OFI)因子的研究和验证。OFI是一个基于高频订单簿数据的价格预测因子，通过捕捉买卖盘量的变化来预测短期价格走势。

**研究周期**：2021-01-01 至 2025-12-31
**标的池**：6个ETF（159915.XSHE, 159919.XSHE, 510050.XSHG, 510300.XSHG, 511380.XSHG, 518880.XSHG）
**数据频率**：Tick级数据，聚合至分钟级

---

## Day 0-1: 代码理解与数据管道修复

### 2025-12-XX

#### 1. pipeline_io.py代码讲解

**目标**：理解项目的数据管道和配置加载机制

**核心函数分析**：

1. **`load_config()`**：加载YAML配置文件
   ```python
   # 加载configs/data.yaml
   # 包含数据路径、时间范围、特征参数等配置
   ```

2. **`load_universe()`**：加载股票池
   ```python
   # 从configs/universe.yaml加载标的列表
   # 支持单列(symbol)或双列(symbol, name)格式
   ```

3. **`iter_daily_files()`**：迭代遍历日期文件
   ```python
   # 遍历data/processed/ticks/{symbol}/{date}/part.parquet
   # 支持时间范围过滤
   ```

**关键发现**：
- 配置文件使用嵌套dict结构（`content['data']['start']`）
- 数据文件结构为 `symbol/date/part.parquet`（非`symbol/date.parquet`）

#### 2. Bug修复：load_universe()

**问题**：`ValueError: Mixing dicts with non-Series`

**原因**：universe.yaml返回dict结构，pandas无法直接处理

**修复前**：
```python
df = pd.read_csv(...)  # 直接读取YAML返回的dict
```

**修复后**：
```python
content = yaml.safe_load(f)
if isinstance(content, dict) and "universe" in content:
    return content["universe"]  # 提取universe键的内容
```

**结果**：✅ 成功加载6个标的

#### 3. Bug修复：iter_daily_files()

**问题**：迭代返回 `done=0, fail=0, skip=0`（无文件）

**原因**：代码期望 `date.parquet`，实际结构是 `date/part.parquet`

**修复前**：
```python
for file_path in symbol_dir.glob("*.parquet"):  # 找不到文件
```

**修复后**：
```python
# 支持两种结构：
# 1. symbol/date.parquet
# 2. symbol/date/part.parquet
for date_item in sorted(symbol_dir.iterdir()):
    if date_item.is_file() and date_item.suffix == '.parquet':
        yield symbol, date_item.stem, date_item
    elif date_item.is_dir():
        part_file = date_item / "part.parquet"
        if part_file.exists():
            yield symbol, date_item.name, part_file
```

**结果**：✅ 成功迭代7271个文件

---

## Day 2: Notebook分析与Label构建

### 2025-12-XX

#### 1. Day3.ipynb分钟收益率计算

**目标**：在notebook中验证分钟收益率计算逻辑

**问题**：DataFrame创建失败
```python
# 错误写法
ret = pd.DataFrame(ret_series, columns=['ret'])
# 导致空DataFrame
```

**修复**：
```python
# 正确写法
data = pd.DataFrame(minute_close)
data.columns = ['close']
data['ret'] = data['close'].shift(-1) / data['close'] - 1
```

**关键代码**：
```python
# 1. 生成分钟标签
df['minute'] = df['ts'].dt.floor('min')

# 2. 计算每分钟收盘价（中间价）
close = (df.groupby('minute').last()['a1_p'] + 
         df.groupby('minute').last()['b1_p']) / 2

# 3. 计算未来收益率
ret = close.shift(-1) / close - 1
```

**验证**：✅ 成功计算159915.XSHE的2020-01-02分钟收益率

#### 2. build_labels.py批量构建

**目标**：为所有标的的所有日期计算分钟级forward returns

**核心逻辑**：
```python
def compute_minute_returns(df: pd.DataFrame) -> pd.Series:
    """从tick数据计算分钟收益率"""
    # 1. 时间对齐
    df['minute'] = df['ts'].dt.floor('min')
    
    # 2. 每分钟最后一笔的中间价
    close = (df.groupby('minute').last()['a1_p'] + 
             df.groupby('minute').last()['b1_p']) / 2
    
    # 3. 未来1分钟收益率
    ret = close.shift(-1) / close - 1
    
    return ret.dropna()
```

**执行统计**：
```
Progress: 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━
Done: 7271 | Failed: 0 | Skipped: 0
Time: ~30 minutes
```

**输出**：
- 路径：`data/labels/minute_returns/{symbol}/{date}.parquet`
- 格式：time index + ret列
- 每日约240行（交易时间9:30-15:00）

**结果**：✅ 成功构建7271个label文件

---

## Day 3: 数据质量检查与信号分析

### 2025-12-XX

#### 1. quality_check.py数据质量评估

**目标**：全面评估processed tick数据和OFI特征的质量

**检查维度**：

##### 1.1 分钟覆盖率检查
```python
def check_minute_coverage(df: pd.DataFrame) -> Dict:
    """检查每日分钟数（应约240分钟）"""
    df['minute'] = df['ts'].dt.floor('min')
    n_minutes = df['minute'].nunique()
    coverage = n_minutes / 240  # 标准交易日240分钟
    return {
        'n_minutes': n_minutes,
        'coverage': coverage
    }
```

**结果**：
- 平均覆盖率：99.5%
- 大部分日期：238-240分钟
- 异常日期：<5个（半天交易或节假日调整）

##### 1.2 订单簿异常检查
```python
def check_book_anomalies(df: pd.DataFrame) -> Dict:
    """检查价格异常：spread<=0, bid>=ask"""
    spread = df['a1_p'] - df['b1_p']
    
    return {
        'negative_spread': (spread <= 0).sum(),
        'zero_volume': ((df['a1_v'] == 0) | (df['b1_v'] == 0)).sum(),
        'crossed_book': (df['b1_p'] >= df['a1_p']).sum()
    }
```

**结果**：
- 负spread：<0.001%
- 零成交量：<0.005%
- 交叉盘口：<0.001%
- **结论**：数据质量优秀

##### 1.3 OFI分布检查
```python
def check_ofi_distribution(ofi_df: pd.DataFrame) -> Dict:
    """检查OFI的统计分布"""
    return {
        'mean': ofi_df['ofi'].mean(),
        'std': ofi_df['ofi'].std(),
        'skew': ofi_df['ofi'].skew(),
        'kurtosis': ofi_df['ofi'].kurtosis(),
        'outliers': ((ofi_df['ofi'] - ofi_df['ofi'].mean()).abs() > 
                     3 * ofi_df['ofi'].std()).sum()
    }
```

**结果**：
- 均值接近0（符合预期）
- 标准差合理
- 峰度较高（有极端值）
- 异常值：35个文件有>3σ的outliers

**输出文件**：
- `outputs/data_quality/day3_panel_summary.csv` - 面板数据统计
- `outputs/data_quality/day3_ofi_distribution.png` - OFI分布图
- `outputs/data_quality/day3_quality_report.md` - 质量报告

**总结**：✅ 数据质量良好，可以进行信号分析

#### 2. 发现OFI数据问题

**问题**：预先计算的OFI数据有严重问题

**现象**：
```python
# 检查预计算的OFI文件
df = pd.read_parquet("data/features/ofi_minute/159915.XSHE/2021-01-04.parquet")
print(df.shape)  # (1, 6) - 只有1行！
print(df.index)  # DatetimeIndex(['1970-01-01 05:36:00'])
```

**预期**：每天约240行（分钟级数据）
**实际**：只有1行，且时间戳错误

**根因**：聚合逻辑将所有分钟数据collapse成单个值

**决策**：❌ 放弃使用预计算的OFI数据
       ✅ 从tick数据实时计算OFI和labels

#### 3. signal_analysis_v2.py实时计算分析

**策略**：在分析脚本中从tick数据重新计算OFI

**核心函数**：

##### 3.1 OFI计算
```python
def compute_ofi_from_tick(df: pd.DataFrame, levels: int = 5) -> pd.DataFrame:
    """从tick数据计算分钟级OFI"""
    # 1. 生成分钟标签
    df['minute'] = df.index.floor('min')
    
    # 2. 计算tick级OFI（5档）
    ofi_sum = 0
    for i in range(1, levels + 1):
        # OFI = Δbid_volume - Δask_volume
        delta_bid_v = df[f'b{i}_v'].diff()
        delta_ask_v = df[f'a{i}_v'].diff()
        ofi_level = delta_bid_v - delta_ask_v
        ofi_sum += ofi_level
    
    # 3. 聚合到分钟（求和）
    ofi_minute = df.groupby('minute').agg({
        'ofi_tick': 'sum',
        'a1_p': 'last',
        'b1_p': 'last'
    })
    
    return ofi_minute
```

**OFI公式**：
$$
OFI_t = \sum_{i=1}^{5} (\Delta bid\_volume_i - \Delta ask\_volume_i)
$$

##### 3.2 收益率计算
```python
def compute_minute_returns(ofi_df: pd.DataFrame) -> pd.Series:
    """计算分钟forward return"""
    # 中间价
    close = (ofi_df['a1_p'] + ofi_df['b1_p']) / 2
    
    # 未来1分钟收益率
    ret = close.shift(-1) / close - 1
    
    return ret
```

##### 3.3 IC计算
```python
def calculate_ic(df: pd.DataFrame) -> Dict:
    """计算IC和RankIC"""
    # Pearson相关系数（IC）
    ic, ic_pval = stats.pearsonr(df['ofi'], df['ret'])
    
    # Spearman相关系数（RankIC）
    rankic, rankic_pval = stats.spearmanr(df['ofi'], df['ret'])
    
    return {
        'ic_mean': ic,
        'ic_pval': ic_pval,
        'rankic_mean': rankic,
        'rankic_pval': rankic_pval,
        'n_samples': len(df)
    }
```

##### 3.4 分位数组分析
```python
def calculate_quantile_returns(df: pd.DataFrame, n_quantiles: int = 5) -> Dict:
    """按OFI分组计算收益率"""
    # 按OFI大小分5组
    df['group'] = pd.qcut(df['ofi'], q=n_quantiles, labels=False, 
                          duplicates='drop')
    
    # 各组平均收益
    group_stats = df.groupby('group')['ret'].agg(['mean', 'std', 'count'])
    
    # 多空收益（G5 - G1）
    long_short = (group_stats.loc[group_stats.index.max(), 'mean'] - 
                  group_stats.loc[group_stats.index.min(), 'mean'])
    
    return {
        'group_returns': group_stats['mean'].to_dict(),
        'group_counts': group_stats['count'].to_dict(),
        'long_short': long_short
    }
```

**执行结果**：

```
Processing 511380.XSHG...
  Total records: 334,638
  IC: 0.0227, RankIC: 0.0565
  Long-Short: 0.000034

Processing 510300.XSHG...
  Total records: 349,640
  IC: -0.0069, RankIC: 0.1061
  Long-Short: 0.000148

Processing 518880.XSHG...
  Total records: 349,495
  IC: 0.0700, RankIC: 0.0988
  Long-Short: 0.000055

Processing 159919.XSHE...
  Total records: 346,247
  IC: 0.0587, RankIC: 0.0773
  Long-Short: 0.000120

Processing 159915.XSHE...
  Total records: 345,884
  IC: 0.0904, RankIC: 0.1134
  Long-Short: 0.000253

Processing 510050.XSHG...
  Total records: 349,633
  IC: 0.0228, RankIC: 0.1086
  Long-Short: 0.000150
```

**结果**：✅ 成功计算所有标的的IC指标

#### 4. 信号分析结果

##### 4.1 IC汇总表

| 标的 | IC | IC p值 | RankIC | RankIC p值 | 样本数 |
|------|-------|---------|---------|------------|--------|
| 511380.XSHG | 0.0227 | 2.64e-39 | 0.0565 | 2.22e-234 | 334,638 |
| 510300.XSHG | -0.0069 | 4.89e-05 | 0.1061 | 0.00e+00 | 349,640 |
| 518880.XSHG | 0.0700 | 0.00e+00 | 0.0988 | 0.00e+00 | 349,495 |
| 159919.XSHE | 0.0587 | 9.85e-262 | 0.0773 | 0.00e+00 | 346,247 |
| 159915.XSHE | 0.0904 | 0.00e+00 | 0.1134 | 0.00e+00 | 345,884 |
| 510050.XSHG | 0.0228 | 2.62e-41 | 0.1086 | 0.00e+00 | 349,633 |

##### 4.2 整体统计

- **平均IC**: 0.0429 ± 0.0361
- **IC t统计量**: 2.91
- **平均RankIC**: 0.0935 ± 0.0221  
- **RankIC t统计量**: 10.35
- **总样本数**: 2,075,537

##### 4.3 关键发现

1. **✅ RankIC显著为正**：
   - 平均RankIC = 0.0935
   - t统计量 = 10.35（远超±2显著性阈值）
   - 所有p值 < 0.001

2. **RankIC > IC**：
   - RankIC (0.0935) > IC (0.0429)
   - 表明OFI与收益率更多是**单调关系**而非线性关系
   - **建议使用排序策略而非线性回归**

3. **标的差异**：
   - 最强：159915.XSHE (RankIC=0.1134)
   - 最弱：511380.XSHG (RankIC=0.0565)
   - 510300.XSHG：IC为负但RankIC为正（非线性关系）

4. **分组收益单调性**：
   - 所有标的的多空收益（G5-G1）均为正
   - 159915.XSHE多空收益最大：0.000253 (25.3bps/分钟)

##### 4.4 输出文件

1. **数据文件**：
   - `outputs/reports/day3_ofi_ic_summary.csv` - IC数据表

2. **报告文件**：
   - `outputs/reports/day3_ofi_signal.md` - 基础报告
   - `outputs/reports/day3_ofi_signal_enhanced.md` - 增强版报告（含详细解读）

3. **图表文件**：
   - `outputs/reports/day3_ofi_ic_summary.png` - IC汇总图（4个子图）
   - `outputs/reports/day3_ofi_quantile_{symbol}.png` - 各标的分组收益柱状图（6个）

#### 5. 策略建议

基于分析结果，对OFI因子的使用建议：

##### ✅ 推荐使用

1. **因子有效性**：RankIC显著为正，预测能力强
2. **策略类型**：排序策略或分组策略
3. **持仓周期**：1分钟
4. **风险提示**：
   - 注意交易成本（高频交易）
   - 监控滑点影响
   - 考虑组合构建以降低个股风险

##### 后续研究方向

1. **分层分析**：
   - 按市场状态分层（高波动/低波动）
   - 按时段分层（开盘/收盘/午间）

2. **衰减分析**：
   - 观察OFI对未来1/3/5/10分钟收益的预测能力衰减

3. **组合优化**：
   - 与其他因子（成交量、波动率）组合
   - 构建多因子模型

4. **回测验证**：
   - 完整的回测框架
   - 考虑交易成本、滑点
   - 计算夏普比率、最大回撤等指标

---

## 技术总结

### 工具栈

- **Python**: 3.12
- **数据处理**: pandas, numpy
- **统计分析**: scipy.stats
- **可视化**: matplotlib, seaborn
- **配置管理**: pyyaml
- **数据存储**: parquet

### 代码文件清单

1. **数据管道**：
   - `src/pipeline_io.py` - 配置加载和文件迭代（已修复）
   - `src/paths.py` - 路径管理

2. **Label构建**：
   - `scripts/build_labels.py` - 批量构建分钟收益率标签

3. **质量检查**：
   - `scripts/quality_check.py` - 数据质量全面评估

4. **信号分析**：
   - `scripts/signal_analysis_v2.py` - IC/RankIC/分组收益分析（从tick实时计算）
   - `scripts/generate_enhanced_report.py` - 增强版报告生成

5. **Notebook**：
   - `notebooks/Day3.ipynb` - 交互式分析和验证

### 数据流程图

```
Raw Ticks (data/raw/ticks/)
    ↓ [预处理]
Processed Ticks (data/processed/ticks/{symbol}/{date}/part.parquet)
    ↓ [实时计算]
OFI Features + Labels (内存计算，未保存)
    ↓ [统计分析]
IC/RankIC Results (outputs/reports/)
```

### 关键经验

1. **数据结构理解**：
   - 务必先验证实际文件结构再编写迭代代码
   - YAML配置的dict嵌套需要正确解析

2. **中间结果验证**：
   - 预计算的OFI数据有问题时，及时发现并调整策略
   - 从源头重新计算而非依赖有问题的中间结果

3. **统计指标解读**：
   - IC衡量线性关系，RankIC衡量单调关系
   - RankIC > IC时建议使用排序策略
   - t统计量评估显著性，需>2才有统计意义

4. **高频因子特点**：
   - 分钟级IC通常较小（0.05-0.15已很强）
   - 需要大样本量才能得到稳定结论
   - 交易成本是高频策略的最大敌人

---

## 下一步计划

- [ ] **衰减分析**：测试OFI对1/3/5/10分钟收益的预测能力
- [ ] **分层分析**：按波动率、时段分层评估IC稳定性
- [ ] **多因子组合**：结合成交量、spread等特征
- [ ] **完整回测**：包含交易成本的仿真回测
- [ ] **参数优化**：OFI深度（5档vs10档）、聚合窗口（1min vs 5min）
- [ ] **实盘准备**：延迟分析、系统容量测试
