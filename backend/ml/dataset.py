import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from .window import make_windows


class Prepared:
def __init__(self, Xtr, ytr, Xv, yv, Xte, yte, scaler: StandardScaler):
self.Xtr, self.ytr, self.Xv, self.yv, self.Xte, self.yte, self.scaler = Xtr, ytr, Xv, yv, Xte, yte, scaler


def prepare_dataset(bars_df: pd.DataFrame,
features=("close","volume"),
label_col: str = "close",
label_mode: str = "returns", # "levels" or "returns"
lookback: int = 128,
horizon: int = 1,
val_ratio: float = 0.1,
test_ratio: float = 0.1) -> Prepared:
df = bars_df[list(features)].dropna().astype(float)
if label_mode == "returns":
df_ret = df.copy()
df_ret[label_col] = df_ret[label_col].pct_change().fillna(0.0)
target_series = df_ret[label_col].values.reshape(-1,1)
else:
target_series = df[label_col].values.reshape(-1,1)


scaler = StandardScaler()
Xscaled = scaler.fit_transform(df.values)


X, _ = make_windows(Xscaled, lookback, horizon)


if label_mode == "returns":
ysrc = target_series
y_list = []
for i in range(len(ysrc) - lookback - horizon + 1):
y_list.append(ysrc[i+lookback:i+lookback+horizon].sum(axis=0))
y = np.asarray(y_list)
else:
y_list = []
for i in range(len(target_series) - lookback - horizon + 1):
y_list.append(target_series[i+lookback:i+lookback+horizon].flatten())
y = np.asarray(y_list)


n = len(X)
n_test = int(n * test_ratio)
n_val = int(n * val_ratio)
Xtr, ytr = X[:n-n_val-n_test], y[:n-n_val-n_test]
Xv, yv = X[n-n_val-n_test:n-n_test], y[n-n_val-n_test:n-n-test]
Xte, yte = X[n-n_test:], y[n-n_test:]
return Prepared(Xtr,ytr,Xv,yv,Xte,yte, scaler)