from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
from services.influx_reader import get_bars


router = APIRouter()


class PredictReq(BaseModel):
symbol: str
interval: str
model_path: str
lookback: int = 128
features: List[str] = ["close","volume"]


@router.post("/next")
def predict_next(req: PredictReq):
bars = get_bars(req.symbol, req.interval, start="-200d")
if bars is None or bars.empty:
raise HTTPException(404, "No bars available")


df = bars[list(req.features)].dropna()
sc = StandardScaler()
Xs = sc.fit_transform(df.values)
if len(Xs) < req.lookback:
raise HTTPException(400, "Not enough history for lookback")


window = Xs[-req.lookback:]
X = window.reshape(1, req.lookback, Xs.shape[1])


model = load_model(req.model_path)
yhat = model.predict(X, verbose=0)[0].tolist()
return {"symbol": req.symbol, "interval": req.interval, "forecast": yhat}