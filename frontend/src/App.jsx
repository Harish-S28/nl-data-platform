import { useState, useRef } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

function isNumeric(val) {
  return typeof val === "number";
}

function pickChartShape(columns, rows) {
  if (!rows || rows.length === 0 || columns.length < 2) return null;
  const numericCols = columns.filter((c) => rows.every((r) => isNumeric(r[c]) || r[c] === null));
  const labelCol = columns.find((c) => !numericCols.includes(c));
  const valueCol = numericCols[0];
  if (!labelCol || !valueCol) return null;
  return { labelCol, valueCol };
}

function pickChartType(question, rowCount) {
  const q = question.toLowerCase();
  if (q.includes("pie") || q.includes("share") || q.includes("proportion") || q.includes("breakdown")) return "pie";
  if (q.includes("trend") || q.includes("over time") || q.includes("line chart") || q.includes("timeline")) return "line";
  if (q.includes("bar chart") || q.includes("bar graph")) return "bar";
  return rowCount > 12 ? "line" : "bar";
}

const PIE_COLORS = ["#e0a458", "#7fb88f", "#7f9ad9", "#d97e72", "#c79be0", "#e0c558", "#7fc4d9"];

export default function App() {
  const [dataset, setDataset] = useState(null); // {table_name, columns, row_count, original_filename}
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const [result, setResult] = useState(null); // {sql, insight, columns, rows, row_count}

  const fileInputRef = useRef(null);

  async function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadError("");
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setDataset(data);
    } catch (err) {
      setUploadError(err.message);
      setDataset(null);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim() || !dataset) return;
    setAsking(true);
    setAskError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ table_name: dataset.table_name, question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");
      setResult(data);
    } catch (err) {
      setAskError(err.message);
    } finally {
      setAsking(false);
    }
  }

  const chartShape = result ? pickChartShape(result.columns, result.rows) : null;
  const chartType = result && chartShape ? pickChartType(result.question, result.rows.length) : null;

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">⌁</span>
          <span className="brand-name">Plainquery</span>
        </div>
        <p className="tagline">Upload data. Ask in plain English. Get answers.</p>
      </header>

      <main className="main">
        <section className="panel upload-panel">
          <h2 className="panel-title">01 — Your data</h2>

          {!dataset && (
            <div className="dropzone" onClick={() => fileInputRef.current.click()}>
              <p className="dropzone-text">
                {uploading ? "Reading your file…" : "Click to choose a CSV, Excel, or JSON file"}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileChange}
                hidden
              />
            </div>
          )}

          {uploadError && <p className="error-text">{uploadError}</p>}

          {dataset && (
            <div className="dataset-card">
              <div className="dataset-card-row">
                <span className="dataset-name">{dataset.original_filename}</span>
                <button className="link-btn" onClick={() => { setDataset(null); setResult(null); }}>
                  Change file
                </button>
              </div>
              <p className="dataset-meta">
                {dataset.row_count.toLocaleString()} rows · {dataset.columns.length} columns
              </p>
              <div className="column-chips">
                {dataset.columns.map((c) => (
                  <span key={c.column} className="chip">{c.column}</span>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="panel ask-panel">
          <h2 className="panel-title">02 — Ask a question</h2>
          <form onSubmit={handleAsk} className="ask-form">
            <input
              className="ask-input"
              type="text"
              placeholder={dataset ? "e.g. what is the total revenue by product?" : "Upload a file first"}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={!dataset || asking}
            />
            <button className="primary-btn" type="submit" disabled={!dataset || asking || !question.trim()}>
              {asking ? "Thinking…" : "Ask"}
            </button>
          </form>
          {askError && <p className="error-text">{askError}</p>}
        </section>

        {result && (
          <section className="panel result-panel">
            <h2 className="panel-title">03 — Answer</h2>

            {result.insight && (
              <div className="insight-box">
                <span className="insight-label">Insight</span>
                <p className="insight-text">{result.insight}</p>
              </div>
            )}

            <div className="sql-box">
              <span className="sql-label">Generated SQL query</span>
              <pre className="sql-code">{result.sql}</pre>
            </div>

            {chartShape && (
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={280}>
                  {chartType === "pie" ? (
                    <PieChart>
                      <Pie
                        data={result.rows}
                        dataKey={chartShape.valueCol}
                        nameKey={chartShape.labelCol}
                        cx="50%"
                        cy="50%"
                        outerRadius={95}
                        label={(entry) => entry[chartShape.labelCol]}
                      >
                        {result.rows.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: "#1e2025", border: "1px solid #34363e", borderRadius: 6 }}
                      />
                      <Legend wrapperStyle={{ fontSize: 12, color: "#9a98a3" }} />
                    </PieChart>
                  ) : chartType === "line" ? (
                    <LineChart data={result.rows}>
                      <CartesianGrid stroke="#34363e" vertical={false} />
                      <XAxis dataKey={chartShape.labelCol} stroke="#9a98a3" fontSize={12} />
                      <YAxis stroke="#9a98a3" fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: "#1e2025", border: "1px solid #34363e", borderRadius: 6 }}
                      />
                      <Line dataKey={chartShape.valueCol} stroke="#e0a458" strokeWidth={2} dot={false} />
                    </LineChart>
                  ) : (
                    <BarChart data={result.rows}>
                      <CartesianGrid stroke="#34363e" vertical={false} />
                      <XAxis dataKey={chartShape.labelCol} stroke="#9a98a3" fontSize={12} />
                      <YAxis stroke="#9a98a3" fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: "#1e2025", border: "1px solid #34363e", borderRadius: 6 }}
                      />
                      <Bar dataKey={chartShape.valueCol} fill="#e0a458" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            )}

            <div className="table-wrap">
              <table className="result-table">
                <thead>
                  <tr>
                    {result.columns.map((c) => <th key={c}>{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, i) => (
                    <tr key={i}>
                      {result.columns.map((c) => <td key={c}>{String(row[c])}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
