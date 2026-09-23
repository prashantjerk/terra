import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch live status from Spring Boot backend
  const fetchParkingStatus = async () => {
    try {
      const response = await fetch(
        "http://localhost:8080/api/v1/parking/status",
      );
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      const data = await response.json();

      // Extract the array from the backend response wrapper
      if (data && Array.isArray(data.allSpaces)) {
        setSpaces(data.allSpaces);
        setError(null);
      } else if (Array.isArray(data)) {
        setSpaces(data);
        setError(null);
      } else {
        console.error("Unexpected payload structure:", data);
        setSpaces([]);
        setError("Invalid data format received from backend.");
      }
    } catch (err) {
      console.error("Error fetching parking data:", err);
      setSpaces([]);
      setError("Unable to connect to Terra Backend (http://localhost:8080).");
    } finally {
      setLoading(false);
    }
  };

  // Toggle space occupancy state
  const toggleOccupancy = async (spaceId, currentStatus) => {
    try {
      const response = await fetch(
        `http://localhost:8080/api/v1/parking/update/${spaceId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ isOccupied: !currentStatus }),
        },
      );

      if (response.ok) {
        fetchParkingStatus(); // Refresh grid after update
      } else {
        alert("Failed to update parking space status.");
      }
    } catch (err) {
      console.error("Error updating space:", err);
      alert("Error reaching backend server.");
    }
  };

  useEffect(() => {
    fetchParkingStatus();
    const interval = setInterval(fetchParkingStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  // Safe checks using Array.isArray
  const safeSpaces = Array.isArray(spaces) ? spaces : [];
  const totalSpaces = safeSpaces.length;
  const occupiedSpaces = safeSpaces.filter(
    (s) => s.occupied || s.isOccupied,
  ).length;
  const availableSpaces = totalSpaces - occupiedSpaces;

  return (
    <div className="container">
      <header className="header">
        <h1>Terra Parking Management</h1>
        <p>Real-Time Campus Parking Availability</p>
      </header>

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Spaces</h3>
          <p className="stat-number">{totalSpaces}</p>
        </div>
        <div className="stat-card available">
          <h3>Available</h3>
          <p className="stat-number">{availableSpaces}</p>
        </div>
        <div className="stat-card occupied">
          <h3>Occupied</h3>
          <p className="stat-number">{occupiedSpaces}</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Interactive Parking Lot Grid */}
      <h2>Parking Lot Grid</h2>
      {loading ? (
        <p>Loading parking spaces...</p>
      ) : (
        <div className="parking-grid">
          {safeSpaces.map((space) => {
            const isOccupied = space.occupied ?? space.isOccupied;
            return (
              <div
                key={space.spaceId || space.id}
                className={`parking-space ${isOccupied ? "occupied" : "available"}`}
                onClick={() =>
                  toggleOccupancy(space.spaceId || space.id, isOccupied)
                }
              >
                <div className="space-id">{space.spaceId || space.id}</div>
                <div className="space-status">
                  {isOccupied ? "OCCUPIED" : "VACANT"}
                </div>
                <div className="click-hint">Click to toggle</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
