from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal
import numpy as np
from tensorflow.keras.models import load_model

from services.influx_reader import get_bars
from ml.dataset import prepare_dataset

router = APIRouter()

class EvalReq(BaseModel):
    symbol: str
    interval: str
    model_path: str
    lookback: int = 128
    horizon: int = 1
    features: List[str] = ["close", "volume"]
    label_mode: Literal["returns", "levels"] = "returns"

@router.post("/evaluate")
def evaluate(req: EvalReq):
    bars = get_bars(req.symbol, req.interval, start="-365d")
    if bars is None or bars.empty:
        raise HTTPException(404, "No bars")

    prep = prepare_dataset(
        bars,
        features=tuple(req.features),
        label_mode=req.label_mode,
        lookback=req.lookback,
        horizon=req.horizon,
    )
    model = load_model(req.model_path)
    ypred = model.predict(prep.Xte, verbose=0)
    ytrue = prep.yte

    eps = 1e-8
    rmse = float(np.sqrt(((ytrue - ypred) ** 2).mean()))
    mae  = float(np.abs(ytrue - ypred).mean())
    mape = float((np.abs((ytrue - ypred) / (np.abs(ytrue) + eps))).mean() * 100.0)
    da   = float((np.sign(ypred) == np.sign(ytrue)).mean())

    return {"rmse": rmse, "mae": mae, "mape": mape, "directional_acc": da}

class BacktestReq(BaseModel):
    symbol: str
    interval: str
    model_path: str
    lookback: int = 128
    horizon: int = 1
    features: List[str] = ["close", "volume"]
    label_mode: Literal["returns", "levels"] = "returns"
    threshold: float = 0.0
    cost_bps: float = 1.0

@router.post("/backtest")
def backtest(req: BacktestReq):
    bars = get_bars(req.symbol, req.interval, start="-365d")
    if bars is None or bars.empty:
        raise HTTPException(404, "No bars")

    prep = prepare_dataset(
        bars,
        features=tuple(req.features),
        label_mode=req.label_mode,
        lookback=req.lookback,
        horizon=req.horizon,
    )

    model = load_model(req.model_path)
    ypred = model.predict(prep.Xte, verbose=0).reshape(-1)
    ytrue = prep.yte.reshape(-1)

    # simple long/short based on threshold
    long  = (ypred >  req.threshold).astype(int)
    short = (ypred < -req.threshold).astype(int)
    pos = long - short  # -1, 0, 1

    rets = ytrue  # if label_mode == "returns", this is future cum return over horizon
    gross = pos * rets
    trades = np.abs(np.diff(pos, prepend=0))
    costs = trades * (req.cost_bps / 10000.0)
    net = gross - costs

    eq = (1.0 + net).cumprod()
    sharpe = float((np.mean(net) / (np.std(net) + 1e-8)) * np.sqrt(252))
    maxdd = float(1.0 - (eq / np.maximum.accumulate(eq)).min())

    return {
        "hit_ratio": float((np.sign(ypred) == np.sign(ytrue)).mean()),
        "avg_ret": float(np.mean(net)),
        "sharpe": sharpe,
        "max_drawdown": maxdd,
        "equity_curve": eq.tolist(),
        "positions": pos.tolist(),
    }
