from fastapi import FastAPI
from routers import data, train, predict, metrics, yahoo, yahoo_watchlist


app = FastAPI(title="TS Forecasting API")
app.include_router(yahoo.router, prefix="/collect/yahoo", tags=["collect:yahoo"]) # NEW
app.include_router(yahoo_watchlist.router, prefix="/collect/yahoo", tags=["collect:yahoo"])# NEW
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(train.router, prefix="/train", tags=["train"])
app.include_router(predict.router, prefix="/predict", tags=["predict"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])