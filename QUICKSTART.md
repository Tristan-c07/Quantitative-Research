# Quick Start Guide | 快速开始指南

## 🚀 快速开始 (Quick Start)

### 1. 克隆项目 (Clone Repository)
```bash
git clone https://github.com/Tristan-c07/Quantitative-Research.git
cd Quantitative-Research
```

### 2. 安装依赖 (Install Dependencies)
```bash
pip install -r requirements.txt
```

### 3. 开始使用 (Start Using)

#### 方式一：在聚宽平台运行策略 (Run on JoinQuant)
1. 打开 `strategies/` 文件夹
2. 选择一个策略文件（如 `ma_crossover.py`）
3. 复制代码到[聚宽平台](https://www.joinquant.com)
4. 设置回测参数并运行

#### 方式二：本地研究分析 (Local Research)
```bash
jupyter notebook research/strategy_analysis.ipynb
```

## 📚 文档导航 (Documentation)

- [README.md](README.md) - 项目概述 | Project Overview
- [docs/joinquant_guide.md](docs/joinquant_guide.md) - 聚宽平台使用指南 | JoinQuant Guide
- [docs/strategy_guide.md](docs/strategy_guide.md) - 策略开发指南 | Strategy Development Guide

## 📊 策略列表 (Strategies)

### 1. 均线交叉策略 (Moving Average Crossover)
- **文件**: `strategies/ma_crossover.py`
- **类型**: 趋势跟踪
- **特点**: 简单有效，适合初学者
- **参数**: 短期均线(10日)，长期均线(30日)

### 2. 均值回归策略 (Mean Reversion)
- **文件**: `strategies/mean_reversion.py`
- **类型**: 均值回归
- **特点**: 基于布林带，适合震荡市
- **参数**: 布林带周期(20日)，标准差倍数(2)

### 3. 动量策略 (Momentum)
- **文件**: `strategies/momentum.py`
- **类型**: 动量交易
- **特点**: 多股票选择，风险分散
- **参数**: 动量周期(20日)，RSI周期(14日)

## 🛠️ 工具函数 (Utilities)

### 数据加载 (Data Loading)
```python
from utils.data_loader import load_stock_data

data = load_stock_data('000001.XSHE', '2023-01-01', '2023-12-31')
```

### 技术指标 (Technical Indicators)
```python
from utils.indicators import calculate_ma, calculate_macd, calculate_rsi

data_ma = calculate_ma(data, periods=[5, 10, 20])
data_macd = calculate_macd(data)
data_rsi = calculate_rsi(data)
```

### 性能分析 (Performance Analysis)
```python
from utils.performance import generate_performance_report

returns = calculate_returns(data)
report = generate_performance_report(returns)
```

## 📈 性能指标 (Performance Metrics)

本项目提供的性能指标包括：
- **夏普比率** (Sharpe Ratio) - 风险调整后收益
- **最大回撤** (Maximum Drawdown) - 最大损失
- **年化收益率** (Annual Return) - 年化表现
- **胜率** (Win Rate) - 盈利交易占比
- **盈亏比** (Profit Factor) - 总盈利/总亏损

## 🎯 使用场景 (Use Cases)

### 1. 学习量化交易
- 研究策略代码
- 理解技术指标
- 学习风险管理

### 2. 策略回测
- 在聚宽平台回测
- 本地数据分析
- 参数优化

### 3. 作品集展示
- 展示编程能力
- 展示金融知识
- 展示分析能力

## ⚠️ 免责声明 (Disclaimer)

本项目仅供学习和研究使用，不构成任何投资建议。
量化交易存在风险，投资需谨慎。

This project is for educational and research purposes only. 
Not investment advice. Trading involves risks.

## 📧 联系方式 (Contact)

- GitHub Issues: [提问和建议](https://github.com/Tristan-c07/Quantitative-Research/issues)
- Pull Requests: 欢迎贡献代码

## 📝 License

Apache License 2.0 - 详见 [LICENSE](LICENSE) 文件
