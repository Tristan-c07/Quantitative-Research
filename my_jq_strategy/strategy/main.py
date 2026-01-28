# -*- coding: utf-8 -*-
from jqdata import *
import numpy as np
import pandas as pd

from my_jq_strategy.lib.data import load_orderbook_window
from my_jq_strategy.lib.signal import ofi_signal
from my_jq_strategy.lib.risk import target_position
from my_jq_strategy.lib.utils import log_kv

def initialize(context):
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)

    # 例：单标的先跑通，后面改成 configs/universe.yaml 读取
    g.symbol = '510300.XSHG'
    g.window = 200  # 用多少条盘口快照算信号（先随便）

    run_daily(handle, time='every_bar')

def handle(context):
    symbol = g.symbol

    # 1) 取数据（你后面换成真实 tick/盘口接口）
    df = load_orderbook_window(symbol, count=g.window, end_dt=context.current_dt)
    if df is None or len(df) < 10:
        return

    # 2) 算信号
    sig = ofi_signal(df)

    # 3) 风控 -> 目标仓位
    tgt = target_position(signal=sig)

    # 4) 下单（先只打印，别真下）
    log_kv("sig", sig, "tgt", tgt)

    # 真下单示例（等你信号可信再开）
    # order_target_percent(symbol, tgt)
