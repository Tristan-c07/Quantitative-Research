# src/ofi.py
import pandas as pd
import numpy as np

def compute_ofi_l1(df: pd.DataFrame) -> pd.Series:
    """
    Compute Level-1 OFI for a single day order book DataFrame.
    Assumes df is sorted by ts.
    Returns a pd.Series aligned with df.index.
    """
    b_p = df["b1_p"]
    b_v = df["b1_v"]
    a_p = df["a1_p"]
    a_v = df["a1_v"]

    # shift
    b_p_prev = b_p.shift(1)
    b_v_prev = b_v.shift(1)
    a_p_prev = a_p.shift(1)
    a_v_prev = a_v.shift(1)

    # Bid contribution
    bid = np.where(
        b_p > b_p_prev, b_v,
        np.where(
            b_p < b_p_prev, -b_v_prev,
            b_v - b_v_prev
        )
    )

    # Ask contribution
    ask = np.where(
        a_p > a_p_prev, -a_v_prev,
        np.where(
            a_p < a_p_prev, a_v,
            -(a_v - a_v_prev)
        )
    )

    ofi = bid + ask
    ofi[0] = 0.0  # 第一条没有前值

    return pd.Series(ofi, index=df.index, name="ofi_l1")
