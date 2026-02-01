# Research Log (Day0–Day3) — ETF LOB / OFI Pipeline

> 目标：在聚宽（JQData）拿到 ETF 五档盘口 tick 快照数据，落地到本地可复现的 repo 管线里；完成 OFI（Order Flow Imbalance）特征计算（先单标的单日跑通，再扩展到多 ETF、多日、自动化批处理），为后续研究/回测做数据与特征底座。

---

## 0. 项目约定与产出标准

### 0.1 研究问题（当前阶段）
- 用 **五档盘口快照** 构造 **OFI 特征**（level=5）。
- 先从 **单标的、单日** → **单标的、全样本日** → **多标的、全样本日** 扩展。

### 0.2 明确数据范围
- 选择规则
  - 流动性筛选：先用 成交额 Top 30 做候选池
  - 快照质量硬过滤（0成交/无报价/a1<b1 等）
  - 最后按 点差更小 + 快照更密 排序，只留 12 只

- ETF 列表（12只，按当前研究主线）：
  - 511360.XSHG, 511090.XSHG, 511380.XSHG, 518880.XSHG, 510500.XSHG,
  - 159919.XSHE, 510300.XSHG, 510310.XSHG, 159915.XSHE, 510050.XSHG,
  - 513090.XSHG, 588000.XSHG
- 时间范围：近 5 年（按平台可用范围获取/分批下载）。

### 0.3 Repo 结构与可复现性要求
- 本地 VSCode + GitHub 维护主 repo（数据不入 git）。
- **配置驱动**：所有关键参数（universe、数据路径、特征参数）用 `configs/*.yaml` 控制。
- 产出必须可追踪：每一天结束应有「能跑的脚本/配置」+「明确输出文件」+「日志记录」。

---

## Day0 — 搭建骨架 + 明确数据可得性 + 统一落地策略

### 当天目标
1) 明确：聚宽能提供什么盘口深度、什么频率、如何下载与搬运到本地。  
2) 建好 repo 骨架与配置框架（让后续不是“在 notebook 里手工改路径”）。  
3) 选定 ETF universe（先小而确定，保证 Day1–Day2 顺畅）。

### 做了什么 & 怎么做的
#### Step 0.1 选题收敛
- 在多个候选方向中确定：以 **微观结构因子（OFI）** 为主线。
- 原因：数据链条清晰、产出快、结果可视化（净值/IC/截面回归/日内图）容易做成作品。

#### Step 0.2 Repo 骨架落地（本地）
- 建立项目目录（典型结构）：
  - `configs/`：`universe.yaml`、`data.yaml`（核心）
  - `src/`：数据处理与特征计算脚本
  - `notebooks/`：探索与验证（但不承担配置与路径逻辑）
  - `data/`：本地缓存（写入 `.gitignore`）
  - `reports/`：研究输出与日志

#### Step 0.3 确认数据字段与“够不够做 OFI”
- 明确：JQData 只能提供 **5档盘口**，但足够完成 level=5 的 OFI（研究先从 5 档做，后续需要更深可再迁移数据源）。
- 确定保存字段（示例）：
  - 时间：`time`
  - 五档：`a1_p,b1_p,a1_v,b1_v,...,a5_p,b5_p,a5_v,b5_v`
  - 成交：`volume, money, current` 等（后续用于过滤/校验/回测对齐）

### 当天产出
- ✅ `configs/universe.yaml`：12只 ETF 列表固化
- ✅ repo 目录骨架 + `.gitignore`（data 不入 git）
- ✅ 数据字段清单与 OFI 可行性结论（level=5 可做）

---

## Day1 — 下载盘口 tick 数据 + 规范化存储 + 解决编码/磁盘/搬运问题

### 当天目标
1) 在聚宽研究环境批量下载 tick/盘口快照到平台文件系统。  
2) 打包下载到本地，并清理平台磁盘占用。  
3) 本地形成“可按 symbol/date 定位”的数据目录，后续直接用脚本读取。

### 做了什么 & 怎么做的
#### Step 1.1 在聚宽研究环境用 jqdata 批量拉取
- 使用聚宽研究环境（不是本地 `jqdatasdk`，因为本地权限/数据范围不足）。
- 下载策略：按「半年」分批拉取，避免单次任务过大、也便于失败重试。

#### Step 1.2 处理平台问题：磁盘满、文件不可编辑、无法新建终端
- 通过删除大文件、清空回收站、打包 zip 的方式释放空间。
- 最终形成工作流：  
  1) 下载一批 → 2) 压缩 zip → 3) 下载到本地 → 4) 删除平台原始文件与 zip → 5) 下一批


#### Step 1.3 存储格式选择（Parquet > CSV.gz）
- 讨论并确认：落地到本地后，后续分析/回测/聚合更推荐 parquet（列式、压缩、读写快、类型稳定）。
- Day1 阶段：平台端可能先 csv.gz（下载方便），本地可以逐步转 parquet（管线化）。

