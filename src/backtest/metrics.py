"""
Backtest Metrics and Performance Analysis
"""

import numpy as np
from typing import Union


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe Ratio
    
    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate
        
    Returns:
        float: Sharpe ratio
    """
    excess_returns = returns - risk_free_rate
    std = float(np.std(excess_returns))
    return float(np.mean(excess_returns)) / std if std != 0.0 else 0.0


def calculate_max_drawdown(equity_curve: np.ndarray) -> float:
    """
    Calculate Maximum Drawdown
    
    Args:
        equity_curve: Array of equity values
        
    Returns:
        float: Maximum drawdown
    """
    if len(equity_curve) == 0:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    return float(np.min(drawdown))
