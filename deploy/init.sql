-- Market7 Database Initialization Script
-- This script sets up the database schema for the trading system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS indicators;
CREATE SCHEMA IF NOT EXISTS config;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Trading tables
CREATE TABLE IF NOT EXISTS trading.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'cancelled', 'failed')),
    exchange VARCHAR(20) NOT NULL,
    order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    quantity DECIMAL(20, 8) NOT NULL,
    avg_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.dca_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    position_id UUID REFERENCES trading.positions(id),
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold')),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    volume DECIMAL(20, 8) NOT NULL,
    reason TEXT,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE
);

-- ML tables
CREATE TABLE IF NOT EXISTS ml.models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    training_data_size INTEGER,
    training_duration INTERVAL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml.predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES ml.models(id),
    symbol VARCHAR(20) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    prediction_value DECIMAL(20, 8),
    confidence DECIMAL(5, 4),
    probability DECIMAL(5, 4),
    input_features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml.training_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES ml.models(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    training_data_size INTEGER,
    validation_accuracy DECIMAL(5, 4),
    test_accuracy DECIMAL(5, 4),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indicator tables
CREATE TABLE IF NOT EXISTS indicators.indicator_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, timeframe, indicator_name, timestamp)
);

CREATE TABLE IF NOT EXISTS indicators.indicator_quality (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    quality_score DECIMAL(5, 4) NOT NULL CHECK (quality_score >= 0 AND quality_score <= 1),
    validation_issues JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Configuration tables
CREATE TABLE IF NOT EXISTS config.system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS config.environment_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    environment VARCHAR(20) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(environment, config_key)
);

-- Monitoring tables
CREATE TABLE IF NOT EXISTS monitoring.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 8) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'unhealthy', 'degraded')),
    response_time_ms INTEGER,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'suppressed')),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trading.trades(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trading.trades(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON trading.positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON trading.positions(status);
CREATE INDEX IF NOT EXISTS idx_dca_signals_symbol ON trading.dca_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_dca_signals_executed ON trading.dca_signals(executed);

CREATE INDEX IF NOT EXISTS idx_models_type_active ON ml.models(model_type, is_active);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_timestamp ON ml.predictions(symbol, created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON ml.predictions(model_id);

CREATE INDEX IF NOT EXISTS idx_indicator_data_symbol_timeframe ON indicators.indicator_data(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_indicator_data_timestamp ON indicators.indicator_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_indicator_quality_symbol ON indicators.indicator_quality(symbol);

CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON monitoring.system_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_health_checks_service_timestamp ON monitoring.health_checks(service_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON monitoring.alerts(status, severity);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trading.trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON trading.positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON ml.models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON config.system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_environment_config_updated_at BEFORE UPDATE ON config.environment_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default configuration
INSERT INTO config.system_config (key, value, description) VALUES
('trading.max_positions', '10', 'Maximum number of open positions'),
('trading.max_daily_loss', '1000', 'Maximum daily loss in USD'),
('trading.max_daily_trades', '50', 'Maximum number of trades per day'),
('ml.model_update_interval', '3600', 'Model update interval in seconds'),
('monitoring.health_check_interval', '30', 'Health check interval in seconds'),
('api.rate_limit', '100', 'API rate limit per minute')
ON CONFLICT (key) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW trading.active_positions AS
SELECT 
    p.*,
    t.symbol,
    t.side,
    t.quantity,
    t.avg_price,
    t.current_price,
    t.unrealized_pnl,
    t.realized_pnl
FROM trading.positions p
JOIN trading.trades t ON p.id = t.position_id
WHERE p.status = 'open';

CREATE OR REPLACE VIEW ml.active_models AS
SELECT 
    m.*,
    tr.status as training_status,
    tr.validation_accuracy,
    tr.test_accuracy
FROM ml.models m
LEFT JOIN ml.training_runs tr ON m.id = tr.model_id
WHERE m.is_active = TRUE;

CREATE OR REPLACE VIEW monitoring.system_health AS
SELECT 
    hc.service_name,
    hc.status,
    hc.response_time_ms,
    hc.timestamp,
    CASE 
        WHEN hc.timestamp > NOW() - INTERVAL '5 minutes' THEN 'recent'
        ELSE 'stale'
    END as data_freshness
FROM monitoring.health_checks hc
WHERE hc.timestamp = (
    SELECT MAX(timestamp) 
    FROM monitoring.health_checks hc2 
    WHERE hc2.service_name = hc.service_name
);

-- Grant permissions
GRANT USAGE ON SCHEMA trading, ml, indicators, config, monitoring TO market7;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading, ml, indicators, config, monitoring TO market7;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA trading, ml, indicators, config, monitoring TO market7;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA trading, ml, indicators, config, monitoring TO market7;