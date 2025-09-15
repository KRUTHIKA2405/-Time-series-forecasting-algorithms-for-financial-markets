import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from typing import Tuple


class PreparedDataset:
    def __init__(self, Xtr, ytr, Xv, yv, Xte, yte, scaler: StandardScaler):
        self.Xtr, self.ytr = Xtr, ytr
        self.Xv, self.yv = Xv, yv
        self.Xte, self.yte = Xte, yte
        self.scaler = scaler


def make_windows(
    arr: np.ndarray, lookback: int, horizon: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Turn an array into overlapping windows.
    arr: shape (T, F)
    returns: X shape (N, lookback, F), y shape (N, horizon)
    """
    X, y = [], []
    for i in range(len(arr) - lookback - horizon + 1):
        X.append(arr[i : i + lookback])
        y.append(arr[i + lookback : i + lookback + horizon, 0])  # assume first col is label
    return np.array(X), np.array(y)


def prepare_dataset(
    df: pd.DataFrame,
    features: Tuple[str, ...] = ("close", "volume"),
    label_mode: str = "returns",
    lookback: int = 128,
    horizon: int = 1,
    splits: Tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> PreparedDataset:
    """
    Prepare train/val/test sets from raw bars.
    label_mode: "returns" = predict log returns, "levels" = predict raw levels.
    """

    df = df.copy().dropna()
    if label_mode == "returns":
        df["target"] = np.log(df["close"]).diff().shift(-horizon)
    else:
        df["target"] = df["close"].shift(-horizon)
    df = df.dropna()

    data = df[list(features) + ["target"]].values
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    X, y = make_windows(data_scaled, lookback, horizon)

    N = len(X)
    ntr = int(N * splits[0])
    nv = int(N * splits[1])
    nte = N - ntr - nv

    Xtr, ytr = X[:ntr], y[:ntr]
    Xv, yv = X[ntr : ntr + nv], y[ntr : ntr + nv]
    Xte, yte = X[ntr + nv :], y[ntr + nv :]

    return PreparedDataset(Xtr, ytr, Xv, yv, Xte, yte, scaler)
