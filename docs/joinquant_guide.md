# 聚宽平台使用指南 | JoinQuant Platform Guide

[中文](#chinese) | [English](#english)

---

<a name="chinese"></a>
## 聚宽平台使用指南

### 什么是聚宽？

聚宽（JoinQuant）是中国领先的量化交易平台，为个人投资者和机构提供：
- 免费的量化研究环境
- 全面的历史数据
- 强大的回测引擎
- 实盘交易接口

### 注册与登录

1. 访问 [聚宽官网](https://www.joinquant.com)
2. 点击"注册"创建账号
3. 验证邮箱后登录平台

### 创建策略

#### 步骤1：进入策略编辑器

1. 登录后点击"策略研究"
2. 选择"新建策略"
3. 选择"Python"作为编程语言

#### 步骤2：编写策略代码

聚宽策略主要包含以下几个函数：

```python
def initialize(context):
    """
    初始化函数，策略开始时运行一次
    在这里设置：
    - 基准收益
    - 股票池
    - 运行时间
    - 策略参数
    """
    pass

def handle_data(context, data):
    """
    每个交易日运行的函数（已弃用，推荐使用run_daily）
    """
    pass

def market_open(context):
    """
    开盘时运行的函数（需要在initialize中设置）
    """
    pass
```

#### 步骤3：回测策略

1. 设置回测参数：
   - 起始时间
   - 结束时间
   - 初始资金
   - 基准
   
2. 点击"回测"按钮

3. 查看回测结果：
   - 收益曲线
   - 回撤曲线
   - 性能指标
   - 交易记录

### 常用API函数

#### 数据获取

```python
# 获取历史数据
df = attribute_history(security, count, unit, fields)
# security: 股票代码
# count: 数量
# unit: '1d'(天), '1m'(分钟)
# fields: ['open', 'close', 'high', 'low', 'volume']

# 获取当前价格
current_price = data[security].price

# 获取股票池
stocks = get_index_stocks('000300.XSHG')  # 沪深300
```

#### 交易函数

```python
# 按目标金额下单
order_target_value(security, amount)

# 按目标数量下单
order_target(security, amount)

# 按比例下单
order_target_percent(security, percent)

# 市价单
order(security, amount)
```

#### 持仓查询

```python
# 获取当前持仓
positions = context.portfolio.positions

# 获取某只股票的持仓
position = context.portfolio.positions.get(security)

# 获取可用资金
cash = context.portfolio.available_cash

# 获取总资产
total_value = context.portfolio.total_value
```

### 策略优化技巧

#### 1. 参数优化

使用参数扫描功能测试不同参数组合：

```python
# 在initialize中设置可调参数
g.short_period = 10
g.long_period = 30
```

#### 2. 风险控制

```python
# 设置止损
if context.portfolio.positions[stock].pnl_ratio < -0.05:
    order_target(stock, 0)

# 设置止盈
if context.portfolio.positions[stock].pnl_ratio > 0.10:
    order_target(stock, 0)
```

#### 3. 仓位管理

```python
# 等权配置
target_weight = 1.0 / len(stock_list)
for stock in stock_list:
    order_target_percent(stock, target_weight)
```

### 注意事项

1. **数据权限**
   - 免费用户有分钟数据限制
   - 付费用户享有更多数据权限

2. **回测限制**
   - 回测时间不宜过长（建议1-3年）
   - 避免使用未来函数

3. **实盘注意**
   - 回测结果不代表实盘表现
   - 需要考虑滑点和冲击成本
   - 建议先进行模拟交易

### 学习资源

- [聚宽文档中心](https://www.joinquant.com/help)
- [API文档](https://www.joinquant.com/help/api/)
- [策略示例](https://www.joinquant.com/view/community/list)

---

<a name="english"></a>
## JoinQuant Platform Guide

### What is JoinQuant?

JoinQuant is China's leading quantitative trading platform, providing:
- Free quantitative research environment
- Comprehensive historical data
- Powerful backtesting engine
- Live trading interface

### Registration and Login

1. Visit [JoinQuant Official Website](https://www.joinquant.com)
2. Click "Register" to create an account
3. Verify email and login

### Creating a Strategy

#### Step 1: Enter Strategy Editor

1. After login, click "Strategy Research"
2. Select "New Strategy"
3. Choose "Python" as programming language

#### Step 2: Write Strategy Code

JoinQuant strategies mainly include these functions:

```python
def initialize(context):
    """
    Initialization function, runs once at strategy start
    Set here:
    - Benchmark
    - Stock pool
    - Execution schedule
    - Strategy parameters
    """
    pass

def handle_data(context, data):
    """
    Function runs every trading day (deprecated, use run_daily)
    """
    pass

def market_open(context):
    """
    Function runs at market open (needs setup in initialize)
    """
    pass
```

#### Step 3: Backtest Strategy

1. Set backtest parameters:
   - Start date
   - End date
   - Initial capital
   - Benchmark
   
2. Click "Backtest" button

3. View backtest results:
   - Return curve
   - Drawdown curve
   - Performance metrics
   - Trade records

### Common API Functions

#### Data Retrieval

```python
# Get historical data
df = attribute_history(security, count, unit, fields)
# security: stock code
# count: number of bars
# unit: '1d'(day), '1m'(minute)
# fields: ['open', 'close', 'high', 'low', 'volume']

# Get current price
current_price = data[security].price

# Get stock pool
stocks = get_index_stocks('000300.XSHG')  # CSI300
```

#### Trading Functions

```python
# Order by target value
order_target_value(security, amount)

# Order by target quantity
order_target(security, amount)

# Order by target percentage
order_target_percent(security, percent)

# Market order
order(security, amount)
```

#### Position Query

```python
# Get current positions
positions = context.portfolio.positions

# Get position for a stock
position = context.portfolio.positions.get(security)

# Get available cash
cash = context.portfolio.available_cash

# Get total value
total_value = context.portfolio.total_value
```

### Strategy Optimization Tips

#### 1. Parameter Optimization

Use parameter scanning to test different combinations:

```python
# Set adjustable parameters in initialize
g.short_period = 10
g.long_period = 30
```

#### 2. Risk Control

```python
# Set stop loss
if context.portfolio.positions[stock].pnl_ratio < -0.05:
    order_target(stock, 0)

# Set take profit
if context.portfolio.positions[stock].pnl_ratio > 0.10:
    order_target(stock, 0)
```

#### 3. Position Management

```python
# Equal weight allocation
target_weight = 1.0 / len(stock_list)
for stock in stock_list:
    order_target_percent(stock, target_weight)
```

### Important Notes

1. **Data Access**
   - Free users have minute data limitations
   - Paid users get more data access

2. **Backtest Limitations**
   - Don't make backtest period too long (recommend 1-3 years)
   - Avoid look-ahead bias

3. **Live Trading**
   - Backtest results don't guarantee live performance
   - Consider slippage and market impact
   - Recommend paper trading first

### Learning Resources

- [JoinQuant Documentation](https://www.joinquant.com/help)
- [API Documentation](https://www.joinquant.com/help/api/)
- [Strategy Examples](https://www.joinquant.com/view/community/list)
