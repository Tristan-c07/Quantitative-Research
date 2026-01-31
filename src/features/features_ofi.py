import pandas as pd
import numpy as np
from ..ofi import compute_ofi_l1

def make_1m_features_one_day(df: pd.DataFrame) -> pd.DataFrame:
    # Input: one-day ticks LOB DataFrame
    # Output: one-day 1m bars LOB DataFrame
    df = df.sort_values("ts").copy()
    
    df["mid"] = (df["a1_p"] + df["b1_p"]) / 2.0
    df["spread"] = df["a1_p"] - df["b1_p"]
    
    df["ofi1"] = compute_ofi_l1(df)
    df["minute"] = df["ts"].dt.floor("min")# type: ignore

    g = df.groupby("minute", sort=True)

    out = pd.DataFrame({
        "ofi1_sum": g["ofi1"].sum(),
        "mid_last": g["mid"].last(),
        "spread_med": g["spread"].median(),
        "n_ticks": g.size(),
    }).reset_index()

    # 下一分钟收益（用分钟末 mid）
    out["ret_fwd_1m"] = np.log(out["mid_last"].shift(-1) / out["mid_last"])

    return out