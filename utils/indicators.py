"""
技术指标计算工具 (Technical Indicators)
====================================

常用技术指标的计算函数
Common technical indicators calculation functions

Author: Quantitative Research
License: Apache 2.0
"""

import pandas as pd
import numpy as np


def calculate_ma(df, periods=[5, 10, 20, 60]):
    """
    计算移动平均线
    Calculate Moving Average
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    periods : list
        均线周期列表
    
    Returns:
    --------
    pd.DataFrame : 添加了均线列的DataFrame
    """
    result = df.copy()
    
    for period in periods:
        col_name = f'MA{period}'
        result[col_name] = result['close'].rolling(window=period).mean()
    
    return result


def calculate_ema(df, periods=[12, 26]):
    """
    计算指数移动平均线
    Calculate Exponential Moving Average
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    periods : list
        EMA周期列表
    
    Returns:
    --------
    pd.DataFrame : 添加了EMA列的DataFrame
    """
    result = df.copy()
    
    for period in periods:
        col_name = f'EMA{period}'
        result[col_name] = result['close'].ewm(span=period, adjust=False).mean()
    
    return result


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    Calculate MACD (Moving Average Convergence Divergence)
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    fast : int
        快线周期
    slow : int
        慢线周期
    signal : int
        信号线周期
    
    Returns:
    --------
    pd.DataFrame : 添加了MACD相关列的DataFrame
    """
    result = df.copy()
    
    # 计算EMA
    ema_fast = result['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = result['close'].ewm(span=slow, adjust=False).mean()
    
    # MACD线
    result['MACD'] = ema_fast - ema_slow
    
    # 信号线
    result['MACD_signal'] = result['MACD'].ewm(span=signal, adjust=False).mean()
    
    # MACD柱状图
    result['MACD_hist'] = result['MACD'] - result['MACD_signal']
    
    return result


def calculate_rsi(df, period=14):
    """
    计算相对强弱指标
    Calculate RSI (Relative Strength Index)
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    period : int
        计算周期
    
    Returns:
    --------
    pd.DataFrame : 添加了RSI列的DataFrame
    """
    result = df.copy()
    
    # 计算价格变化
    delta = result['close'].diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 计算平均收益和损失
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 计算RS和RSI
    rs = avg_gain / avg_loss
    result['RSI'] = 100 - (100 / (1 + rs))
    
    return result


def calculate_bollinger_bands(df, period=20, std_multiplier=2):
    """
    计算布林带
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    period : int
        计算周期
    std_multiplier : float
        标准差倍数
    
    Returns:
    --------
    pd.DataFrame : 添加了布林带列的DataFrame
    """
    result = df.copy()
    
    # 中轨（移动平均线）
    result['BB_middle'] = result['close'].rolling(window=period).mean()
    
    # 标准差
    std = result['close'].rolling(window=period).std()
    
    # 上轨和下轨
    result['BB_upper'] = result['BB_middle'] + (std_multiplier * std)
    result['BB_lower'] = result['BB_middle'] - (std_multiplier * std)
    
    # 带宽
    result['BB_width'] = (result['BB_upper'] - result['BB_lower']) / result['BB_middle']
    
    return result


def calculate_atr(df, period=14):
    """
    计算平均真实波幅
    Calculate ATR (Average True Range)
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含OHLC数据的DataFrame
    period : int
        计算周期
    
    Returns:
    --------
    pd.DataFrame : 添加了ATR列的DataFrame
    """
    result = df.copy()
    
    # 计算真实波幅
    high_low = result['high'] - result['low']
    high_close = abs(result['high'] - result['close'].shift())
    low_close = abs(result['low'] - result['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # 计算ATR
    result['ATR'] = true_range.rolling(window=period).mean()
    
    return result


def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    Calculate KDJ Indicator
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含OHLC数据的DataFrame
    n : int
        周期
    m1 : int
        K值平滑参数
    m2 : int
        D值平滑参数
    
    Returns:
    --------
    pd.DataFrame : 添加了KDJ列的DataFrame
    """
    result = df.copy()
    
    # 计算RSV
    low_min = result['low'].rolling(window=n).min()
    high_max = result['high'].rolling(window=n).max()
    rsv = (result['close'] - low_min) / (high_max - low_min) * 100
    
    # 计算K值
    result['K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    
    # 计算D值
    result['D'] = result['K'].ewm(com=m2-1, adjust=False).mean()
    
    # 计算J值
    result['J'] = 3 * result['K'] - 2 * result['D']
    
    return result


def calculate_volume_ma(df, periods=[5, 10, 20]):
    """
    计算成交量移动平均
    Calculate Volume Moving Average
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含成交量数据的DataFrame
    periods : list
        均量周期列表
    
    Returns:
    --------
    pd.DataFrame : 添加了均量列的DataFrame
    """
    result = df.copy()
    
    for period in periods:
        col_name = f'VOL_MA{period}'
        result[col_name] = result['volume'].rolling(window=period).mean()
    
    return result


def calculate_all_indicators(df):
    """
    计算所有常用技术指标
    Calculate all common technical indicators
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含OHLC和成交量数据的DataFrame
    
    Returns:
    --------
    pd.DataFrame : 包含所有技术指标的DataFrame
    """
    result = df.copy()
    
    # 移动平均线
    result = calculate_ma(result, periods=[5, 10, 20, 60])
    
    # MACD
    result = calculate_macd(result)
    
    # RSI
    result = calculate_rsi(result)
    
    # 布林带
    result = calculate_bollinger_bands(result)
    
    # ATR
    result = calculate_atr(result)
    
    # KDJ
    result = calculate_kdj(result)
    
    # 成交量均线
    result = calculate_volume_ma(result)
    
    return result


if __name__ == "__main__":
    # 示例用法
    # Example usage
    from data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('000001.XSHE', '2023-01-01', '2023-12-31')
    
    # 计算所有指标
    data_with_indicators = calculate_all_indicators(data)
    
    print(f"\n数据列: {data_with_indicators.columns.tolist()}")
    print(f"\n最新数据:\n{data_with_indicators.tail()}")
