-- Aggregate occupancy observations; capacity stays in the frontend.
CREATE TABLE IF NOT EXISTS parking_logs (
    id BIGSERIAL PRIMARY KEY,
    num_cars_parked INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Do not seed a zero count: it would look like a fresh camera observation.
