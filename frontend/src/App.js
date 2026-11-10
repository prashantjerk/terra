import React, { useState, useEffect, useRef } from "react";
import "./App.css";

// Local override takes priority; live view is 12 spaces, original saved demo is 11.
const CAPACITY_OVERRIDE = process.env.REACT_APP_TOTAL_CAPACITY;
const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:8080";

function App() {
  const DEMO_MODE = new URLSearchParams(window.location.search).get("demo") === "14_58_01";
  const TOTAL_CAPACITY = Number(CAPACITY_OVERRIDE || (DEMO_MODE ? 11 : 12));
  if (!Number.isInteger(TOTAL_CAPACITY) || TOTAL_CAPACITY < 1) {
    throw new Error("REACT_APP_TOTAL_CAPACITY must be a positive integer");
  }
  const [occupiedCount, setOccupiedCount] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [observationStamp, setObservationStamp] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const busy = useRef(false);
  const [cooldown, setCooldown] = useState(0);
  const [freshness, setFreshness] = useState('Stored result; click Refresh to check the Pi.');
  // Fetch live aggregate status from Spring Boot backend
  const fetchParkingStatus = async (refresh = false) => {
    if (busy.current) return;
    busy.current = true;
    setLoading(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 70000);
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/parking/${refresh ? "refresh" : "status"}`,
        { method: refresh ? 'POST' : 'GET', signal: controller.signal },
      );
      if (response.status === 429 || response.status === 503) {
        const wait = Number(response.headers?.get('Retry-After')) || 10;
        setCooldown(Math.max(1, wait));
        throw new Error(response.status === 429 ? `Request limit reached. Try again in ${wait} seconds.`
          : 'Pi unavailable. Showing the previous result.');
      }
      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();

      // Extract aggregate count and optional timestamp
      const parked = data.numOfCarsParked ?? null;
      if (parked !== null && (!Number.isInteger(parked) || parked < 0)) {
        throw new Error("Invalid parked-car count");
      }
      setOccupiedCount(parked);
      setObservationStamp(data.timeStamp || null);

      if (data.timeStamp) {
        setLastUpdated(new Date(data.timeStamp).toLocaleTimeString());
      } else {
        setLastUpdated(null);
      }

      setFreshness(refresh ? 'Latest successful check (a recent result may be reused).' : 'Stored result; click Refresh to check the Pi.');
      setError(null);
    } catch (err) {
      console.error("Error fetching parking status:", err);
      setError(err.name === 'AbortError' ? 'Request timed out. Showing the previous result.' : err.message);
      setFreshness('Previous result; a fresh check has not been confirmed.');
    } finally {
      clearTimeout(timeout);
      busy.current = false;
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParkingStatus();

  }, []);

  useEffect(() => { setImageError(false); }, [observationStamp]);
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown(value => Math.max(0, value - 1)), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const availableCount = occupiedCount === null ? null : Math.max(0, TOTAL_CAPACITY - occupiedCount);

  return (
    <div className="container">
      <header className="header">
        <h1>Terra Parking Management</h1>
        <p>Campus Parking Availability on Demand</p>
      </header>

      <button onClick={() => fetchParkingStatus(true)} disabled={loading || cooldown > 0}>
        {loading ? 'Checking…' : cooldown > 0 ? `Refresh in ${cooldown}s` : 'Refresh parking status'}
      </button>
      <p role="status">{freshness}</p>
      {error && <div className="error-banner">{error}</div>}
      {occupiedCount > TOTAL_CAPACITY && (
        <div className="error-banner">Detected count exceeds the configured capacity. Review the detection boxes.</div>
      )}

      {/* Summary Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Capacity</h3>
          <p className="stat-number">{TOTAL_CAPACITY}</p>
        </div>
        <div className="stat-card available">
          <h3>Available</h3>
          <p className="stat-number">{availableCount ?? "—"}</p>
        </div>
        <div className="stat-card occupied">
          <h3>Occupied</h3>
          <p className="stat-number">{occupiedCount ?? "—"}</p>
        </div>
      </div>

      {/* Lot Status Summary Card */}
      <div className="status-container">
        <h2>Current Capacity Overview</h2>
        {loading ? (
          <p>Loading parking data...</p>
        ) : (
          <div className="occupancy-progress-wrapper">
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${Math.min(100, ((occupiedCount || 0) / TOTAL_CAPACITY) * 100)}%`,
                  backgroundColor:
                    occupiedCount >= TOTAL_CAPACITY ? "#ef5350" : "#4caf50",
                }}
              ></div>
            </div>
            <p className="update-timestamp">
              Last confirmed check: {lastUpdated || "N/A"}
            </p>
          </div>
        )}
      </div>
      {DEMO_MODE && (
        <section className="demo-photo">
          <h2>Saved-photo demo · 14:58:01</h2>
          <p>Saved image, not a live camera feed. Values above show the latest count received by the backend.</p>
          {imageError ? (
            <p role="alert">Demo photo unavailable. Pull the same photo on the backend laptop and restart from terra-backend.</p>
          ) : (
            <img key={observationStamp || "initial"}
              src={`${API_BASE}/api/v1/parking/demo-image?v=${encodeURIComponent(observationStamp || "initial")}`}
              alt="Parking lot used for the 14:58:01 saved-photo demo"
              onError={() => setImageError(true)} />
          )}
        </section>
      )}
    </div>
  );
}

export default App;
