from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

router = APIRouter(prefix="/collect/yahoo", tags=["yahoo"])

# Pydantic request schema
class YahooReq(BaseModel):
    symbol: str  # e.g., "AAPL", "^GSPC", "BTC-USD"
    interval: str  # e.g., "1m", "5m", "1d"
    lookback: str = "60d"  # e.g., "60d", "5y"

# Influx setup
bucket = os.getenv("INFLUX_BUCKET", "marketdata")
org = os.getenv("INFLUX_ORG", "test")
url = os.getenv("INFLUX_URL", "http://localhost:8086")
token = os.getenv("INFLUX_TOKEN", "my-token")

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


@router.post("/backfill")
def backfill(req: YahooReq):
    """
    Download bars from Yahoo Finance and store into InfluxDB.
    """
    try:
        df = yf.download(req.symbol, interval=req.interval, period=req.lookback, progress=False)
    except Exception as e:
        raise HTTPException(500, f"Yahoo download failed: {e}")

    if df is None or df.empty:
        raise HTTPException(404, "No Yahoo data returned")

    df = df.reset_index().rename(
        columns={
            "Date": "time",
            "Datetime": "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )

    # Write to InfluxDB
    points = []
    for _, row in df.iterrows():
        pt = (
            Point("bars")
            .tag("symbol", req.symbol)
            .tag("interval", req.interval)
            .tag("currency", "USD")
            .field("open", float(row["open"]))
            .field("high", float(row["high"]))
            .field("low", float(row["low"]))
            .field("close", float(row["close"]))
            .field("adj_close", float(row.get("adj_close", row["close"])))
            .field("volume", float(row["volume"]))
            .time(pd.to_datetime(row["time"]))
        )
        points.append(pt)

    if points:
        write_api.write(bucket=bucket, org=org, record=points)

    return {"status": "ok", "rows": len(points)}
