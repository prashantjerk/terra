-- Create parking_logs table to record continuous time-series updates from Raspberry Pi
CREATE TABLE IF NOT EXISTS parking_logs (
                                            id BIGSERIAL PRIMARY KEY,
                                            num_cars_parked INT NOT NULL,
                                            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial test log entry
INSERT INTO parking_logs (num_cars_parked, recorded_at)
VALUES (0, CURRENT_TIMESTAMP);