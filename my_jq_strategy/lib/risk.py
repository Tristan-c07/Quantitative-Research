# -*- coding: utf-8 -*-
import numpy as np

def target_position(signal: float,
                    max_leverage: float = 0.2,
                    k: float = 1e-4) -> float:
    """
    把信号压缩成 [-max_leverage, +max_leverage] 的目标仓位。
    k 控制信号强度到仓位的映射尺度（后面用样本波动/分位数定标）。
    """
    x = np.tanh(k * signal)
    return float(np.clip(x * max_leverage, -max_leverage, max_leverage))
