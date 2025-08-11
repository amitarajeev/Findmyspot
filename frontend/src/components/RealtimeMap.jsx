import React, { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

async function j(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function haversineMeters(a, b) {
  if (!a || !b) return null;
  const toRad = (x) => (x * Math.PI) / 180;
  const R = 6371000;
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function pct(x) {
  if (x == null) return "—";
  return `${Math.round(x * 100)}%`;
}

/* ---------- Friendly rule helpers ---------- */
function toAmPm(t) {
  if (!t) return "";
  const s = String(t);
  let h = 0, m = 0;
  if (s.includes(":")) {
    const [H, M = "0"] = s.split(":");
    h = parseInt(H, 10) || 0;
    m = parseInt(M, 10) || 0;
  } else {
    h = parseInt(s, 10) || 0;
  }
  const ampm = h >= 12 ? "pm" : "am";
  const h12 = ((h + 11) % 12) + 1;
  return m ? `${h12}:${String(m).padStart(2, "0")} ${ampm}` : `${h12} ${ampm}`;
}
function niceDays(s) {
  const map = {
    "Mon-Fri": "Weekdays",
    "Mon–Fri": "Weekdays",
    "Sat-Sun": "Saturday & Sunday",
    "Sat–Sun": "Saturday & Sunday",
    Sat: "Saturday",
    Sun: "Sunday",
  };
  return map[s] || s || "All days";
}
function explainCode(code) {
  const map = {
    MP2P: "Max 2P (2-hour limit)",
    LZ30: "Loading zone (30-min)",
    LZ15: "Loading zone (15-min)",
    "2P": "2-hour limit",
    "1P": "1-hour limit",
    NP: "No parking",
    P: "General parking",
  };
  return map[code] || null;
}
function normalizeRule(raw) {
  let r = raw;
  if (typeof r === "string") { try { r = JSON.parse(r); } catch {} }
  if (typeof r === "string") return { text: r, sentence: r };

  const days = r.Restriction_Days || r.Days || r.DayType || r.Day || r.Day_Type || "";
  const disp = r.Restriction_Display || r.SignPlateText || r.Sign || r.Display || "";
  const startRaw = r.Time_Restrictions_Start || r.Start || r.StartTime || "";
  const endRaw   = r.Time_Restrictions_Finish || r.End || r.EndTime || "";

  const fmt = (x) => String(x || "").replace(":00:00", "").replace(/:00$/, "");
  const window = startRaw && endRaw ? `${fmt(startRaw)}–${fmt(endRaw)}` : "";

  const daysNice = niceDays(String(days));
  const codeNote = explainCode(String(disp));
  const start = toAmPm(fmt(startRaw));
  const finish = toAmPm(fmt(endRaw));

  let sentence = "";
  if (codeNote && /^no parking/i.test(codeNote)) {
    sentence = `${daysNice}: No parking from ${start} to ${finish}.`;
  } else {
    sentence = `${daysNice}: ${codeNote ? `${codeNote}. ` : ""}You can park here from ${start} to ${finish}.`;
  }

  return {
    days: String(days),
    display: String(disp),
    window,
    text: [days, disp, window].filter(Boolean).join(" • "),
    sentence,
  };
}

export default function RealtimeMap() {
  const [subTab, setSubTab] = useState("finder");

  // Finder
  const [street, setStreet] = useState("Collins");
  const [foundZones, setFoundZones] = useState([]);
  const [zonesBusy, setZonesBusy] = useState(false);
  const [selectedZone, setSelectedZone] = useState(null);

  // Realtime
  const [onlyAvailable, setOnlyAvailable] = useState(true);
  const [radius, setRadius] = useState(1000);
  const [limit, setLimit] = useState(10);
  const [realtime, setRealtime] = useState([]);
  const [rtBusy, setRtBusy] = useState(false);

  // Predictions
  const [pDayType, setPDayType] = useState("Weekday");
  const [pStartHour, setPStartHour] = useState(10);
  const [pHorizon, setPHorizon] = useState(3);
  const [predRows, setPredRows] = useState([]);
  const [predSuggest, setPredSuggest] = useState([]);
  const [predBusy, setPredBusy] = useState(false);

  // Historical
  const [hDayType, setHDayType] = useState("Weekday");
  const [hist, setHist] = useState({});
  const [histBusy, setHistBusy] = useState(false);

  // Rules
  const [rules, setRules] = useState([]);
  const [rulesBusy, setRulesBusy] = useState(false);

  // Location
  const [pos, setPos] = useState(null);
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (p) => setPos({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => setPos(null),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, []);

  // Clear panels when zone changes
  useEffect(() => {
    setPredRows([]);
    setPredSuggest([]);
    setHist({});
    setRules([]);
  }, [selectedZone]);

  // Finder — search zones
  const findZones = async () => {
    setZonesBusy(true);
    setFoundZones([]);
    try {
      const data = await j(`${API_BASE}/api/parking/zones?on_street=${encodeURIComponent(street)}`);
      const zones = (data?.zones || []).slice(0, 30);
      const augmented = await Promise.all(
        zones.map(async (z) => {
          try {
            const snap = await j(`${API_BASE}/api/parking/realtime?zone_number=${z}&only_available=false`);
            const rows = snap?.results || [];
            const labels = {};
            let latSum = 0, lonSum = 0, n = 0;
            rows.forEach((r) => {
              const lab = (r.RoadSegmentDescription || "").trim();
              if (lab) labels[lab] = (labels[lab] || 0) + 1;
              const lat = Number(r.Latitude ?? r.Latitude_x);
              const lon = Number(r.Longitude ?? r.Longitude_x);
              if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
                latSum += lat; lonSum += lon; n += 1;
              }
            });
            const label = Object.entries(labels).sort((a, b) => b[1] - a[1])[0]?.[0] || "Unknown";
            const centroid = n ? { lat: latSum / n, lon: lonSum / n } : null;
            return { zone: z, label, centroid };
          } catch {
            return { zone: z, label: "Unknown", centroid: null };
          }
        })
      );
      setFoundZones(augmented.filter((z) => z.label && z.label !== "Unknown"));
    } catch {
      setFoundZones([]);
    } finally {
      setZonesBusy(false);
    }
  };

  // Realtime — snapshot
  const loadRealtime = async () => {
    setRtBusy(true);
    setRealtime([]);
    try {
      const url = new URL(`${API_BASE}/api/parking/realtime`);
      if (selectedZone) url.searchParams.set("zone_number", selectedZone);
      url.searchParams.set("only_available", String(!!onlyAvailable));
      const data = await j(url.toString());
      const rows = data?.results || [];

      const map = new Map();
      rows.forEach((r) => {
        const zid = r.Zone_Number ?? r.Zone ?? r.zone ?? null;
        if (zid == null) return;
        const k = String(zid);
        const free = String(r.Status_Description || "").toLowerCase() === "unoccupied";
        const prev = map.get(k) || {
          zone: Number(zid),
          free: 0, total: 0,
          latSum: 0, lonSum: 0, n: 0,
          labels: {},
        };
        prev.total += 1;
        if (free) prev.free += 1;
        const lab = (r.RoadSegmentDescription || "").trim();
        if (lab) prev.labels[lab] = (prev.labels[lab] || 0) + 1;
        const lat = Number(r.Latitude ?? r.Latitude_x);
        const lon = Number(r.Longitude ?? r.Longitude_x);
        if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
          prev.latSum += lat; prev.lonSum += lon; prev.n += 1;
        }
        map.set(k, prev);
      });

      let list = Array.from(map.values()).map((v) => {
        const centroid = v.n ? { lat: v.latSum / v.n, lon: v.lonSum / v.n } : null;
        const distance = pos && centroid ? haversineMeters(pos, centroid) : null;
        const label =
          Object.entries(v.labels).sort((a, b) => b[1] - a[1])[0]?.[0] || "Street segment";
        return { zone: v.zone, free: v.free, total: v.total, centroid, distance, label };
      });

      list.sort((a, b) => {
        const d = b.free - a.free;
        if (d) return d;
        if (a.distance == null) return 1;
        if (b.distance == null) return -1;
        return a.distance - b.distance;
      });

      if (pos) list = list.filter((z) => z.distance == null || z.distance <= radius);
      list = list.slice(0, limit);

      setRealtime(list);
    } catch {
      setRealtime([]);
    } finally {
      setRtBusy(false);
    }
  };

  // Predictions
  const predict = async () => {
    if (!selectedZone) return;
    setPredBusy(true);
    setPredRows([]); setPredSuggest([]);
    try {
      const url = new URL(`${API_BASE}/api/parking/predict`);
      url.searchParams.set("zone_number", selectedZone);
      url.searchParams.set("hour", String(pStartHour));
      url.searchParams.set("day_type", pDayType);
      url.searchParams.set("hours_ahead", String(pHorizon));
      url.searchParams.set("suggest_nearby", "true");
      url.searchParams.set("radius_m", "600");
      const data = await j(url.toString());
      setPredRows(data?.predictions || []);
      setPredSuggest(data?.suggested_zones || []);
    } catch {
      setPredRows([]); setPredSuggest([]);
    } finally {
      setPredBusy(false);
    }
  };

  // History
  const loadHist = async () => {
    if (!selectedZone) return;
    setHistBusy(true); setHist({});
    try {
      const data = await j(
        `${API_BASE}/api/parking/historical?zone_number=${selectedZone}&day_type=${encodeURIComponent(hDayType)}`
      );
      setHist(data?.availability_by_hour || {});
    } catch {
      setHist({});
    } finally {
      setHistBusy(false);
    }
  };

  // Rules
  const loadRules = async () => {
    if (!selectedZone) return;
    setRulesBusy(true); setRules([]);
    try {
      const data = await j(`${API_BASE}/api/parking/zone/${selectedZone}/rules`);
      const items = (data?.rules || []).map(normalizeRule);
      setRules(items);
    } catch {
      setRules([]);
    } finally {
      setRulesBusy(false);
    }
  };

  // Initial realtime (Quick Find)
  useEffect(() => { loadRealtime(); /* eslint-disable-next-line */ }, []);

  /* === Historical chart derived values === */
  const hours24 = useMemo(() => Array.from({ length: 24 }, (_, h) => h), []);
  const histValues = useMemo(
    () => hours24.map((h) => Number(hist[h] ?? 0)),
    [hist, hours24]
  );
  const hasHistData = histValues.some((v) => v > 0);
  const maxHist = Math.max(1, ...histValues);

  // ticks (0%, 25%, 50%, 75%, 100%)
  const histTicks = useMemo(() => {
    const bases = [0, 0.25, 0.5, 0.75, 1];
    return bases.map((b) => Math.round(maxHist * b));
  }, [maxHist]);

  // dynamic color scale (so you don't see all-red when values are small)
  const colorFor = (v) => {
    const ratio = maxHist ? v / maxHist : 0;
    if (ratio >= 0.66) return "var(--green)";     // good
    if (ratio >= 0.33) return "var(--accent)";    // fair
    return "var(--red)";                          // poor
  };

  return (
    <div className="card">
      <div className="row" style={{ marginBottom: 12 }}>
        <button
          className={subTab === "finder" ? "active" : ""}
          onClick={() => setSubTab("finder")}
        >
          Finder & Predictions
        </button>
        <button
          className={subTab === "realtime" ? "active" : ""}
          onClick={() => setSubTab("realtime")}
        >
          Realtime Nearby
        </button>
      </div>

      {subTab === "finder" && (
        <div className="grid-2">
          {/* LEFT */}
          <div className="panel">
            <h2>Parking Finder — Melbourne CBD</h2>

            <h3>Search zones by street</h3>
            <div className="row">
              <input
                value={street}
                onChange={(e) => setStreet(e.target.value)}
                placeholder="e.g., Lonsdale Street"
              />
              <button onClick={findZones} disabled={zonesBusy}>
                {zonesBusy ? "Finding…" : "Find Zones"}
              </button>
            </div>

            <div className="zone-list">
              {foundZones.map((z) => (
                <button
                  key={z.zone}
                  className={"zone" + (selectedZone === z.zone ? " active" : "")}
                  onClick={() => setSelectedZone(z.zone)}
                  title={z.label}
                >
                  <div className="zone-title">Zone {z.zone}</div>
                  <div className="zone-sub">{z.label}</div>
                </button>
              ))}
              {!foundZones.length && (
                <div className="muted">Enter a street and click Find Zones.</div>
              )}
            </div>
          </div>

          {/* RIGHT */}
          <div className="panel">
            <h3>Predictions (next 1–3 hours)</h3>
            <div className="row">
              <select value={pDayType} onChange={(e) => setPDayType(e.target.value)}>
                <option>Weekday</option>
                <option>Saturday</option>
                <option>Sunday</option>
              </select>
              <select
                value={pStartHour}
                onChange={(e) => setPStartHour(Number(e.target.value))}
              >
                {Array.from({ length: 24 }).map((_, h) => (
                  <option key={h} value={h}>
                    {String(h).padStart(2, "0")}:00
                  </option>
                ))}
              </select>
              <select
                value={pHorizon}
                onChange={(e) => setPHorizon(Number(e.target.value))}
              >
                <option value={1}>+1h</option>
                <option value={2}>+2h</option>
                <option value={3}>+3h</option>
              </select>
              <button onClick={predict} disabled={predBusy || !selectedZone}>
                {predBusy ? "Predicting…" : "Predict"}
              </button>
            </div>
            {!selectedZone && <div className="muted">Select a zone to see predictions.</div>}
            {!!predRows.length && (
              <ul className="list">
                {predRows.map((p, i) => (
                  <li key={i} className="li">
                    <div className="li-main">
                      <div className="li-title">
                        Hour {String(p.hour).padStart(2, "0")}:00 — <b>{pct(p.predicted_availability)}</b>
                      </div>
                      <span className="badge">~{p.available_spots} spots</span>
                    </div>
                    <div className="li-sub">
                      <span>{p.status}</span>
                      <span>confidence {Math.round((p.confidence_score || 0) * 100)}%</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {!!predSuggest.length && (
              <>
                <h3>Nearby suggestions</h3>
                <ul className="list">
                  {predSuggest.map((s, i) => (
                    <li key={i} className="li">
                      <div className="li-main">
                        <div className="li-title">
                          Zone {s.zone_number} — best around {String(s.best_hour).padStart(2, "0")}:00
                        </div>
                        <span className="badge">{pct(s.best_predicted_availability)}</span>
                      </div>
                      <div className="li-sub">
                        <span>{Math.round(s.distance_m)} m away</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}

            <div className="divider" />

            <h3>Historical trends (typical free spots by hour)</h3>
            <div className="row">
              <select value={hDayType} onChange={(e) => setHDayType(e.target.value)}>
                <option>Weekday</option>
                <option>Saturday</option>
                <option>Sunday</option>
              </select>
              <button onClick={loadHist} disabled={histBusy || !selectedZone}>
                {histBusy ? "Loading…" : "Refresh"}
              </button>
            </div>
            {!selectedZone && <div className="muted">Select a zone to see hourly trends.</div>}

            {hasHistData ? (
              <>
                <div className="chart">
                  <div className="chart-wrap">
                    <div className="yaxis-title">Typical free spots</div>

                    <div className="chart-grid">
                      <div className="yaxis">
                        {[...histTicks].reverse().map((t, i) => (
                          <div key={i}>{t}</div>
                        ))}
                      </div>

                      <div className="chart-row">
                        {hours24.map((h) => {
                          const v = Number(hist[h] ?? 0);
                          const height = Math.min(100, (v / maxHist) * 100);
                          return (
                            <div key={h} className="bar-wrap" title={`${String(h).padStart(2, "0")}:00 — ${v} free`}>
                              <div className="bar" style={{ height: `${height}%`, background: colorFor(v) }} />
                              <div className="bar-x">{String(h).padStart(2, "0")}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="axis-x-title">Hour of day (24h)</div>
                  </div>
                </div>

                <div className="legend-sm">
                  <span><i className="key k-good" /> Good (≥ ⅔ of max)</span>
                  <span><i className="key k-fair" /> Fair (⅓–⅔ of max)</span>
                  <span><i className="key k-poor" /> Poor (&lt; ⅓ of max)</span>
                </div>
              </>
            ) : (
              selectedZone && <div className="muted">No data. Refresh to load.</div>
            )}

            <div className="divider" />

            <h3>Zone rules & sign plates</h3>
            <div className="row">
              <button onClick={loadRules} disabled={!selectedZone || rulesBusy}>
                {rulesBusy ? "Loading…" : "Load Rules"}
              </button>
            </div>

            {!!rules.length && (
              <div className="rules" style={{ maxHeight: 220, overflow: "auto" }}>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {rules.map((r, i) => (
                    <li key={i} style={{ marginBottom: 10, lineHeight: 1.6 }}>
                      {r.sentence || r.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {!rulesBusy && !rules.length && selectedZone && (
              <div className="muted">No rules loaded. Click “Load Rules”.</div>
            )}
          </div>
        </div>
      )}

      {subTab === "realtime" && (
        <>
          <h3>Realtime availability</h3>
          <div className="row" style={{ gap: 12 }}>
            <label className="chk">
              <input
                type="checkbox"
                checked={onlyAvailable}
                onChange={(e) => setOnlyAvailable(e.target.checked)}
              />
              Only show available
            </label>

            <label>
              Radius
              <select value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
                <option value={500}>500 m</option>
                <option value={800}>800 m</option>
                <option value={1000}>1000 m</option>
                <option value={1500}>1500 m</option>
                <option value={2000}>2000 m</option>
              </select>
            </label>

            <label>
              Top
              <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={20}>20</option>
              </select>
            </label>

            <button onClick={loadRealtime} disabled={rtBusy}>
              {rtBusy ? "Loading…" : "Refresh"}
            </button>
            <button
              onClick={() => {
                setSelectedZone(null);
                loadRealtime();
              }}
              disabled={rtBusy}
            >
              Quick Find
            </button>
          </div>

          <ul className="list">
            {realtime.map((z) => (
              <li key={z.zone} className="li">
                <div className="li-main">
                  <div className="li-title">
                    Zone {z.zone} — {z.label || "Street segment"}
                  </div>
                  <span className="badge">
                    {z.free}/{z.total} free
                  </span>
                </div>
                <div className="li-sub">
                  <span>
                    Distance: {z.distance != null ? `${Math.round(z.distance)} m` : "—"}
                  </span>
                  {z.centroid && (
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${z.centroid.lat},${z.centroid.lon}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open in Maps
                    </a>
                  )}
                </div>
              </li>
            ))}
            {!realtime.length && (
              <li className="muted">
                No results within the selected radius. Try widening the radius or
                disabling “Only show available”.
              </li>
            )}
          </ul>
        </>
      )}
    </div>
  );
}