### 当天产出
- ✅ 平台端：tick/盘口快照数据按批次下载完成（并形成 zip 下载/清理流程）
- ✅ 本地端：数据落地到 repo 的 `data/` 下（不入 git）
- ✅ 明确存储策略：中长期转 parquet（便于 DuckDB/Polars/Pandas 高效处理）

---

## Day2 — 单标的单日 minute 聚合 OFI 跑通 + 配置化批处理雏形 + 路径问题定位

### 当天目标
1) 先跑通 **一只 ETF、一天** 的 minute-OFI 聚合（证明公式、字段、清洗都 OK）。  
2) 把流程“从 notebook 手工”升级成“配置驱动 + 可批处理”。  
3) 解决路径/工作目录导致的读取失败问题，避免每个 notebook 都要写补丁。

### 做了什么 & 怎么做的
#### Step 2.1 单标的单日 minute-OFI 计算跑通
- 输入：某 ETF 某交易日的盘口快照（五档）
- 处理：
  - 清洗：处理临近收盘的异常行（如 `price=0` 的脏点）
  - 计算：按 OFI 规则对五档逐档计算并聚合
  - 频率：tick → minute 聚合（你已完成该聚合结果）
- 输出：单日 minute 级别 OFI 序列（可用于画日内曲线、做回测特征）

#### Step 2.2 目录结构规范化（面向批处理）
- 采用分区式目录（关键是可定位、可并行）：
  - 示例：`data/processed/lob/symbol=XXXXXX/date=YYYY-MM-DD/part.parquet`

#### Step 2.3 配置化：用 `data.yaml` + `universe.yaml` 驱动 pipeline
- 目标是实现：一次运行，自动遍历 universe × dates，批量产出 minute-OFI。


### 当天产出
- ✅ 单 ETF 单日 minute-OFI 已跑通（证明特征计算链路成立）
- ✅ 配置化批处理框架已搭出（`data.yaml`/`universe.yaml` 驱动）
- ✅ 路径/工作目录问题已被明确识别为主阻塞点（不是公式问题）

---

## Day3 — 数据质量检查 + OFI信号统计显著性分析

### 当天目标
1) 对已有的 tick 数据和标签数据进行**全面质量检查**，确保数据可用性。  
2) 从 tick 数据**实时计算 OFI**，并与未来收益率标签匹配。  
3) 完成 **IC/RankIC 分析**和**分组收益分析**，验证 OFI 的预测能力。  
4) 产出标准化的研究报告，为后续策略开发提供依据。

### 做了什么 & 怎么做的

#### Step 3.1 构建分钟收益率标签
**目标**：为每个标的每天生成未来一分钟收益率，作为因子评估的标签。

**操作流程**：
1. 先在 `notebooks/Day3.ipynb` 中验证单日数据：
   - 读取 tick 数据，按分钟聚合
   - 计算中间价：`close = (a1_p + b1_p) / 2`
   - 计算未来收益率：`ret[t] = (close[t+1] - close[t]) / close[t]`
   - 验证逻辑：09:30 也应该有收益率（预测 09:31 的收益）

2. 编写批处理脚本 `scripts/build_labels.py`

3. 执行结果：
   - 成功生成 **7,271 个标签文件**（6 个标的 × 约 1,212 个交易日）
   - 每个文件包含约 240 行（交易时段的分钟数）
   - 数据格式：index 为 `minute` 时间戳，列为 `ret`（未来一分钟收益率）

#### Step 3.2 数据质量全面检查
**目标**：在进行因子分析前，先确保数据质量符合研究标准。

**编写脚本** `scripts/quality_check.py`，检查三个维度：

1. **分钟覆盖率**：
   - 预期：A股连续竞价时段约 240 分钟
   - 计算：`coverage = n_minutes / 240`
   - 目的：发现数据缺失严重的交易日

2. **订单簿异常率**：
   - `spread_negative`：买卖价差 ≤ 0 的比例
   - `mid_negative`：中间价 ≤ 0 的比例
   - `bid_ge_ask`：买一价 ≥ 卖一价的比例
   - 目的：识别盘口数据错误

3. **OFI 分布稳定性**：
   - 按天计算 OFI 的均值、标准差、分位数
   - 识别异常日（均值/标准差超过 5 倍整体标准差）
   - 目的：发现极端市场波动或数据异常

**执行结果**：
- 生成 `outputs/data_quality/day3_panel_summary.csv`（7,271 条记录）
- 生成 `outputs/data_quality/day3_ofi_distribution.png`（时序可视化）
- 生成 `outputs/data_quality/day3_quality_report.md`（完整报告）

