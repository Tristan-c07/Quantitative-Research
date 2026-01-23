"""
均值回归策略 (Mean Reversion Strategy)
====================================

策略说明 (Strategy Description):
- 基于布林带(Bollinger Bands)的均值回归策略
- 价格触及下轨时买入（超卖）
- 价格触及上轨时卖出（超买）

适用于聚宽平台 (For JoinQuant Platform)

Author: Quantitative Research
License: Apache 2.0
"""

import numpy as np


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
        open_tax=0,
        close_tax=0.001,
        open_commission=0.0003,
        close_commission=0.0003,
        min_commission=5
    ), type='stock')
    
    # 设置股票池
    g.stock = '600519.XSHG'  # 贵州茅台
    
    # 设置布林带参数
    g.period = 20        # 周期
    g.std_multiplier = 2  # 标准差倍数
    
    # 持仓状态
    g.holding = False
    
    # 每天开盘前运行
    run_daily(market_open, time='every_bar')


def calculate_bollinger_bands(prices, period=20, std_multiplier=2):
    """
    计算布林带
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    prices : array-like
        价格序列
    period : int
        计算周期
    std_multiplier : float
        标准差倍数
    
    Returns:
    --------
    tuple : (upper_band, middle_band, lower_band)
    """
    middle_band = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper_band = middle_band + std_multiplier * std
    lower_band = middle_band - std_multiplier * std
    
    return upper_band, middle_band, lower_band


def market_open(context):
    """
    开盘时运行的函数
    Function to run at market open
    """
    stock = g.stock
    
    # 获取历史数据
    df = attribute_history(stock, g.period + 5, '1d', ['close'])
    prices = df['close'].values
    current_price = prices[-1]
    
    # 计算布林带
    upper_band, middle_band, lower_band = calculate_bollinger_bands(
        prices, g.period, g.std_multiplier
    )
    
    # 获取当前持仓
    current_position = context.portfolio.positions.get(stock)
    has_position = current_position is not None and current_position.closeable_amount > 0
    
    # 交易逻辑
    # 买入信号：价格跌破下轨（超卖）
    if current_price <= lower_band and not has_position:
        # 使用可用资金的95%买入
        order_target_value(stock, context.portfolio.available_cash * 0.95)
        g.holding = True
        log.info(f"买入信号: 价格({current_price:.2f})低于下轨({lower_band:.2f})")
        log.info(f"布林带: 上轨={upper_band:.2f}, 中轨={middle_band:.2f}, 下轨={lower_band:.2f}")
    
    # 卖出信号1：价格突破上轨（超买）
    elif current_price >= upper_band and has_position:
        order_target(stock, 0)
        g.holding = False
        log.info(f"卖出信号: 价格({current_price:.2f})高于上轨({upper_band:.2f})")
    
    # 卖出信号2：价格回归中轨附近
    elif has_position and current_price >= middle_band:
        # 可以选择在中轨附近部分或全部止盈
        order_target(stock, 0)
        g.holding = False
        log.info(f"止盈: 价格({current_price:.2f})回归中轨({middle_band:.2f})")


def after_trading_end(context):
    """
    收盘后运行的函数
    Function to run after market close
    """
    log.info(f"持仓状态: {g.holding}")
    log.info(f"账户总资产: {context.portfolio.total_value:.2f}")
    log.info(f"当前收益率: {(context.portfolio.total_value / context.portfolio.starting_cash - 1) * 100:.2f}%")


# ============================
# 策略优化建议 (Optimization Tips):
# ============================
# 1. 结合RSI指标确认超买超卖状态
# 2. 添加成交量确认信号
# 3. 动态调整布林带参数
# 4. 设置止损保护
# 5. 分批建仓和平仓
# 6. 避免在趋势市场使用均值回归策略
