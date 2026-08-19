CREATE TABLE IF NOT EXISTS network_snapshots (
    id SERIAL PRIMARY KEY,
    asn VARCHAR(20) NOT NULL,
    operator_name VARCHAR(100),
    prefix_count INTEGER,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
);