"""
性能分析工具 (Performance Analysis)
================================

用于评估策略表现的工具函数
Tools for evaluating strategy performance

Author: Quantitative Research
License: Apache 2.0
"""

import pandas as pd
import numpy as np
from datetime import datetime


def calculate_returns(df, price_col='close'):
    """
    计算收益率
    Calculate returns
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    price_col : str
        价格列名
    
    Returns:
    --------
    pd.Series : 收益率序列
    """
    returns = df[price_col].pct_change()
    return returns


def calculate_cumulative_returns(returns):
    """
    计算累计收益率
    Calculate cumulative returns
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    
    Returns:
    --------
    pd.Series : 累计收益率序列
    """
    cumulative = (1 + returns).cumprod() - 1
    return cumulative


def calculate_sharpe_ratio(returns, risk_free_rate=0.03, periods_per_year=252):
    """
    计算夏普比率
    Calculate Sharpe Ratio
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    risk_free_rate : float
        无风险利率（年化）
    periods_per_year : int
        每年交易日数量
    
    Returns:
    --------
    float : 夏普比率
    """
    # 剔除NaN
    returns = returns.dropna()
    
    if len(returns) == 0:
        return 0.0
    
    # 计算超额收益
    daily_rf = risk_free_rate / periods_per_year
    excess_returns = returns - daily_rf
    
    # 计算夏普比率
    if excess_returns.std() == 0:
        return 0.0
    
    sharpe = np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()
    return sharpe


def calculate_max_drawdown(returns):
    """
    计算最大回撤
    Calculate Maximum Drawdown
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    
    Returns:
    --------
    tuple : (最大回撤, 回撤开始时间, 回撤结束时间)
    """
    # 计算累计收益
    cumulative = (1 + returns).cumprod()
    
    # 计算历史最高点
    running_max = cumulative.expanding().max()
    
    # 计算回撤
    drawdown = (cumulative - running_max) / running_max
    
    # 找到最大回撤
    max_dd = drawdown.min()
    
    # 找到最大回撤的位置
    max_dd_idx = drawdown.idxmin()
    
    # 找到最大回撤开始的位置（之前的最高点）
    max_dd_start = cumulative[:max_dd_idx].idxmax()
    
    return max_dd, max_dd_start, max_dd_idx


def calculate_annual_return(returns, periods_per_year=252):
    """
    计算年化收益率
    Calculate Annualized Return
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    periods_per_year : int
        每年交易日数量
    
    Returns:
    --------
    float : 年化收益率
    """
    if len(returns) == 0:
        return 0.0
    
    # 计算总收益
    total_return = (1 + returns).prod() - 1
    
    # 计算年化收益
    n_periods = len(returns)
    n_years = n_periods / periods_per_year
    
    if n_years == 0:
        return 0.0
    
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    return annual_return


def calculate_volatility(returns, periods_per_year=252):
    """
    计算波动率（年化）
    Calculate Volatility (Annualized)
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    periods_per_year : int
        每年交易日数量
    
    Returns:
    --------
    float : 年化波动率
    """
    volatility = returns.std() * np.sqrt(periods_per_year)
    return volatility


def calculate_win_rate(returns):
    """
    计算胜率
    Calculate Win Rate
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    
    Returns:
    --------
    float : 胜率（0-1之间）
    """
    returns = returns.dropna()
    
    if len(returns) == 0:
        return 0.0
    
    win_rate = (returns > 0).sum() / len(returns)
    return win_rate


def calculate_profit_factor(returns):
    """
    计算盈亏比
    Calculate Profit Factor
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    
    Returns:
    --------
    float : 盈亏比
    """
    returns = returns.dropna()
    
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    
    if gross_loss == 0:
        return np.inf if gross_profit > 0 else 0.0
    
    profit_factor = gross_profit / gross_loss
    return profit_factor


def calculate_calmar_ratio(returns, periods_per_year=252):
    """
    计算卡玛比率（年化收益/最大回撤）
    Calculate Calmar Ratio
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    periods_per_year : int
        每年交易日数量
    
    Returns:
    --------
    float : 卡玛比率
    """
    annual_return = calculate_annual_return(returns, periods_per_year)
    max_dd, _, _ = calculate_max_drawdown(returns)
    
    if max_dd == 0:
        return np.inf if annual_return > 0 else 0.0
    
    calmar = annual_return / abs(max_dd)
    return calmar


def generate_performance_report(returns, initial_capital=100000):
    """
    生成完整的性能报告
    Generate Complete Performance Report
    
    Parameters:
    -----------
    returns : pd.Series
        收益率序列
    initial_capital : float
        初始资金
    
    Returns:
    --------
    dict : 性能指标字典
    """
    returns = returns.dropna()
    
    # 计算各项指标
    total_return = (1 + returns).prod() - 1
    annual_return = calculate_annual_return(returns)
    volatility = calculate_volatility(returns)
    sharpe = calculate_sharpe_ratio(returns)
    max_dd, dd_start, dd_end = calculate_max_drawdown(returns)
    win_rate = calculate_win_rate(returns)
    profit_factor = calculate_profit_factor(returns)
    calmar = calculate_calmar_ratio(returns)
    
    # 最终资金
    final_capital = initial_capital * (1 + total_return)
    
    report = {
        '初始资金': f'¥{initial_capital:,.2f}',
        '最终资金': f'¥{final_capital:,.2f}',
        '总收益率': f'{total_return * 100:.2f}%',
        '年化收益率': f'{annual_return * 100:.2f}%',
        '年化波动率': f'{volatility * 100:.2f}%',
        '夏普比率': f'{sharpe:.2f}',
        '最大回撤': f'{max_dd * 100:.2f}%',
        '回撤开始': str(dd_start)[:10] if dd_start else 'N/A',
        '回撤结束': str(dd_end)[:10] if dd_end else 'N/A',
        '胜率': f'{win_rate * 100:.2f}%',
        '盈亏比': f'{profit_factor:.2f}',
        '卡玛比率': f'{calmar:.2f}',
        '交易天数': len(returns)
    }
    
    return report


def print_performance_report(report):
    """
    打印性能报告
    Print Performance Report
    
    Parameters:
    -----------
    report : dict
        性能报告字典
    """
    print("\n" + "="*50)
    print("策略性能报告 | Strategy Performance Report")
    print("="*50)
    
    for key, value in report.items():
        print(f"{key:12s}: {value}")
    
    print("="*50 + "\n")


if __name__ == "__main__":
    # 示例用法
    # Example usage
    from data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('000001.XSHE', '2023-01-01', '2023-12-31')
    
    # 计算收益率
    returns = calculate_returns(data)
    
    # 生成性能报告
    report = generate_performance_report(returns, initial_capital=100000)
    
    # 打印报告
    print_performance_report(report)
