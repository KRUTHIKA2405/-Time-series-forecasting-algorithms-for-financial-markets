import { useState, useEffect } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [symbol, setSymbol] = useState("AAPL");
  const [interval, setInterval] = useState("5m");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/data/bars`, {
        params: { symbol, interval, start: "-7d" },
      });
      setData(res.data.data);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>📈 Time Series Forecasting Dashboard</h1>

      <div style={{ marginBottom: 20 }}>
        <label>Symbol: </label>
        <input value={symbol} onChange={(e) => setSymbol(e.target.value)} />
        <label style={{ marginLeft: 10 }}>Interval: </label>
        <input value={interval} onChange={(e) => setInterval(e.target.value)} />
        <button onClick={fetchData} style={{ marginLeft: 10 }}>
          Load Data
        </button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid stroke="#ccc" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="close" stroke="#82ca9d" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default App;
