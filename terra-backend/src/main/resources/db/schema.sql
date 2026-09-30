-- Create parking_logs table to record continuous time-series updates from Raspberry Pi
CREATE TABLE IF NOT EXISTS parking_logs (
                                            id BIGSERIAL PRIMARY KEY,
                                            num_cars_parked INT NOT NULL,
                                            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Per-space occupancy is independent of aggregate camera-count logs.
CREATE TABLE IF NOT EXISTS parking_spaces (
    space_id VARCHAR(32) PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    is_occupied BOOLEAN,
    last_updated TIMESTAMP NOT NULL,
    version BIGINT NOT NULL DEFAULT 0
);

-- Upgrade the earlier space_id/is_occupied/last_updated table if it exists.
ALTER TABLE parking_spaces ADD COLUMN IF NOT EXISTS label VARCHAR(100);
ALTER TABLE parking_spaces ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
UPDATE parking_spaces SET label = space_id WHERE label IS NULL;
UPDATE parking_spaces SET last_updated = CURRENT_TIMESTAMP WHERE last_updated IS NULL;
ALTER TABLE parking_spaces ALTER COLUMN space_id TYPE VARCHAR(32);
ALTER TABLE parking_spaces ALTER COLUMN label SET NOT NULL;
ALTER TABLE parking_spaces ALTER COLUMN last_updated SET NOT NULL;
ALTER TABLE parking_spaces ALTER COLUMN is_occupied DROP NOT NULL;
ALTER TABLE parking_spaces ALTER COLUMN is_occupied DROP DEFAULT;
