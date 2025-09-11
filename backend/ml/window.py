import numpy as np


def make_windows(arr: np.ndarray, lookback: int, horizon: int):
X, y = [], []
for i in range(len(arr) - lookback - horizon + 1):
X.append(arr[i:i+lookback])
y.append(arr[i+lookback:i+lookback+horizon])
return np.asarray(X), np.asarray(y)