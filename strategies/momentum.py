"""
动量策略 (Momentum Strategy)
==========================

策略说明 (Strategy Description):
- 基于相对强弱指标(RSI)和价格动量的策略
- 选择短期表现强劲的股票
- 趋势确认后跟随进场

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
    
    # 设置股票池 - 沪深300成分股
    g.stock_pool = get_index_stocks('000300.XSHG')[:20]  # 取前20只
    
    # 策略参数
    g.momentum_period = 20  # 动量计算周期
    g.rsi_period = 14       # RSI周期
    g.rsi_upper = 70        # RSI上限
    g.rsi_lower = 30        # RSI下限
    g.max_holdings = 5      # 最大持仓数量
    
    # 每天开盘前运行
    run_daily(market_open, time='every_bar')
    
    # 每天收盘后运行
    run_daily(after_trading_end, time='after_close')


def calculate_rsi(prices, period=14):
    """
    计算RSI指标
    Calculate RSI (Relative Strength Index)
    
    Parameters:
    -----------
    prices : array-like
        价格序列
    period : int
        计算周期
    
    Returns:
    --------
    float : RSI值
    """
    if len(prices) < period + 1:
        return 50  # 默认返回中性值
    
    # 计算价格变化
    deltas = np.diff(prices)
    
    # 分离上涨和下跌
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 计算平均收益和损失
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_momentum(prices, period=20):
    """
    计算动量指标（收益率）
    Calculate momentum (rate of return)
    
    Parameters:
    -----------
    prices : array-like
        价格序列
    period : int
        回望周期
    
    Returns:
    --------
    float : 动量值（百分比）
    """
    if len(prices) < period + 1:
        return 0
    
    momentum = (prices[-1] / prices[-period-1] - 1) * 100
    return momentum


def market_open(context):
    """
    开盘时运行的函数
    Function to run at market open
    """
    # 计算每只股票的动量和RSI
    stock_scores = {}
    
    for stock in g.stock_pool:
        # 获取历史数据
        try:
            df = attribute_history(stock, g.momentum_period + 20, '1d', ['close'])
            prices = df['close'].values
            
            # 计算指标
            momentum = calculate_momentum(prices, g.momentum_period)
            rsi = calculate_rsi(prices, g.rsi_period)
            
            # 选择标准：正动量 + RSI在合理区间（避免超买）
            if momentum > 0 and g.rsi_lower < rsi < g.rsi_upper:
                stock_scores[stock] = momentum
        except:
            continue
    
    # 按动量排序，选择前N只股票
    if len(stock_scores) > 0:
        sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
        target_stocks = [stock for stock, score in sorted_stocks[:g.max_holdings]]
        
        # 获取当前持仓
        current_positions = list(context.portfolio.positions.keys())
        
        # 卖出不在目标股票中的持仓
        for stock in current_positions:
            if stock not in target_stocks:
                order_target(stock, 0)
                log.info(f"卖出 {stock}: 不在目标股票列表")
        
        # 买入目标股票（等权配置）
        if len(target_stocks) > 0:
            target_weight = 0.95 / len(target_stocks)  # 95%资金均分
            for stock in target_stocks:
                order_target_value(stock, context.portfolio.total_value * target_weight)
                if stock not in current_positions:
                    log.info(f"买入 {stock}: 动量={stock_scores[stock]:.2f}%")
    else:
        # 没有符合条件的股票，清仓
        for stock in context.portfolio.positions.keys():
            order_target(stock, 0)


def after_trading_end(context):
    """
    收盘后运行的函数
    Function to run after market close
    """
    positions = list(context.portfolio.positions.keys())
    log.info(f"当前持仓({len(positions)}只): {positions}")
    log.info(f"账户总资产: {context.portfolio.total_value:.2f}")
    log.info(f"当前收益率: {(context.portfolio.total_value / context.portfolio.starting_cash - 1) * 100:.2f}%")


# ============================
# 策略优化建议 (Optimization Tips):
# ============================
# 1. 添加行业分散度约束
# 2. 引入量价关系确认
# 3. 动态调整持仓数量
# 4. 添加风险控制机制（最大回撤限制）
# 5. 考虑市场整体环境（大盘趋势）
# 6. 优化再平衡频率