**关键发现**：
- ✅ 分钟覆盖率均值 99.5%~100.5%（接近预期）
- ✅ 订单簿异常率 < 0.001%（数据质量良好）
- ⚠️ 1 个文件覆盖率 < 90%，需要人工检查
- ⚠️ 35 个文件 OFI 均值异常（可能是极端市场波动）

#### Step 3.3 OFI 信号统计显著性分析
**目标**：验证 OFI 是否具有预测未来收益的能力（不考虑交易成本）。

**策略调整**：
- 发现预计算的 OFI 数据存在问题（部分文件为空）
- 决定从 tick 数据**实时计算 OFI**，确保数据一致性

**编写脚本** `scripts/signal_analysis_v2.py`，完成以下分析：

1. **IC/RankIC 计算**（核心指标）：
   ```python
   # 对每个标的每天
   for symbol, date in all_data:
       # 加载 tick 数据并实时计算 OFI
       df = load_tick_data(symbol, date)
       ofi = compute_ofi_realtime(df, levels=5)
       
       # 按分钟聚合
       ofi_minute = ofi.resample('1min').sum()
       
       # 加载标签
       ret = load_label(symbol, date)
       
       # 对齐并计算相关性
       merged = pd.merge(ofi_minute, ret, left_index=True, right_index=True)
       ic = merged['ofi'].corr(merged['ret'])  # Pearson
       rank_ic = merged['ofi'].corr(merged['ret'], method='spearman')  # Spearman
   ```

2. **显著性检验**：
   - 对所有交易日的 IC 序列做 t 检验
   - 计算：`t_stat = mean(IC) / (std(IC) / sqrt(n))`
   - 判断：|t_stat| > 2 且 p < 0.05 为显著

3. **分组收益分析**：
   - 将每天的 OFI 分成 5 个分位数组（Q1-Q5）
   - 计算每组的平均未来收益率
   - 验证单调性：高 OFI 组的收益是否显著高于低 OFI 组

**执行结果**：

| 指标 | 数值 |
|------|------|
| 平均 RankIC | 0.0935 |
| 平均 IC | 0.0429 |
| t 统计量 | 10.35 |
| p 值 | < 0.0001 |
| 分析样本 | 7,271 个交易日 |

**各标的表现**：

| 标的 | RankIC | IC | t-stat |
|------|--------|-----|--------|
| 159915.XSHE | 0.1134 | 0.0534 | 11.51 |
| 159919.XSHE | 0.0971 | 0.0544 | 9.86 |
| 510050.XSHG | 0.1008 | 0.0600 | 10.23 |
| 510300.XSHG | 0.1061 | -0.0069 | 10.77 |
| 511380.XSHG | 0.0565 | 0.0294 | 5.73 |
| 518880.XSHG | 0.0871 | 0.0472 | 8.84 |

**分组收益分析**（以 159915.XSHE 为例）：

| 分组 | 平均收益率 (bps) |
|------|------------------|
| Q1 (最低OFI) | -0.52 |
| Q2 | -0.15 |
| Q3 | 0.08 |
| Q4 | 0.31 |
| Q5 (最高OFI) | 0.68 |

- ✅ 收益单调递增
- ✅ Q5-Q1 价差 = 1.20 bps（显著为正）

#### Step 3.4 生成研究报告
**产出文件**：
1. `outputs/reports/day3_ofi_signal_enhanced.md`：完整分析报告
2. `outputs/reports/day3_ofi_ic_summary.csv`：IC 数据表
3. `outputs/reports/day3_ofi_ic_summary.png`：IC 汇总图表
4. `outputs/reports/day3_ofi_quintile_*.png`：6 个标的的分组收益图

**报告核心结论**：
1. **OFI 具有显著预测能力**：
   - RankIC = 0.0935（t=10.35，p<0.0001）
   - 6 个标的全部显著为正

2. **单调性强于线性性**：
   - RankIC > IC，说明 OFI 与收益更多是单调关系
   - 建议使用排序策略或分组策略

3. **策略想法**：
   - 持仓周期：1 分钟
   - 做多高 OFI，做空低 OFI

### 当天产出
- ✅ `data/labels/minute_returns/`：7,271 个标签文件
- ✅ `outputs/data_quality/`：质量检查报告和图表
- ✅ `outputs/reports/day3_ofi_signal_enhanced.md`：完整分析报告
- ✅ `scripts/build_labels.py`：标签构建脚本
- ✅ `scripts/quality_check.py`：质量检查脚本
- ✅ `scripts/signal_analysis_v2.py`：信号分析脚本

### 关键经验
1. **实时计算 > 预计算**：当预计算数据有问题时，从原始数据重新计算更可靠
2. **质量检查先行**：在因子分析前做全面质量检查，避免被脏数据误导
3. **RankIC 更稳健**：对于高频因子，Spearman 相关性比 Pearson 更能反映单调关系
4. **分组分析验证单调性**：不仅要看 IC，还要看分组收益的单调性和稳定性

---