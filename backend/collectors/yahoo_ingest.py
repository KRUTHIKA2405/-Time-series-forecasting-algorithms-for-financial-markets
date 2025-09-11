import pandas as pd


def _infer_asset_class(symbol: str) -> str:
if symbol.endswith("-USD"): return "crypto"
if symbol.startswith("^"): return "index"
return "equity"


def _infer_venue(symbol: str) -> str:
if symbol.endswith("-USD"): return "YahooCrypto"
if symbol.startswith("^"): return "YahooIndex"
return "YahooEquity"


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def fetch_yahoo_bars(symbol: str, interval: str = "1h", period: Optional[str] = None,
start: Optional[str] = None, end: Optional[str] = None,
auto_adjust: bool = True) -> pd.DataFrame:
if interval not in YF_INTERVALS:
raise ValueError(f"Unsupported Yahoo interval: {interval}")
ticker = yf.Ticker(symbol)
kw = dict(interval=interval, auto_adjust=auto_adjust, threads=True)
if period:
kw["period"] = period
else:
kw["start"] = start
if end: kw["end"] = end
df = ticker.history(**kw)
if df is None or df.empty:
return pd.DataFrame()
df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
keep = [c for c in ["open","high","low","close","volume"] if c in df.columns]
df = df[keep].copy()
df.index = pd.to_datetime(df.index, utc=True)
df = df.reset_index().rename(columns={"index":"time", "Date":"time"})
df["time"] = pd.to_datetime(df["time"], utc=True)
for col in ["open","high","low","close","volume"]:
if col in df.columns:
df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["time","open","high","low","close"]).sort_values("time")
if "volume" in df.columns:
df["volume"] = df["volume"].fillna(0)
return df


def write_to_influx(df: pd.DataFrame, symbol: str, interval: str, measurement: str = "bars") -> int:
if df.empty: return 0
venue = _infer_venue(symbol); asset_class = _infer_asset_class(symbol)
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
w = client.write_api(write_options=SYNCHRONOUS)
pts = []
for r in df.itertuples(index=False):
p = (Point(measurement)
.tag("asset_class", asset_class)
.tag("symbol", symbol)
.tag("venue", venue)
.tag("interval", interval)
.tag("currency", "USD")
.field("open", float(r.open))
.field("high", float(r.high))
.field("low", float(r.low))
.field("close", float(r.close))
.field("volume", float(getattr(r, "volume", 0.0)))
.time(pd.Timestamp(r.time).to_pydatetime()))
pts.append(p)
if pts:
w.write(bucket=INFLUX_BUCKET, record=pts)
return len(pts)


def backfill_yahoo(symbol: str, interval: str, period: Optional[str] = None,
start: Optional[str] = None, end: Optional[str] = None,
auto_adjust: bool = True) -> int:
df = fetch_yahoo_bars(symbol, interval=interval, period=period, start=start, end=end, auto_adjust=auto_adjust)
return write_to_influx(df, symbol=symbol, interval=interval)