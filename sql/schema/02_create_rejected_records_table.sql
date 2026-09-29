CREATE TABLE rejected_records (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(50) NOT NULL,
    raw_data JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rejected_records_source_table
        CHECK (source_table IN ('customers', 'products', 'orders', 'order_items'))
);
