"""
Backtest Metrics and Performance Analysis
"""


def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calculate Sharpe Ratio
    
    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate
        
    Returns:
        float: Sharpe ratio
    """
    import numpy as np
    excess_returns = returns - risk_free_rate
    return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else 0.0


def calculate_max_drawdown(equity_curve):
    """
    Calculate Maximum Drawdown
    
    Args:
        equity_curve: Array of equity values
        
    Returns:
        float: Maximum drawdown
    """
    import numpy as np
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    return np.min(drawdown)
