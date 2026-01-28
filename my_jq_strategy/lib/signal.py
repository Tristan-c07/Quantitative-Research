# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

def ofi_signal(ob: pd.DataFrame) -> float:
    """
    输入：盘口快照序列 ob（按 time 升序）
    输出：一个连续信号值（正=买压，负=卖压）
    先给一个最小实现：只用 L1 的变化（便于先跑通链路）
    """
    required = {"b1_p","b1_v","a1_p","a1_v"}
    if ob is None or len(ob) < 2 or not required.issubset(ob.columns):
        return 0.0

    # 最小 L1 OFI：基于 bid/ask 价量变化的简化版（占位）
    bpx = ob["b1_p"].to_numpy()
    bpv = ob["b1_v"].to_numpy()
    apx = ob["a1_p"].to_numpy()
    apv = ob["a1_v"].to_numpy()

    # 用差分构造一个“方向性强度”（你后面会换成标准 OFI 定义）
    dbp = np.diff(bpx)
    dap = np.diff(apx)
    dvb = np.diff(bpv)
    dva = np.diff(apv)

    # 一个可工作的占位：bid上升/量增视为买压，ask下降/量减视为买压
    ofi = (dbp > 0) * dvb - (dap > 0) * dva
    return float(np.nan_to_num(ofi).sum())
