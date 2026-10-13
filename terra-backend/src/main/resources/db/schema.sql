-- Aggregate occupancy observations; capacity stays in the frontend.
CREATE TABLE IF NOT EXISTS parking_logs (
    id BIGSERIAL PRIMARY KEY,
    num_cars_parked INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Do not seed a zero count: it would look like a fresh camera observation.

CREATE TABLE IF NOT EXISTS parking_latest_check (
    id BIGINT PRIMARY KEY,
    num_cars_parked INT NOT NULL,
    checked_at TIMESTAMP NOT NULL
);
