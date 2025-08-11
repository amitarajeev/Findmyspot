import React, { useEffect, useMemo, useState } from "react";
import RealtimeMap from "./components/RealtimeMap";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

/* -------------------------------------------------------------
   Helpers
------------------------------------------------------------- */
async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function NumberFormat({ value }) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat().format(Number(value));
}

function pct(n) {
  if (n == null || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

/* -------------------------------------------------------------
   Vehicles — registrations chart
------------------------------------------------------------- */
function VehiclesInsights() {
  const [startYear, setStartYear] = useState(2016);
  const [endYear, setEndYear] = useState(2018);
  const [years, setYears] = useState([]);
  const [totals, setTotals] = useState([]);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await fetchJSON(
        `${API_BASE}/api/vehicle-growth?start=${startYear}&end=${endYear}`
      );
      const ys = data?.years || [];
      const totalsByYear = {};
      (data?.data || []).forEach((row) => {
        const reg = row.registrations || {};
        Object.entries(reg).forEach(([y, v]) => {
          totalsByYear[y] = (totalsByYear[y] || 0) + Number(v || 0);
        });
      });
      setYears(ys);
      setTotals(ys.map((y) => totalsByYear[y] ?? 0));
      setSource(data?.source || "");
    } catch (e) {
      setErr("Failed to load vehicle registrations.");
      setYears([]);
      setTotals([]);
      setSource("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* initial */ }, []);

  const maxVal = Math.max(0, ...totals);
  const ticks = useMemo(() => {
    if (maxVal <= 0) return [0, 1, 2, 3, 4];
    const step = maxVal / 4;
    return [0, 1, 2, 3, 4].map((i) => Math.round(i * step));
  }, [maxVal]);

  const firstVal = totals[0] ?? null;
  const lastVal = totals.length ? totals[totals.length - 1] : null;
  const changeAbs = (lastVal != null && firstVal != null) ? (lastVal - firstVal) : null;
  const changePct = (lastVal != null && firstVal) ? (lastVal / firstVal - 1) : null;

  const peakIdx = totals.reduce(
    (best, v, i) => (v > totals[best] ? i : best),
    totals.length ? 0 : -1
  );
  const peakYear = peakIdx >= 0 ? years[peakIdx] : null;
  const peakVal = peakIdx >= 0 ? totals[peakIdx] : null;

  return (
    <div className="card chart-shell">
      <h2>Car Ownership — Vehicle Registrations</h2>
      <div className="row">
        <label>Start{" "}
          <input
            type="number"
            value={startYear}
            min={2016}
            max={2018}
            onChange={(e) => setStartYear(Number(e.target.value))}
          />
        </label>
        <label>End{" "}
          <input
            type="number"
            value={endYear}
            min={2016}
            max={2018}
            onChange={(e) => setEndYear(Number(e.target.value))}
          />
        </label>
        <button onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Apply"}
        </button>
      </div>

      {err && <p className="error">{err}</p>}

      <div className="chart-wrap">
        <div className="yaxis-title">Total registrations</div>
        <div className="chart-grid">
          {/* Y axis */}
          <div className="yaxis">
            {ticks.slice().reverse().map((t, i) => (
              <div key={i}><NumberFormat value={t} /></div>
            ))}
          </div>

          {/* Plot */}
          <div className="chart-row" aria-label="Vehicle registrations bar chart">
            {years.map((y, i) => {
              const v = totals[i] || 0;
              const height = maxVal > 0 ? (v / maxVal) * 100 : 0;
              return (
                <div key={y} className="bar-wrap" title={`${y} — ${v.toLocaleString()}`}>
                  <div className="bar" style={{ height: `${Math.max(2, height)}%` }} />
                  <div className="bar-x">{y}</div>
                </div>
              );
            })}
            {!years.length && (
              <div className="muted" style={{ gridColumn: "1 / -1", alignSelf: "center" }}>
                No data for range.
              </div>
            )}
          </div>
        </div>

        {/* X axis title */}
        <div className="axis-x-title">Year</div>

        {/* Legend */}
        <div className="legend">
          <span><span className="key k-fair" /> Total registrations</span>
        </div>

        {/* Insights */}
        <div className="stat-grid">
          <div className="stat">
            <div className="label">First year ({years[0] ?? "—"})</div>
            <div className="value"><NumberFormat value={firstVal} /></div>
          </div>
          <div className="stat">
            <div className="label">Last year ({years.at(-1) ?? "—"})</div>
            <div className="value"><NumberFormat value={lastVal} /></div>
          </div>
          <div className="stat">
            <div className="label">Change</div>
            <div className="value">
              <NumberFormat value={changeAbs} /> {changePct != null ? ` (${pct(changePct)})` : ""}
            </div>
          </div>
          <div className="stat">
            <div className="label">Peak year</div>
            <div className="value">
              {peakYear ?? "—"}{peakVal != null ? ` — ${peakVal.toLocaleString()}` : ""}
            </div>
          </div>
        </div>

        {source && (
          <p className="source">
            Source:{" "}
            <a href={source} target="_blank" rel="noreferrer">
              Official dataset (opens in new tab)
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------
   CBD Population — growth chart
------------------------------------------------------------- */
function PopulationInsights() {
  const [startYear, setStartYear] = useState(2015);
  const [endYear, setEndYear] = useState(2021);
  const [region, setRegion] = useState("CBD");
  const [years, setYears] = useState([]);
  const [population, setPopulation] = useState([]);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await fetchJSON(
        `${API_BASE}/api/population-growth?start=${startYear}&end=${endYear}&region=${encodeURIComponent(region)}`
      );
      const ys = data?.years || [];
      const regionObj =
        (data?.data || []).find((d) => d.region?.toLowerCase() === region.toLowerCase()) ||
        (data?.data || [])[0] || null;
      const popMap = regionObj?.population || {};
      setYears(ys);
      setPopulation(ys.map((y) => (popMap[y] != null ? Number(popMap[y]) : null)));
      setSource(data?.source || "");
    } catch (e) {
      setErr("Failed to load CBD population.");
      setYears([]);
      setPopulation([]);
      setSource("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* initial */ }, []);

  const numericVals = population.map((v) => (typeof v === "number" ? v : 0));
  const maxVal = Math.max(0, ...numericVals);
  const ticks = useMemo(() => {
    if (maxVal <= 0) return [0, 1, 2, 3, 4];
    const step = maxVal / 4;
    return [0, 1, 2, 3, 4].map((i) => Math.round(i * step));
  }, [maxVal]);

  const valid = population.filter((v) => typeof v === "number");
  const firstVal = valid.length ? population[population.findIndex((v) => typeof v === "number")] : null;
  const lastVal = valid.length ? population[population.length - 1] : null;
  const changeAbs = (lastVal != null && firstVal != null) ? (lastVal - firstVal) : null;
  const changePct = (lastVal != null && firstVal) ? (lastVal / firstVal - 1) : null;
  const nYears = years.length > 1 ? (years.length - 1) : 0;
  const cagr = (lastVal != null && firstVal && nYears > 0)
    ? (Math.pow(lastVal / firstVal, 1 / nYears) - 1)
    : null;

  const peakIdx = population.reduce(
    (best, v, i) => (typeof v === "number" && (best < 0 || v > population[best]) ? i : best),
    -1
  );
  const peakYear = peakIdx >= 0 ? years[peakIdx] : null;

  return (
    <div className="card chart-shell">
      <h2>CBD Population — Growth & Trend</h2>
      <div className="row">
        <label>Start{" "}
          <input
            type="number"
            value={startYear}
            onChange={(e) => setStartYear(Number(e.target.value))}
          />
        </label>
        <label>End{" "}
          <input
            type="number"
            value={endYear}
            onChange={(e) => setEndYear(Number(e.target.value))}
          />
        </label>
        <label>Region{" "}
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option>CBD</option>
            <option>Melbourne</option>
            <option>Greater Melbourne</option>
          </select>
        </label>
        <button onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Apply"}
        </button>
      </div>

      {err && <p className="error">{err}</p>}

      <div className="chart-wrap">
        <div className="yaxis-title">Population (est.)</div>
        <div className="chart-grid">
          {/* Y axis */}
          <div className="yaxis">
            {ticks.slice().reverse().map((t, i) => (
              <div key={i}><NumberFormat value={t} /></div>
            ))}
          </div>

          {/* Plot */}
          <div className="chart-row" aria-label="Population bar chart">
            {years.map((y, i) => {
              const v = population[i];
              const num = typeof v === "number" ? v : 0;
              const height = maxVal > 0 ? (num / maxVal) * 100 : 0;
              return (
                <div key={y} className="bar-wrap" title={`${y} — ${v == null ? "—" : v.toLocaleString()}`}>
                  <div className="bar" style={{ height: `${Math.max(2, height)}%` }} />
                  <div className="bar-x">{y}</div>
                </div>
              );
            })}
            {!years.length && (
              <div className="muted" style={{ gridColumn: "1 / -1", alignSelf: "center" }}>
                No data for range.
              </div>
            )}
          </div>
        </div>

        {/* X axis title */}
        <div className="axis-x-title">Year</div>

        {/* Legend */}
        <div className="legend">
          <span><span className="key k-fair" /> Total population</span>
        </div>

        {/* Insights */}
        <div className="stat-grid">
          <div className="stat">
            <div className="label">First year ({years[0] ?? "—"})</div>
            <div className="value"><NumberFormat value={firstVal} /></div>
          </div>
          <div className="stat">
            <div className="label">Last year ({years.at(-1) ?? "—"})</div>
            <div className="value"><NumberFormat value={lastVal} /></div>
          </div>
          <div className="stat">
            <div className="label">Change</div>
            <div className="value">
              <NumberFormat value={changeAbs} /> {changePct != null ? ` (${pct(changePct)})` : ""}
            </div>
          </div>
            <div className="stat">
              <div className="label">CAGR</div>
              <div className="value">{cagr == null ? "—" : pct(cagr)}</div>
            </div>
          <div className="stat">
            <div className="label">Peak year</div>
            <div className="value">{peakYear ?? "—"}</div>
          </div>
        </div>

        {source && (
          <p className="source">
            Source:{" "}
            <a href={source} target="_blank" rel="noreferrer">
              Official dataset (opens in new tab)
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------
   App layout — unchanged tabs
------------------------------------------------------------- */
export default function App() {
  const [tab, setTab] = useState("parking");

  useEffect(() => {
    const hash = window.location.hash.replace("#", "");
    if (hash) setTab(hash);
    const onHash = () => setTab(window.location.hash.replace("#", "") || "parking");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    if (!window.location.hash || window.location.hash.replace("#", "") !== tab) {
      window.location.hash = tab;
    }
  }, [tab]);

  return (
    <div className="app">
      <div className="nav">
        <div className="brand">FindMySpot Melbourne</div>
        <div className="spacer" />
        <button className={tab === "parking" ? "active" : ""} onClick={() => setTab("parking")}>Parking</button>
        <button className={tab === "vehicles" ? "active" : ""} onClick={() => setTab("vehicles")}>Car Ownership</button>
        <button className={tab === "population" ? "active" : ""} onClick={() => setTab("population")}>CBD Population</button>
      </div>

      <div className="container">
        {tab === "parking" && <RealtimeMap />}
        {tab === "vehicles" && <VehiclesInsights />}
        {tab === "population" && <PopulationInsights />}
      </div>

      <div className="footer">© {new Date().getFullYear()} FindMySpot • Melbourne, AU</div>
    </div>
  );
}
