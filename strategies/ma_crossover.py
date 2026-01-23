"""
均线交叉策略 (Moving Average Crossover Strategy)
===========================================

策略说明 (Strategy Description):
- 使用双均线交叉系统
- 短期均线上穿长期均线时买入
- 短期均线下穿长期均线时卖出

适用于聚宽平台 (For JoinQuant Platform)

Author: Quantitative Research
License: Apache 2.0
"""

def initialize(context):
    """
    初始化函数 - 在策略开始时运行一次
    Initialize function - runs once at the start
    """
    # 设置基准收益：沪深300指数
    set_benchmark('000300.XSHG')
    
    # 开启动态复权模式（真实价格）
    set_option('use_real_price', True)
    
    # 设置交易成本
    set_order_cost(OrderCost(
        open_tax=0,           # 印花税
        close_tax=0.001,      # 印花税 0.1%
        open_commission=0.0003,  # 买入手续费
        close_commission=0.0003, # 卖出手续费
        min_commission=5      # 最小手续费5元
    ), type='stock')
    
    # 设置股票池
    g.stock = '000001.XSHE'  # 平安银行
    
    # 设置均线参数
    g.short_period = 10  # 短期均线周期
    g.long_period = 30   # 长期均线周期
    
    # 每天开盘前运行
    run_daily(market_open, time='every_bar')


def market_open(context):
    """
    开盘时运行的函数
    Function to run at market open
    """
    stock = g.stock
    
    # 获取历史数据
    df = attribute_history(stock, g.long_period + 1, '1d', ['close'])
    
    # 计算均线
    short_ma = df['close'][-g.short_period:].mean()
    long_ma = df['close'][-g.long_period:].mean()
    
    # 获取前一日的均线值
    prev_short_ma = df['close'][-(g.short_period + 1):-1].mean()
    prev_long_ma = df['close'][-(g.long_period + 1):-1].mean()
    
    # 获取当前持仓
    current_position = context.portfolio.positions.get(stock)
    
    # 交易逻辑
    # 金叉：短期均线上穿长期均线，买入
    if prev_short_ma <= prev_long_ma and short_ma > long_ma:
        if current_position is None or current_position.closeable_amount == 0:
            # 使用可用资金的95%买入
            order_target_value(stock, context.portfolio.available_cash * 0.95)
            log.info(f"买入信号：短期均线({short_ma:.2f})上穿长期均线({long_ma:.2f})")
    
    # 死叉：短期均线下穿长期均线，卖出
    elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
        if current_position is not None and current_position.closeable_amount > 0:
            # 清仓
            order_target(stock, 0)
            log.info(f"卖出信号：短期均线({short_ma:.2f})下穿长期均线({long_ma:.2f})")


def after_trading_end(context):
    """
    收盘后运行的函数
    Function to run after market close
    """
    # 输出当前持仓和收益情况
    log.info(f"当前持仓: {list(context.portfolio.positions.keys())}")
    log.info(f"账户总资产: {context.portfolio.total_value:.2f}")
    log.info(f"当前收益率: {(context.portfolio.total_value / context.portfolio.starting_cash - 1) * 100:.2f}%")


# ============================
# 策略优化建议 (Optimization Tips):
# ============================
# 1. 调整均线周期参数以适应不同市场环境
# 2. 添加成交量过滤条件
# 3. 设置止损止盈位
# 4. 考虑使用多个股票进行分散投资
# 5. 添加波动率过滤器避免震荡市
