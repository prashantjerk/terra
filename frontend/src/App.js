import React, { useState, useEffect } from "react";
import "./App.css";

const TOTAL_CAPACITY = 6; // Set your lot's fixed capacity here

function App() {
  const [occupiedCount, setOccupiedCount] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch live aggregate status from Spring Boot backend
  const fetchParkingStatus = async () => {
    try {
      const response = await fetch(
        "http://localhost:8080/api/v1/parking/status",
      );
      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();

      // Extract aggregate count and optional timestamp
      const parked = data.numOfCarsParked ?? 0;
      setOccupiedCount(parked);

      if (data.timeStamp) {
        setLastUpdated(new Date(data.timeStamp).toLocaleTimeString());
      } else {
        setLastUpdated(null);
      }

      setError(null);
    } catch (err) {
      console.error("Error fetching parking status:", err);
      setError("Unable to connect to Terra Backend (http://localhost:8080).");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParkingStatus();
    const interval = setInterval(fetchParkingStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const availableCount = Math.max(0, TOTAL_CAPACITY - occupiedCount);

  return (
    <div className="container">
      <header className="header">
        <h1>Terra Parking Management</h1>
        <p>Real-Time Campus Parking Availability</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {/* Summary Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Capacity</h3>
          <p className="stat-number">{TOTAL_CAPACITY}</p>
        </div>
        <div className="stat-card available">
          <h3>Available</h3>
          <p className="stat-number">{availableCount}</p>
        </div>
        <div className="stat-card occupied">
          <h3>Occupied</h3>
          <p className="stat-number">{occupiedCount}</p>
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
                  width: `${(occupiedCount / TOTAL_CAPACITY) * 100}%`,
                  backgroundColor:
                    occupiedCount >= TOTAL_CAPACITY ? "#ef5350" : "#4caf50",
                }}
              ></div>
            </div>
            <p className="update-timestamp">
              Last sensor update: {lastUpdated || "N/A"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
