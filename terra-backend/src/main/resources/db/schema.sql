-- Create the parking spaces table if it doesn't already exist
CREATE TABLE IF NOT EXISTS parking_spaces (
                                              space_id VARCHAR(10) PRIMARY KEY,
    is_occupied BOOLEAN NOT NULL DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Seed initial test spaces for the miniature parking lot
INSERT INTO parking_spaces (space_id, is_occupied) VALUES
                                                       ('A1', false),
                                                       ('A2', false),
                                                       ('A3', false),
                                                       ('B1', false),
                                                       ('B2', false),
                                                       ('B3', false)
    ON CONFLICT (space_id) DO NOTHING;