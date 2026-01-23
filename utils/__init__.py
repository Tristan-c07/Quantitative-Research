"""
Quantitative Research Utilities
量化研究工具包

This package provides utility functions for:
- Data loading and processing
- Technical indicator calculation
- Performance analysis and reporting

本包提供以下工具函数：
- 数据加载和处理
- 技术指标计算
- 性能分析和报告
"""

from .data_loader import load_stock_data, load_multiple_stocks
from .indicators import calculate_ma, calculate_macd, calculate_rsi, calculate_bollinger_bands
from .performance import generate_performance_report, calculate_sharpe_ratio, calculate_max_drawdown

__version__ = '1.0.0'
__author__ = 'Quantitative Research'

__all__ = [
    'load_stock_data',
    'load_multiple_stocks',
    'calculate_ma',
    'calculate_macd',
    'calculate_rsi',
    'calculate_bollinger_bands',
    'generate_performance_report',
    'calculate_sharpe_ratio',
    'calculate_max_drawdown',
]
