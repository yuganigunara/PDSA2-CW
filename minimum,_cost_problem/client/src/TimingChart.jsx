import { useState, useEffect } from "react";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const API = "http://localhost:8000";

export function TimingChart() {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchChartData();
  }, []);

  const fetchChartData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/game/chart-data?limit=20`);
      if (!res.ok) throw new Error("Failed to fetch chart data");
      
      const data = await res.json();
      
      if (data.length === 0) {
        setError("No game rounds available for chart");
        setLoading(false);
        return;
      }

      const labels = data.map((d, i) => `Round ${d.round_id}`);
      const hungarianTimes = data.map((d) => d.hungarian_time_ms);
      const greedyTimes = data.map((d) => d.greedy_time_ms);

      setChartData({
        labels,
        datasets: [
          {
            label: "Hungarian Algorithm (ms)",
            data: hungarianTimes,
            borderColor: "#22c55e",
            backgroundColor: "rgba(34, 197, 94, 0.1)",
            tension: 0.4,
            fill: true,
            pointBackgroundColor: "#22c55e",
            pointBorderColor: "#fff",
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "Greedy Algorithm (ms)",
            data: greedyTimes,
            borderColor: "#f97316",
            backgroundColor: "rgba(249, 115, 22, 0.1)",
            tension: 0.4,
            fill: true,
            pointBackgroundColor: "#f97316",
            pointBorderColor: "#fff",
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      });
      setLoading(false);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div className="section-label">LAST 20 ROUNDS - EXECUTION TIME COMPARISON</div>
        <button className="refresh-btn" onClick={fetchChartData} disabled={loading}>
          {loading ? "Loading..." : "🔄 Refresh"}
        </button>
      </div>

      {error && <div className="chart-error">{error}</div>}

      {loading && <div className="chart-loading">Loading chart data...</div>}

      {chartData && !loading && (
        <div className="chart-wrapper">
          <Line
            data={chartData}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: "top",
                  labels: {
                    color: "#999",
                    font: { size: 12 },
                    usePointStyle: true,
                    padding: 15,
                  },
                },
                title: {
                  display: false,
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: "Time (milliseconds)",
                    color: "#666",
                  },
                  grid: {
                    color: "rgba(255, 255, 255, 0.05)",
                  },
                  ticks: {
                    color: "#999",
                  },
                },
                x: {
                  title: {
                    display: true,
                    text: "Round Number",
                    color: "#666",
                  },
                  grid: {
                    color: "rgba(255, 255, 255, 0.05)",
                  },
                  ticks: {
                    color: "#999",
                  },
                },
              },
            }}
          />
        </div>
      )}
    </div>
  );
}
