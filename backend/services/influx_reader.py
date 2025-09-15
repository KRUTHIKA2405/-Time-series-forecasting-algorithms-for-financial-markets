from influxdb_client import InfluxDBClient
import pandas as pd
import os

bucket = os.getenv("INFLUX_BUCKET", "marketdata")
org = os.getenv("INFLUX_ORG", "test")
url = os.getenv("INFLUX_URL", "http://localhost:8086")
token = os.getenv("INFLUX_TOKEN", "my-token")

client = InfluxDBClient(url=url, token=token, org=org)


def get_bars(symbol: str, interval: str, start: str = None) -> pd.DataFrame:
    """
    Pull OHLCV bars from InfluxDB for a given symbol & interval.
    """
    query_api = client.query_api()

    start_clause = start if start else "-30d"  # default last 30 days

    flux = f"""
    from(bucket: "{bucket}")
      |> range(start: {start_clause})
      |> filter(fn: (r) => r["_measurement"] == "ohlcv")
      |> filter(fn: (r) => r["symbol"] == "{symbol}")
      |> filter(fn: (r) => r["interval"] == "{interval}")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
      |> sort(columns: ["_time"])
    """

    tables = query_api.query_data_frame(flux)
    if not tables or len(tables) == 0:
        return pd.DataFrame()

    # Influx can return multiple tables — concat if needed
    if isinstance(tables, list):
        df = pd.concat(tables)
    else:
        df = tables

    df = df.rename(columns={"_time": "time"})
    df = df.set_index("time")
    return df
