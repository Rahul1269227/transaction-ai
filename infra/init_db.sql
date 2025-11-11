-- Initialize database schema for transaction categorization

-- Enable pgvector extension (if available)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    original_text TEXT NOT NULL,
    amount DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'INR',
    date DATE,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    confidence DECIMAL(5, 4),
    method VARCHAR(50),
    merchant VARCHAR(255),
    channel VARCHAR(50),
    reference VARCHAR(255),
    requires_review BOOLEAN DEFAULT FALSE,
    reviewed BOOLEAN DEFAULT FALSE,
    correct_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Merchants table
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(50) UNIQUE NOT NULL,
    canonical_name VARCHAR(255) NOT NULL,
    aliases TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    -- embedding VECTOR(384), -- Uncomment if pgvector is available
    transaction_count INTEGER DEFAULT 0,
    confidence_avg DECIMAL(5, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    transaction_text TEXT NOT NULL,
    predicted_category VARCHAR(100) NOT NULL,
    correct_category VARCHAR(100) NOT NULL,
    predicted_subcategory VARCHAR(100),
    correct_subcategory VARCHAR(100),
    amount DECIMAL(15, 2),
    date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training jobs table
CREATE TABLE IF NOT EXISTS training_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    dataset_path TEXT,
    model_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'queued',
    accuracy DECIMAL(5, 4),
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_requires_review ON transactions(requires_review);
CREATE INDEX IF NOT EXISTS idx_merchants_canonical_name ON merchants(canonical_name);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_merchants_updated_at BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
