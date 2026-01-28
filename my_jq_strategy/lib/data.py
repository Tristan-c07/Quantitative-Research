# -*- coding: utf-8 -*-
import pandas as pd

def load_orderbook_window(symbol: str, count: int, end_dt):
    """
    返回一个 DataFrame，至少包含：
      time,
      b1_p,b1_v,a1_p,a1_v, ... b5_p,b5_v,a5_p,a5_v
    先写成占位：你后面把 jqdata 的盘口/逐笔接口接进来。
    """
    # TODO: 用聚宽研究环境里你实际能拿到的接口替换这里
    # 现在先返回 None，主策略会直接跳过
    return None
