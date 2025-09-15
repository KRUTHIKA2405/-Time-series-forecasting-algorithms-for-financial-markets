from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import yfinance as yf
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

router = APIRouter(prefix="/collect/yahoo/watchlist", tags=["yahoo-watchlist"])

# Location to store the watchlist JSON
WATCHLIST_PATH = Path("watchlist.json")

# Influx setup
bucket = os.getenv("INFLUX_BUCKET", "marketdata")
org = os.getenv("INFLUX_ORG", "test")
url = os.getenv("INFLUX_URL", "http://localhost:8086")
token = os.getenv("INFLUX_TOKEN", "my-token")

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


class WatchItem(BaseModel):
    symbol: str
    interval: str
    lookback: str = "60d"  # default to 60 days


def load_watchlist():
    if not WATCHLIST_PATH.exists():
        return []
    with open(WATCHLIST_PATH, "r") as f:
        return json.load(f)


def save_watchlist(items):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(items, f, indent=2)


@router.get("/")
def get_watchlist():
    return load_watchlist()


@router.post("/add")
def add_watch(item: WatchItem):
    items = load_watchlist()
    if any(w["symbol"] == item.symbol and w["interval"] == item.interval for w in items):
        raise HTTPException(400, "Already in watchlist")
    items.append(item.dict())
    save_watchlist(items)
    return {"status": "added", "count": len(items)}


@router.post("/backfill")
def backfill_watchlist():
    items = load_watchlist()
    if not items:
        raise HTTPException(404, "No items in watchlist")

    rows_written = 0
    for it in items:
        try:
            df = yf.download(
                it["symbol"], interval=it["interval"], period=it["lookback"], progress=False
            )
        except Exception as e:
            raise HTTPException(500, f"Yahoo download failed for {it['symbol']}: {e}")

        if df is None or df.empty:
            continue

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

        points = []
        for _, row in df.iterrows():
            pt = (
                Point("bars")
                .tag("symbol", it["symbol"])
                .tag("interval", it["interval"])
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
            rows_written += len(points)

    return {"status": "ok", "rows": rows_written, "watchlist_size": len(items)}
