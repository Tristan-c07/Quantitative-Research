# Quantitative Research | 量化交易研究

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## 📈 Quantitative Trading Research Portfolio

A comprehensive quantitative trading research repository featuring strategy development, backtesting, and analysis on the JoinQuant platform. This project demonstrates professional-level quantitative research skills suitable for portfolio showcasing.

### 🎯 Project Overview

This repository contains:
- **Multiple trading strategies** implemented for the JoinQuant platform
- **Research notebooks** for strategy development and analysis
- **Utility functions** for data processing and performance evaluation
- **Documentation** for strategy implementation and best practices

### 📁 Project Structure

```
Quantitative-Research/
├── strategies/          # Trading strategies
│   ├── ma_crossover.py     # Moving Average Crossover Strategy
│   ├── mean_reversion.py   # Mean Reversion Strategy
│   └── momentum.py         # Momentum Strategy
├── research/           # Jupyter notebooks for research
│   ├── strategy_analysis.ipynb
│   └── market_research.ipynb
├── utils/              # Utility functions
│   ├── data_loader.py      # Data fetching utilities
│   ├── indicators.py       # Technical indicators
│   └── performance.py      # Performance metrics
├── docs/               # Documentation
│   ├── strategy_guide.md
│   └── joinquant_guide.md
├── data/               # Data storage
│   ├── raw/               # Raw data
│   └── processed/         # Processed data
├── requirements.txt    # Python dependencies
└── README.md
```

### 🚀 Getting Started

#### Prerequisites
- Python 3.7+
- JoinQuant account (聚宽平台账号)

#### Installation

1. Clone the repository:
```bash
git clone https://github.com/Tristan-c07/Quantitative-Research.git
cd Quantitative-Research
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install TA-Lib for technical analysis:
```bash
# On Ubuntu/Debian
sudo apt-get install ta-lib

# On macOS
brew install ta-lib

# Then install Python wrapper
pip install TA-Lib
```

### 📊 Strategy Examples

#### 1. Moving Average Crossover Strategy
A classic trend-following strategy that generates buy signals when short-term MA crosses above long-term MA.

#### 2. Mean Reversion Strategy
Identifies overbought/oversold conditions and trades on the assumption that prices will revert to the mean.

#### 3. Momentum Strategy
Capitalizes on market momentum by identifying and following strong trends.

### 📚 Usage

#### Running Strategies on JoinQuant

1. Copy the strategy code from `strategies/` folder
2. Log in to [JoinQuant Platform](https://www.joinquant.com)
3. Create a new strategy and paste the code
4. Configure parameters and run backtest

#### Local Research

```python
from utils.data_loader import load_stock_data
from utils.indicators import calculate_ma
from utils.performance import calculate_returns

# Load data
data = load_stock_data('000001.XSHE', '2020-01-01', '2023-12-31')

# Calculate indicators
data = calculate_ma(data, periods=[20, 60])

# Analyze performance
returns = calculate_returns(data)
```

### 📈 Performance Metrics

All strategies include comprehensive performance analysis:
- Sharpe Ratio
- Maximum Drawdown
- Annual Returns
- Win Rate
- Profit Factor

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### 📧 Contact

For questions or collaboration opportunities, please open an issue or contact through GitHub.

---

<a name="chinese"></a>
## 📈 量化交易研究作品集

一个全面的量化交易研究仓库，包含在聚宽平台上的策略开发、回测和分析。本项目展示了专业级别的量化研究技能，适合作为个人作品集展示。

### 🎯 项目概述

本仓库包含：
- 在聚宽平台上实现的**多种交易策略**
- 用于策略开发和分析的**研究笔记本**
- 用于数据处理和性能评估的**工具函数**
- 策略实现和最佳实践的**文档**

### 📁 项目结构

```
Quantitative-Research/
├── strategies/          # 交易策略
│   ├── ma_crossover.py     # 均线交叉策略
│   ├── mean_reversion.py   # 均值回归策略
│   └── momentum.py         # 动量策略
├── research/           # Jupyter研究笔记本
│   ├── strategy_analysis.ipynb
│   └── market_research.ipynb
├── utils/              # 工具函数
│   ├── data_loader.py      # 数据获取工具
│   ├── indicators.py       # 技术指标
│   └── performance.py      # 性能指标
├── docs/               # 文档
│   ├── strategy_guide.md
│   └── joinquant_guide.md
├── data/               # 数据存储
│   ├── raw/               # 原始数据
│   └── processed/         # 处理后的数据
├── requirements.txt    # Python依赖
└── README.md
```

### 🚀 快速开始

#### 前置要求
- Python 3.7+
- 聚宽平台账号

#### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/Tristan-c07/Quantitative-Research.git
cd Quantitative-Research
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. （可选）安装 TA-Lib 用于技术分析：
```bash
# Ubuntu/Debian 系统
sudo apt-get install ta-lib

# macOS 系统
brew install ta-lib

# 然后安装 Python 包装器
pip install TA-Lib
```

### 📊 策略示例

#### 1. 均线交叉策略
经典的趋势跟踪策略，当短期均线上穿长期均线时产生买入信号。

#### 2. 均值回归策略
识别超买/超卖状态，基于价格将回归均值的假设进行交易。

#### 3. 动量策略
通过识别和跟随强劲趋势来捕捉市场动量。

### 📚 使用方法

#### 在聚宽平台运行策略

1. 从 `strategies/` 文件夹复制策略代码
2. 登录[聚宽平台](https://www.joinquant.com)
3. 创建新策略并粘贴代码
4. 配置参数并运行回测

#### 本地研究

```python
from utils.data_loader import load_stock_data
from utils.indicators import calculate_ma
from utils.performance import calculate_returns

# 加载数据
data = load_stock_data('000001.XSHE', '2020-01-01', '2023-12-31')

# 计算指标
data = calculate_ma(data, periods=[20, 60])

# 分析性能
returns = calculate_returns(data)
```

### 📈 性能指标

所有策略都包含全面的性能分析：
- 夏普比率
- 最大回撤
- 年化收益率
- 胜率
- 盈亏比

### 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

### 📝 许可证

本项目采用 Apache License 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

### 📧 联系方式

如有问题或合作机会，请通过 GitHub 开启 issue 或联系。