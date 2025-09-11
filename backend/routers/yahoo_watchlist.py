from fastapi import APIRouter, HTTPException
from pathlib import Path
import json, traceback
from collectors.yahoo_ingest import backfill_yahoo


router = APIRouter()
WATCHLIST_PATH = Path(__file__).resolve().parents[1] / "collectors" / "watchlist.json"


@router.post("/backfill/watchlist")
def backfill_watchlist():
if not WATCHLIST_PATH.exists():
raise HTTPException(400, f"watchlist not found at {WATCHLIST_PATH}")
try:
items = json.loads(WATCHLIST_PATH.read_text())
results = []
for it in items:
sym = it["symbol"]; interval = it["interval"]
period = it.get("period"); start = it.get("start"); end = it.get("end")
rows = backfill_yahoo(sym, interval=interval, period=period, start=start, end=end)
results.append({"symbol": sym, "interval": interval, "rows_written": int(rows)})
return {"status":"ok", "count": len(results), "items": results}
except Exception as e:
traceback.print_exc()
raise HTTPException(500, f"Batch backfill failed: {e}")