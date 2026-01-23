"""
数据加载工具 (Data Loading Utilities)
===================================

用于从各种数据源加载股票数据
Tools for loading stock data from various sources

Author: Quantitative Research
License: Apache 2.0
"""

import pandas as pd
from datetime import datetime, timedelta


def load_stock_data(stock_code, start_date, end_date, source='local'):
    """
    加载股票历史数据
    Load historical stock data
    
    Parameters:
    -----------
    stock_code : str
        股票代码，如 '000001.XSHE'
    start_date : str
        开始日期，格式 'YYYY-MM-DD'
    end_date : str
        结束日期，格式 'YYYY-MM-DD'
    source : str
        数据源，可选 'local', 'tushare', 'yfinance'
    
    Returns:
    --------
    pd.DataFrame : 包含日期、开高低收、成交量等数据
    """
    if source == 'tushare':
        return load_from_tushare(stock_code, start_date, end_date)
    elif source == 'yfinance':
        return load_from_yfinance(stock_code, start_date, end_date)
    else:
        # 返回示例数据框架
        return create_sample_data(stock_code, start_date, end_date)


def load_from_tushare(stock_code, start_date, end_date):
    """
    从Tushare加载数据
    Load data from Tushare
    
    需要Tushare账号和token
    Requires Tushare account and token
    """
    try:
        import tushare as ts
        import os
        
        # 设置token（需要在tushare官网注册获取）
        # 推荐使用环境变量: export TUSHARE_TOKEN='your_token'
        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            raise ValueError("Tushare token not found. Set TUSHARE_TOKEN environment variable.")
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 转换股票代码格式
        ts_code = convert_to_tushare_code(stock_code)
        
        # 获取数据
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', '')
        )
        
        # 重命名列
        df = df.rename(columns={
            'trade_date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')
        
        return df
    except Exception as e:
        print(f"从Tushare加载数据失败: {e}")
        return create_sample_data(stock_code, start_date, end_date)


def load_from_yfinance(stock_code, start_date, end_date):
    """
    从Yahoo Finance加载数据
    Load data from Yahoo Finance
    """
    try:
        import yfinance as yf
        
        # 转换股票代码格式
        yf_code = convert_to_yfinance_code(stock_code)
        
        # 获取数据
        df = yf.download(yf_code, start=start_date, end=end_date)
        
        # 重命名列（小写）
        df.columns = [col.lower() for col in df.columns]
        
        return df
    except Exception as e:
        print(f"从Yahoo Finance加载数据失败: {e}")
        return create_sample_data(stock_code, start_date, end_date)


def create_sample_data(stock_code, start_date, end_date):
    """
    创建示例数据
    Create sample data for demonstration
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # 生成模拟价格数据
    import numpy as np
    np.random.seed(42)
    
    n = len(dates)
    price = 100
    prices = [price]
    
    for i in range(n - 1):
        change = np.random.normal(0, 2)
        price = price * (1 + change / 100)
        prices.append(price)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n)
    })
    
    df = df.set_index('date')
    return df


def convert_to_tushare_code(stock_code):
    """
    将聚宽格式转换为Tushare格式
    Convert JoinQuant format to Tushare format
    
    Example: '000001.XSHE' -> '000001.SZ'
    """
    code, market = stock_code.split('.')
    if market == 'XSHE':
        return f"{code}.SZ"
    elif market == 'XSHG':
        return f"{code}.SH"
    return stock_code


def convert_to_yfinance_code(stock_code):
    """
    将聚宽格式转换为Yahoo Finance格式
    Convert JoinQuant format to Yahoo Finance format
    
    Example: '000001.XSHE' -> '000001.SZ'
    """
    code, market = stock_code.split('.')
    if market == 'XSHE':
        return f"{code}.SZ"
    elif market == 'XSHG':
        return f"{code}.SS"
    return stock_code


def load_multiple_stocks(stock_list, start_date, end_date, source='local'):
    """
    批量加载多只股票数据
    Load data for multiple stocks
    
    Parameters:
    -----------
    stock_list : list
        股票代码列表
    start_date : str
        开始日期
    end_date : str
        结束日期
    source : str
        数据源
    
    Returns:
    --------
    dict : {stock_code: DataFrame}
    """
    data_dict = {}
    
    for stock in stock_list:
        try:
            df = load_stock_data(stock, start_date, end_date, source)
            data_dict[stock] = df
            print(f"成功加载 {stock}")
        except Exception as e:
            print(f"加载 {stock} 失败: {e}")
    
    return data_dict


if __name__ == "__main__":
    # 示例用法
    # Example usage
    
    stock_code = '000001.XSHE'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    # 加载数据
    data = load_stock_data(stock_code, start_date, end_date)
    print(f"\n数据维度: {data.shape}")
    print(f"\n前5行数据:\n{data.head()}")
    print(f"\n数据统计:\n{data.describe()}")
