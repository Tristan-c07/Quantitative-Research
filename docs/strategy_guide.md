# 策略开发指南 | Strategy Development Guide

[中文](#chinese) | [English](#english)

---

<a name="chinese"></a>
## 策略开发指南

### 策略开发流程

一个完整的量化策略开发流程包括：

```
1. 策略构思 → 2. 数据分析 → 3. 策略编写 → 4. 回测验证 → 5. 参数优化 → 6. 风险评估 → 7. 模拟交易
```

### 1. 策略构思

#### 常见策略类型

**趋势跟踪策略**
- 均线交叉策略
- 突破策略
- 动量策略

**均值回归策略**
- 布林带策略
- 配对交易
- 统计套利

**事件驱动策略**
- 财报驱动
- 新闻驱动
- 公司行为驱动

#### 策略要素

一个好的策略应包含：

1. **明确的买入信号**
   - 基于技术指标
   - 基于基本面
   - 基于市场情绪

2. **明确的卖出信号**
   - 止损条件
   - 止盈条件
   - 信号反转

3. **风险管理**
   - 仓位控制
   - 止损设置
   - 最大回撤控制

### 2. 数据分析

#### 探索性数据分析

```python
import pandas as pd
from utils.data_loader import load_stock_data
from utils.indicators import calculate_all_indicators

# 加载数据
data = load_stock_data('000001.XSHE', '2020-01-01', '2023-12-31')

# 计算技术指标
data = calculate_all_indicators(data)

# 查看统计信息
print(data.describe())

# 查看相关性
print(data.corr())
```

#### 可视化分析

```python
import matplotlib.pyplot as plt

# 绘制价格走势
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['close'], label='Close Price')
plt.plot(data.index, data['MA20'], label='MA20')
plt.plot(data.index, data['MA60'], label='MA60')
plt.legend()
plt.title('Price and Moving Averages')
plt.show()
```

### 3. 策略编写

#### 基本框架

```python
def initialize(context):
    """初始化"""
    # 设置基准
    set_benchmark('000300.XSHG')
    
    # 设置股票池
    g.stocks = ['000001.XSHE', '600519.XSHG']
    
    # 设置策略参数
    g.param1 = 10
    g.param2 = 20
    
    # 设置运行时间
    run_daily(market_open, time='9:30')
    run_daily(market_close, time='14:50')


def market_open(context):
    """开盘时运行"""
    for stock in g.stocks:
        # 获取数据
        data = get_data(stock)
        
        # 生成信号
        signal = generate_signal(data)
        
        # 执行交易
        if signal == 'buy':
            buy_stock(context, stock)
        elif signal == 'sell':
            sell_stock(context, stock)


def generate_signal(data):
    """生成交易信号"""
    # 这里实现你的交易逻辑
    pass
```

#### 代码规范

1. **函数注释**
```python
def calculate_signal(price, volume):
    """
    计算交易信号
    
    Parameters:
    -----------
    price : float
        当前价格
    volume : int
        成交量
    
    Returns:
    --------
    str : 'buy', 'sell', or 'hold'
    """
    pass
```

2. **日志记录**
```python
log.info(f"买入 {stock} 价格: {price}")
log.warning(f"账户资金不足")
log.error(f"获取数据失败: {error}")
```

### 4. 回测验证

#### 回测设置

```python
# 回测时间段
start_date = '2020-01-01'
end_date = '2023-12-31'

# 初始资金
initial_capital = 100000

# 手续费设置
commission_rate = 0.0003
```

#### 性能评估

```python
from utils.performance import generate_performance_report

# 计算收益率
returns = calculate_returns(portfolio_value)

# 生成报告
report = generate_performance_report(returns, initial_capital)
print_performance_report(report)
```

### 5. 参数优化

#### 网格搜索

```python
# 定义参数范围
short_periods = [5, 10, 15, 20]
long_periods = [30, 40, 50, 60]

best_sharpe = -np.inf
best_params = None

# 遍历所有参数组合
for short in short_periods:
    for long in long_periods:
        if short >= long:
            continue
        
        # 使用当前参数运行回测
        result = run_backtest(short, long)
        
        # 评估性能
        if result['sharpe'] > best_sharpe:
            best_sharpe = result['sharpe']
            best_params = (short, long)

print(f"最优参数: short={best_params[0]}, long={best_params[1]}")
print(f"夏普比率: {best_sharpe:.2f}")
```

### 6. 风险评估

#### 关键风险指标

1. **最大回撤**
   - 衡量策略最大损失
   - 建议 < 30%

2. **夏普比率**
   - 衡量风险调整后收益
   - 建议 > 1.0

3. **胜率**
   - 交易成功的比例
   - 建议 > 50%

4. **盈亏比**
   - 平均盈利/平均亏损
   - 建议 > 1.5

#### 风险控制措施

```python
# 单只股票仓位限制
max_position_per_stock = 0.2  # 20%

# 最大总仓位
max_total_position = 0.95  # 95%

# 止损比例
stop_loss_pct = 0.05  # 5%

# 止盈比例
take_profit_pct = 0.15  # 15%
```

### 7. 常见陷阱

#### 过拟合

**问题：** 参数过度优化导致回测表现好但实盘表现差

**解决方案：**
- 使用样本外测试
- 保持策略简单
- 避免过多参数

#### 未来函数

**问题：** 使用了当时无法获得的数据

**解决方案：**
- 仔细检查数据时间戳
- 避免使用整个周期的统计量

#### 幸存者偏差

**问题：** 只考虑存活的股票，忽略退市股票

**解决方案：**
- 使用包含退市股票的数据
- 及时剔除ST股票

### 最佳实践

1. **从简单开始**
   - 先实现基础版本
   - 逐步添加功能

2. **版本控制**
   - 使用Git管理代码
   - 记录每次修改

3. **文档化**
   - 记录策略逻辑
   - 说明参数含义

4. **持续监控**
   - 定期检查策略表现
   - 及时调整参数

---

<a name="english"></a>
## Strategy Development Guide

### Strategy Development Process

A complete quantitative strategy development process includes:

```
1. Strategy Idea → 2. Data Analysis → 3. Strategy Coding → 4. Backtesting → 5. Optimization → 6. Risk Assessment → 7. Paper Trading
```

### 1. Strategy Conception

#### Common Strategy Types

**Trend Following**
- Moving average crossover
- Breakout strategies
- Momentum strategies

**Mean Reversion**
- Bollinger Bands strategy
- Pairs trading
- Statistical arbitrage

**Event-Driven**
- Earnings-driven
- News-driven
- Corporate action-driven

#### Strategy Components

A good strategy should include:

1. **Clear Entry Signals**
   - Based on technical indicators
   - Based on fundamentals
   - Based on market sentiment

2. **Clear Exit Signals**
   - Stop loss conditions
   - Take profit conditions
   - Signal reversal

3. **Risk Management**
   - Position sizing
   - Stop loss settings
   - Maximum drawdown control

### 2. Data Analysis

#### Exploratory Data Analysis

```python
import pandas as pd
from utils.data_loader import load_stock_data
from utils.indicators import calculate_all_indicators

# Load data
data = load_stock_data('000001.XSHE', '2020-01-01', '2023-12-31')

# Calculate technical indicators
data = calculate_all_indicators(data)

# View statistics
print(data.describe())

# View correlations
print(data.corr())
```

#### Visualization

```python
import matplotlib.pyplot as plt

# Plot price trends
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['close'], label='Close Price')
plt.plot(data.index, data['MA20'], label='MA20')
plt.plot(data.index, data['MA60'], label='MA60')
plt.legend()
plt.title('Price and Moving Averages')
plt.show()
```

### 3. Strategy Coding

#### Basic Framework

```python
def initialize(context):
    """Initialize"""
    # Set benchmark
    set_benchmark('000300.XSHG')
    
    # Set stock pool
    g.stocks = ['000001.XSHE', '600519.XSHG']
    
    # Set strategy parameters
    g.param1 = 10
    g.param2 = 20
    
    # Set execution schedule
    run_daily(market_open, time='9:30')
    run_daily(market_close, time='14:50')


def market_open(context):
    """Run at market open"""
    for stock in g.stocks:
        # Get data
        data = get_data(stock)
        
        # Generate signal
        signal = generate_signal(data)
        
        # Execute trade
        if signal == 'buy':
            buy_stock(context, stock)
        elif signal == 'sell':
            sell_stock(context, stock)


def generate_signal(data):
    """Generate trading signal"""
    # Implement your trading logic here
    pass
```

#### Code Standards

1. **Function Documentation**
```python
def calculate_signal(price, volume):
    """
    Calculate trading signal
    
    Parameters:
    -----------
    price : float
        Current price
    volume : int
        Trading volume
    
    Returns:
    --------
    str : 'buy', 'sell', or 'hold'
    """
    pass
```

2. **Logging**
```python
log.info(f"Buying {stock} at price: {price}")
log.warning(f"Insufficient funds")
log.error(f"Data retrieval failed: {error}")
```

### 4. Backtesting

#### Backtest Configuration

```python
# Backtest period
start_date = '2020-01-01'
end_date = '2023-12-31'

# Initial capital
initial_capital = 100000

# Commission settings
commission_rate = 0.0003
```

#### Performance Evaluation

```python
from utils.performance import generate_performance_report

# Calculate returns
returns = calculate_returns(portfolio_value)

# Generate report
report = generate_performance_report(returns, initial_capital)
print_performance_report(report)
```

### 5. Parameter Optimization

#### Grid Search

```python
# Define parameter ranges
short_periods = [5, 10, 15, 20]
long_periods = [30, 40, 50, 60]

best_sharpe = -np.inf
best_params = None

# Iterate through all parameter combinations
for short in short_periods:
    for long in long_periods:
        if short >= long:
            continue
        
        # Run backtest with current parameters
        result = run_backtest(short, long)
        
        # Evaluate performance
        if result['sharpe'] > best_sharpe:
            best_sharpe = result['sharpe']
            best_params = (short, long)

print(f"Best parameters: short={best_params[0]}, long={best_params[1]}")
print(f"Sharpe ratio: {best_sharpe:.2f}")
```

### 6. Risk Assessment

#### Key Risk Metrics

1. **Maximum Drawdown**
   - Measures strategy's maximum loss
   - Recommend < 30%

2. **Sharpe Ratio**
   - Measures risk-adjusted returns
   - Recommend > 1.0

3. **Win Rate**
   - Percentage of winning trades
   - Recommend > 50%

4. **Profit Factor**
   - Average win / Average loss
   - Recommend > 1.5

#### Risk Control Measures

```python
# Position limit per stock
max_position_per_stock = 0.2  # 20%

# Maximum total position
max_total_position = 0.95  # 95%

# Stop loss percentage
stop_loss_pct = 0.05  # 5%

# Take profit percentage
take_profit_pct = 0.15  # 15%
```

### 7. Common Pitfalls

#### Overfitting

**Problem:** Over-optimization leads to good backtest but poor live performance

**Solutions:**
- Use out-of-sample testing
- Keep strategy simple
- Avoid too many parameters

#### Look-Ahead Bias

**Problem:** Using data that wasn't available at the time

**Solutions:**
- Carefully check data timestamps
- Avoid using period-wide statistics

#### Survivorship Bias

**Problem:** Only considering surviving stocks, ignoring delisted ones

**Solutions:**
- Use data including delisted stocks
- Timely remove ST stocks

### Best Practices

1. **Start Simple**
   - Implement basic version first
   - Add features gradually

2. **Version Control**
   - Use Git for code management
   - Record each modification

3. **Documentation**
   - Document strategy logic
   - Explain parameter meanings

4. **Continuous Monitoring**
   - Regularly check strategy performance
   - Adjust parameters timely
