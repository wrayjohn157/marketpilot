"""
Prometheus metrics for Market7 backend
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
import time
import logging

logger = logging.getLogger(__name__)

# Create a custom registry
registry = CollectorRegistry()

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# Trading metrics
trading_errors_total = Counter(
    'trading_errors_total',
    'Total trading errors',
    ['error_type', 'service'],
    registry=registry
)

dca_failed_attempts_total = Counter(
    'dca_failed_attempts_total',
    'Total DCA failed attempts',
    ['reason'],
    registry=registry
)

dca_successful_attempts_total = Counter(
    'dca_successful_attempts_total',
    'Total DCA successful attempts',
    registry=registry
)

active_trades_gauge = Gauge(
    'active_trades_total',
    'Number of active trades',
    registry=registry
)

trading_volume_gauge = Gauge(
    'trading_volume_usd',
    'Trading volume in USD',
    registry=registry
)

# ML metrics
ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model_type', 'status'],
    registry=registry
)

ml_model_accuracy_gauge = Gauge(
    'ml_model_accuracy',
    'ML model accuracy',
    ['model_type'],
    registry=registry
)

ml_training_duration_seconds = Summary(
    'ml_training_duration_seconds',
    'ML training duration in seconds',
    ['model_type'],
    registry=registry
)

# API metrics
threecommas_api_errors_total = Counter(
    'threecommas_api_errors_total',
    'Total 3Commas API errors',
    ['error_type'],
    registry=registry
)

threecommas_api_requests_total = Counter(
    'threecommas_api_requests_total',
    'Total 3Commas API requests',
    ['endpoint', 'status'],
    registry=registry
)

binance_api_errors_total = Counter(
    'binance_api_errors_total',
    'Total Binance API errors',
    ['error_type'],
    registry=registry
)

binance_api_requests_total = Counter(
    'binance_api_requests_total',
    'Total Binance API requests',
    ['endpoint', 'status'],
    registry=registry
)

# Redis metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=registry
)

redis_connection_errors_total = Counter(
    'redis_connection_errors_total',
    'Total Redis connection errors',
    registry=registry
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'status'],
    registry=registry
)

db_connection_errors_total = Counter(
    'db_connection_errors_total',
    'Total database connection errors',
    registry=registry
)

# System metrics
memory_usage_gauge = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

cpu_usage_gauge = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

# Custom metrics for Market7 specific features
fork_score_gauge = Gauge(
    'fork_score',
    'Current fork score',
    ['symbol'],
    registry=registry
)

btc_sentiment_gauge = Gauge(
    'btc_sentiment_score',
    'BTC sentiment score',
    registry=registry
)

market_volatility_gauge = Gauge(
    'market_volatility',
    'Market volatility index',
    registry=registry
)

def get_metrics():
    """Return Prometheus metrics in the correct format"""
    return generate_latest(registry)

def update_system_metrics():
    """Update system metrics"""
    try:
        import psutil
        
        # Update memory usage
        memory_info = psutil.virtual_memory()
        memory_usage_gauge.set(memory_info.used)
        
        # Update CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage_gauge.set(cpu_percent)
        
    except ImportError:
        logger.warning("psutil not available, system metrics not updated")
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def record_http_request(method, endpoint, status_code, duration):
    """Record HTTP request metrics"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code)
    ).inc()
    
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

def record_trading_error(error_type, service):
    """Record trading error"""
    trading_errors_total.labels(
        error_type=error_type,
        service=service
    ).inc()

def record_dca_attempt(success, reason=None):
    """Record DCA attempt"""
    if success:
        dca_successful_attempts_total.inc()
    else:
        dca_failed_attempts_total.labels(reason=reason or 'unknown').inc()

def record_ml_prediction(model_type, success):
    """Record ML prediction"""
    status = 'success' if success else 'error'
    ml_predictions_total.labels(
        model_type=model_type,
        status=status
    ).inc()

def update_ml_model_accuracy(model_type, accuracy):
    """Update ML model accuracy"""
    ml_model_accuracy_gauge.labels(model_type=model_type).set(accuracy)

def record_api_request(api_name, endpoint, status_code, is_error=False):
    """Record API request"""
    if api_name == '3commas':
        threecommas_api_requests_total.labels(
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        if is_error:
            threecommas_api_errors_total.labels(error_type='api_error').inc()
    elif api_name == 'binance':
        binance_api_requests_total.labels(
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        if is_error:
            binance_api_errors_total.labels(error_type='api_error').inc()

def record_redis_operation(operation, success):
    """Record Redis operation"""
    status = 'success' if success else 'error'
    redis_operations_total.labels(
        operation=operation,
        status=status
    ).inc()

def record_redis_connection_error():
    """Record Redis connection error"""
    redis_connection_errors_total.inc()

def record_db_query(query_type, success):
    """Record database query"""
    status = 'success' if success else 'error'
    db_queries_total.labels(
        query_type=query_type,
        status=status
    ).inc()

def record_db_connection_error():
    """Record database connection error"""
    db_connection_errors_total.inc()

def update_fork_score(symbol, score):
    """Update fork score for a symbol"""
    fork_score_gauge.labels(symbol=symbol).set(score)

def update_btc_sentiment(score):
    """Update BTC sentiment score"""
    btc_sentiment_gauge.set(score)

def update_market_volatility(volatility):
    """Update market volatility"""
    market_volatility_gauge.set(volatility)

def update_active_trades(count):
    """Update active trades count"""
    active_trades_gauge.set(count)

def update_trading_volume(volume_usd):
    """Update trading volume in USD"""
    trading_volume_gauge.set(volume_usd)