from fastapi import APIRouter, HTTPException
from services.influx_reader import get_bars


router = APIRouter()


@router.get("/bars")
def read_bars(symbol: str, interval: str, start: str = "-90d"):
df = get_bars(symbol, interval, start=start)
if df is None or df.empty:
raise HTTPException(404, "No data found")
return {
"symbol": symbol,
"interval": interval,
"rows": len(df),
"data": df.reset_index().to_dict(orient="records"),
}