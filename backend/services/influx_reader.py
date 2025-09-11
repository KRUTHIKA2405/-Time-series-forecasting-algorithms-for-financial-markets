from influxdb_client import InfluxDBClient
import pandas as pd
import os


INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "devtoken")
INFLUX_ORG = os.getenv("INFLUX_ORG", "your_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "market_data")


_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
_query_api = _client.query_api()


def get_bars(symbol: str, interval: str, start: str = "-365d") -> pd.DataFrame:
flux = f'''
from(bucket: "{INFLUX_BUCKET}")
|> range(start: {start})
|> filter(fn: (r) => r._measurement == "bars")
|> filter(fn: (r) => r.symbol == "{symbol}")
|> filter(fn: (r) => r.interval == "{interval}")
|> filter(fn: (r) => r.currency == "USD")
|> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
|> keep(columns: ["_time","open","high","low","close","volume"])
|> sort(columns: ["_time"])
'''
tables = _query_api.query_data_frame(flux)
if tables is None or (isinstance(tables, list) and len(tables) == 0):
return pd.DataFrame()
if isinstance(tables, list):
df = pd.concat(tables, ignore_index=True)
else:
df = tables
if df.empty:
return df
df = df.rename(columns={"_time": "time"}).set_index("time")
return df