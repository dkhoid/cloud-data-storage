-- Create Database
CREATE DATABASE cloud_storage;

-- Connect to database
\c cloud_storage;

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'free', -- free, pro, enterprise
    storage_limit BIGINT DEFAULT 1073741824, -- 1GB in bytes
    storage_used BIGINT DEFAULT 0,
    stripe_customer_id VARCHAR(100),
    subscription_status VARCHAR(20) DEFAULT 'active',
    subscription_end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files Table
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    minio_object_name VARCHAR(255) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    public_url VARCHAR(500),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);

-- Billing Transactions Table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    stripe_payment_id VARCHAR(100),
    status VARCHAR(20), -- pending, completed, failed, refunded
    transaction_type VARCHAR(20), -- subscription, upgrade, one_time
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage History Table (for billing calculations)
CREATE TABLE usage_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    storage_used BIGINT,
    bandwidth_used BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Pricing Plans Table
CREATE TABLE pricing_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    storage_limit BIGINT NOT NULL,
    price_monthly DECIMAL(10, 2) NOT NULL,
    price_yearly DECIMAL(10, 2) NOT NULL,
    features JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert default pricing plans
INSERT INTO pricing_plans (name, storage_limit, price_monthly, price_yearly, features) VALUES
('free', 1073741824, 0, 0, '{"max_file_size": "50MB", "bandwidth": "1GB/month", "support": "community"}'),
('pro', 107374182400, 9.99, 99.99, '{"max_file_size": "5GB", "bandwidth": "100GB/month", "support": "email"}'),
('enterprise', 1099511627776, 29.99, 299.99, '{"max_file_size": "unlimited", "bandwidth": "unlimited", "support": "priority"}');

-- Create indexes for better performance
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_usage_history_user_date ON usage_history(user_id, date);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();