from fastapi import APIRouter, HTTPException
from services.influx_reader import get_bars

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/{symbol}/{interval}")
def get_data(symbol: str, interval: str, start: str = None):
    """
    Fetch OHLCV bars for a given symbol and interval from InfluxDB.
    Example: /data/AAPL/5m?start=2024-01-01
    """
    df = get_bars(symbol, interval, start=start)

    if df is None or df.empty:
        raise HTTPException(404, "No data found")

    return {
        "symbol": symbol,
        "interval": interval,
        "rows": len(df),
        "data": df.reset_index().to_dict(orient="records"),
    }
