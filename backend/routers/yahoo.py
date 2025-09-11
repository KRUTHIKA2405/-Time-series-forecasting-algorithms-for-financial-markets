from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from collectors.yahoo_ingest import backfill_yahoo


router = APIRouter()


class YahooBackfillReq(BaseModel):
symbol: str # e.g., "AAPL", "^GSPC", "BTC-USD"
interval: str # e.g., "1m","5m","1h","1d"
period: Optional[str] = None # e.g., "1mo","3mo","1y","max"
start: Optional[str] = None # "YYYY-MM-DD"
end: Optional[str] = None
auto_adjust: bool = True


@router.post("/backfill")
def yahoo_backfill(req: YahooBackfillReq):
if not req.period and not req.start:
raise HTTPException(400, "Provide either period or (start[, end]).")
rows = backfill_yahoo(
symbol=req.symbol,
interval=req.interval,
period=req.period,
start=req.start,
end=req.end,
auto_adjust=req.auto_adjust,
)
return {"status":"ok","rows_written":int(rows),"symbol":req.symbol,"interval":req.interval}