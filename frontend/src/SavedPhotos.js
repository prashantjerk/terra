import React, { useEffect, useRef, useState } from "react";

export default function SavedPhotos({ apiBase }) {
  const [photos, setPhotos] = useState([]);
  const [photo, setPhoto] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [listing, setListing] = useState(true);
  const [checking, setChecking] = useState(false);
  const [retryAt, setRetryAt] = useState(0);
  const pending = useRef(null);
  const endpoint = `${apiBase}/api/v1/parking/photos`;

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 70000);
    fetch(endpoint, { signal: controller.signal })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not load saved photos.");
        setPhotos(data);
        setPhoto(data[0] || "");
      })
      .catch(err => setError(err.name === "AbortError" ? "Photo list request timed out." : err.message))
      .finally(() => { clearTimeout(timeout); setListing(false); });
    return () => { clearTimeout(timeout); controller.abort(); pending.current?.abort(); };
  }, [endpoint]);

  useEffect(() => {
    if (!retryAt) return;
    const timer = setTimeout(() => setRetryAt(0), Math.max(0, retryAt - Date.now()));
    return () => clearTimeout(timer);
  }, [retryAt]);

  async function check() {
    if (!photo || pending.current || retryAt) return;
    const controller = new AbortController();
    pending.current = controller;
    const timeout = setTimeout(() => controller.abort(), 70000);
    setChecking(true);
    setError("");
    try {
      const response = await fetch(`${endpoint}/check`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        signal: controller.signal, body: JSON.stringify({ photo }),
      });
      const data = await response.json();
      if (!response.ok) {
        const seconds = Number(response.headers.get("Retry-After"));
        if (seconds > 0) setRetryAt(Date.now() + seconds * 1000);
        throw new Error(data.error || "Could not analyze the photo.");
      }
      setResult(data);
    } catch (err) {
      setError(err.name === "AbortError" ? "Photo check timed out." : err.message);
    } finally {
      clearTimeout(timeout);
      pending.current = null;
      setChecking(false);
    }
  }

  return <main className="container">
    <header className="header">
      <h1>Saved photo parking check</h1>
      <p>Results describe the selected photo, not current parking availability.</p>
    </header>
    <label htmlFor="parking-photo">Parking photo</label>{" "}
    <select id="parking-photo" value={photo} disabled={listing || checking || !photos.length}
      onChange={event => { setPhoto(event.target.value); setResult(null); setError(""); }}>
      {!photos.length && <option value="">{listing ? "Loading photos…" : "No photos available"}</option>}
      {photos.map(name => <option key={name}>{name}</option>)}
    </select>{" "}
    <button disabled={!photo || checking || Boolean(retryAt)} onClick={check}>
      {checking ? "Checking…" : retryAt ? "Try again shortly" : "Check photo"}
    </button>
    {error && <p role="alert" className="error-banner">{error}</p>}
    {result && <>
      <div className="stats-grid">
        {[["Capacity", result.capacity], ["Available", result.available], ["Occupied", result.occupied]]
          .map(([label, count]) => <div key={label} className="stat-card">
            <h3>{label}</h3><p className="stat-number">{count}</p>
          </div>)}
      </div>
      <section className="demo-photo">
        <h2>{result.photo}</h2>
        <p>Analyzed {new Date(result.checkedAt).toLocaleString()}</p>
        <img src={`data:image/jpeg;base64,${result.previewJpeg}`} alt="Parking spaces outlined by occupancy" />
        <ul className="photo-spaces">
          {Object.entries(result.spaces).sort(([a], [b]) => a.localeCompare(b))
            .map(([space, status]) => <li key={space}>{space}: {status}</li>)}
        </ul>
      </section>
    </>}
  </main>;
}
