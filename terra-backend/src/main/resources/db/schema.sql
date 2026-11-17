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

CREATE TABLE IF NOT EXISTS parking_photo_results (
    id BIGSERIAL PRIMARY KEY,
    photo_id VARCHAR(255) NOT NULL,
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    occupied INT NOT NULL CHECK (occupied >= 0 AND occupied <= capacity),
    occupied_spaces VARCHAR(255) NOT NULL
);
