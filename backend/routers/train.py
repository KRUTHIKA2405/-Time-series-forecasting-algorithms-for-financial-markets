from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
import tensorflow as tf

from services.influx_reader import get_bars
from ml.dataset import prepare_dataset
from ml.model import build_cnn_lstm

router = APIRouter()

class TrainReq(BaseModel):
    symbol: str
    interval: str
    lookback: int = 128
    horizon: int = 1
    features: List[str] = ["close", "volume"]
    label_mode: str = "returns"   # "returns" or "levels"
    epochs: int = 50
    batch_size: int = 256

@router.post("/start")
def start_training(req: TrainReq):
    bars = get_bars(req.symbol, req.interval, start="-365d")
    if bars is None or bars.empty:
        raise HTTPException(404, "No bars to train on")

    prep = prepare_dataset(
        bars,
        features=tuple(req.features),
        label_mode=req.label_mode,
        lookback=req.lookback,
        horizon=req.horizon,
    )

    model = build_cnn_lstm(prep.Xtr.shape[1:], horizon=req.horizon)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=4),
    ]
    hist = model.fit(
        prep.Xtr, prep.ytr,
        validation_data=(prep.Xv, prep.yv),
        epochs=req.epochs, batch_size=req.batch_size,
        verbose=0, callbacks=callbacks
    )

    os.makedirs("artifacts", exist_ok=True)
    model_path = f"artifacts/{req.symbol}_{req.interval}_cnn_lstm.keras"
    model.save(model_path)

    return {
        "status": "ok",
        "model_path": model_path,
        "val_loss": float(min(hist.history["val_loss"])),
        "val_mae": float(min(hist.history.get("val_mae", [0.0]))),
    }
