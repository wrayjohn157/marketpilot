# 📡 Market7 API Reference

This document provides comprehensive API documentation for the Market7 trading system.

## 🔗 Base URL

```
http://localhost:8000/api
```

## 🔐 Authentication

### API Key Authentication
```bash
curl -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/trades
```

### JWT Token Authentication
```bash
# Get token
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer your_jwt_token" \
     http://localhost:8000/api/trades
```

## 📊 Response Format

### Success Response
```json
{
  "status": "success",
  "data": {
    "trades": [...],
    "count": 10
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {...}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🏠 System Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "services": {
    "backend": "healthy",
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### System Status
```http
GET /api/status
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "uptime": "2d 5h 30m",
    "version": "2.0.0",
    "environment": "production",
    "services": {
      "database": {
        "status": "healthy",
        "connections": 5,
        "max_connections": 100
      },
      "redis": {
        "status": "healthy",
        "memory_usage": "45MB",
        "keys": 1250
      },
      "trading": {
        "status": "active",
        "active_trades": 3,
        "total_volume": "15000.50"
      }
    }
  }
}
```

### Metrics
```http
GET /api/metrics
```

**Response:**
```
# Prometheus metrics format
http_requests_total{method="GET",endpoint="/api/trades",status="200"} 150
http_request_duration_seconds{method="GET",endpoint="/api/trades"} 0.025
trading_errors_total{error_type="api_error",service="3commas"} 2
```

## 💼 Trading Endpoints

### Get Active Trades
```http
GET /api/trades/active
```

**Query Parameters:**
- `limit` (optional): Number of trades to return (default: 50)
- `offset` (optional): Number of trades to skip (default: 0)
- `symbol` (optional): Filter by trading pair

**Response:**
```json
{
  "status": "success",
  "data": {
    "trades": [
      {
        "id": "trade_123",
        "symbol": "BTCUSDT",
        "side": "buy",
        "amount": "0.001",
        "price": "45000.00",
        "current_price": "45500.00",
        "pnl": "0.50",
        "pnl_percent": "1.11",
        "status": "active",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:30:00Z"
      }
    ],
    "count": 1,
    "total_pnl": "0.50",
    "total_volume": "15000.50"
  }
}
```

### Get Trade History
```http
GET /api/trades/history
```

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `symbol` (optional): Filter by trading pair
- `status` (optional): Filter by trade status
- `limit` (optional): Number of trades to return (default: 100)
- `offset` (optional): Number of trades to skip (default: 0)

**Response:**
```json
{
  "status": "success",
  "data": {
    "trades": [
      {
        "id": "trade_123",
        "symbol": "BTCUSDT",
        "side": "buy",
        "amount": "0.001",
        "entry_price": "45000.00",
        "exit_price": "46000.00",
        "pnl": "1.00",
        "pnl_percent": "2.22",
        "status": "closed",
        "created_at": "2024-01-01T10:00:00Z",
        "closed_at": "2024-01-01T11:00:00Z"
      }
    ],
    "count": 1,
    "total_pnl": "1.00",
    "total_volume": "15000.50"
  }
}
```

### Get Trade Details
```http
GET /api/trades/{trade_id}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "trade_123",
    "symbol": "BTCUSDT",
    "side": "buy",
    "amount": "0.001",
    "entry_price": "45000.00",
    "current_price": "45500.00",
    "pnl": "0.50",
    "pnl_percent": "1.11",
    "status": "active",
    "dca_attempts": 2,
    "dca_success_rate": "100%",
    "risk_level": "low",
    "ml_confidence": 0.85,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:30:00Z",
    "dca_history": [
      {
        "attempt": 1,
        "price": "44800.00",
        "amount": "0.0005",
        "timestamp": "2024-01-01T10:15:00Z",
        "success": true
      }
    ]
  }
}
```

### Create New Trade
```http
POST /api/trades
```

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "amount": "0.001",
  "price": "45000.00",
  "stop_loss": "43000.00",
  "take_profit": "47000.00",
  "dca_enabled": true,
  "max_dca_attempts": 3
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "trade_124",
    "symbol": "BTCUSDT",
    "side": "buy",
    "amount": "0.001",
    "price": "45000.00",
    "status": "active",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

### Close Trade
```http
POST /api/trades/{trade_id}/close
```

**Request Body:**
```json
{
  "reason": "manual_close",
  "force": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "trade_123",
    "status": "closed",
    "exit_price": "45500.00",
    "pnl": "0.50",
    "pnl_percent": "1.11",
    "closed_at": "2024-01-01T11:00:00Z"
  }
}
```

## 🤖 DCA Endpoints

### Get DCA Status
```http
GET /api/dca/status
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "enabled": true,
    "active_trades": 3,
    "total_attempts": 15,
    "successful_attempts": 12,
    "success_rate": "80%",
    "total_volume": "5000.00",
    "average_recovery_time": "2h 30m"
  }
}
```

### Execute DCA
```http
POST /api/dca/execute
```

**Request Body:**
```json
{
  "trade_id": "trade_123",
  "volume": "0.0005",
  "reason": "manual_dca"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "trade_id": "trade_123",
    "dca_attempt": 3,
    "volume": "0.0005",
    "price": "44800.00",
    "timestamp": "2024-01-01T10:15:00Z",
    "success": true
  }
}
```

### Get DCA History
```http
GET /api/dca/history
```

**Query Parameters:**
- `trade_id` (optional): Filter by trade ID
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (optional): Number of records to return (default: 100)

**Response:**
```json
{
  "status": "success",
  "data": {
    "dca_attempts": [
      {
        "id": "dca_456",
        "trade_id": "trade_123",
        "attempt": 1,
        "volume": "0.0005",
        "price": "44800.00",
        "success": true,
        "timestamp": "2024-01-01T10:15:00Z"
      }
    ],
    "count": 1,
    "success_rate": "80%"
  }
}
```

## 🧠 ML Endpoints

### Get ML Predictions
```http
GET /api/ml/predictions
```

**Query Parameters:**
- `symbol` (optional): Filter by trading pair
- `model_type` (optional): Filter by model type
- `limit` (optional): Number of predictions to return (default: 50)

**Response:**
```json
{
  "status": "success",
  "data": {
    "predictions": [
      {
        "id": "pred_789",
        "symbol": "BTCUSDT",
        "model_type": "safu_exit",
        "prediction": 0.85,
        "confidence": 0.92,
        "features": {
          "rsi": 45.2,
          "macd": 0.15,
          "bollinger_position": 0.3
        },
        "timestamp": "2024-01-01T10:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### Get ML Performance
```http
GET /api/ml/performance
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "models": [
      {
        "name": "safu_exit",
        "type": "binary_classification",
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85,
        "last_trained": "2024-01-01T08:00:00Z",
        "training_samples": 10000,
        "status": "active"
      }
    ],
    "overall_performance": {
      "average_accuracy": 0.83,
      "total_predictions": 50000,
      "successful_predictions": 41500
    }
  }
}
```

### Retrain Model
```http
POST /api/ml/retrain
```

**Request Body:**
```json
{
  "model_type": "safu_exit",
  "force": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "model_type": "safu_exit",
    "training_started": "2024-01-01T10:00:00Z",
    "estimated_duration": "30m",
    "status": "training"
  }
}
```

## 📊 Analytics Endpoints

### Get Performance Metrics
```http
GET /api/analytics/performance
```

**Query Parameters:**
- `period` (optional): Time period (1d, 7d, 30d, 90d, 1y, all)
- `symbol` (optional): Filter by trading pair

**Response:**
```json
{
  "status": "success",
  "data": {
    "period": "30d",
    "metrics": {
      "total_return": 0.15,
      "total_return_percent": "15%",
      "sharpe_ratio": 1.25,
      "max_drawdown": 0.05,
      "max_drawdown_percent": "5%",
      "win_rate": 0.68,
      "average_win": 0.02,
      "average_loss": -0.01,
      "profit_factor": 1.36,
      "total_trades": 150,
      "winning_trades": 102,
      "losing_trades": 48
    },
    "daily_returns": [
      {
        "date": "2024-01-01",
        "return": 0.01,
        "return_percent": "1%"
      }
    ]
  }
}
```

### Get Risk Metrics
```http
GET /api/analytics/risk
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "portfolio_risk": "medium",
    "var_95": 0.03,
    "var_99": 0.05,
    "beta": 1.2,
    "correlation_matrix": {
      "BTCUSDT": {
        "ETHUSDT": 0.85,
        "ADAUSDT": 0.65
      }
    },
    "concentration_risk": 0.15,
    "liquidity_risk": "low"
  }
}
```

### Get Market Data
```http
GET /api/analytics/market
```

**Query Parameters:**
- `symbol` (required): Trading pair
- `timeframe` (optional): Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (optional): Number of candles to return (default: 100)

**Response:**
```json
{
  "status": "success",
  "data": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "candles": [
      {
        "timestamp": "2024-01-01T10:00:00Z",
        "open": "45000.00",
        "high": "45500.00",
        "low": "44800.00",
        "close": "45200.00",
        "volume": "100.50"
      }
    ],
    "indicators": {
      "rsi": 45.2,
      "macd": 0.15,
      "bollinger_upper": "46000.00",
      "bollinger_lower": "44000.00",
      "bollinger_middle": "45000.00"
    }
  }
}
```

## 🔧 Configuration Endpoints

### Get Configuration
```http
GET /api/config
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "trading": {
      "enabled": true,
      "max_position_size": "1000.00",
      "daily_loss_limit": "100.00",
      "max_drawdown": "0.10"
    },
    "dca": {
      "enabled": true,
      "max_attempts": 5,
      "base_volume": "100.00",
      "volume_scaling": 1.5
    },
    "ml": {
      "enabled": true,
      "confidence_threshold": 0.8,
      "update_frequency": "1h"
    },
    "risk": {
      "safu_enabled": true,
      "stop_loss": "0.05",
      "take_profit": "0.10"
    }
  }
}
```

### Update Configuration
```http
PUT /api/config
```

**Request Body:**
```json
{
  "trading": {
    "max_position_size": "2000.00",
    "daily_loss_limit": "200.00"
  },
  "dca": {
    "max_attempts": 7,
    "base_volume": "150.00"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "message": "Configuration updated successfully",
    "updated_fields": [
      "trading.max_position_size",
      "trading.daily_loss_limit",
      "dca.max_attempts",
      "dca.base_volume"
    ]
  }
}
```

## 📈 External API Endpoints

### 3Commas API Health
```http
GET /api/3commas/health
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "connected": true,
    "account_id": "12345",
    "balance": "10000.00",
    "active_bots": 3,
    "last_sync": "2024-01-01T10:00:00Z"
  }
}
```

### Binance API Health
```http
GET /api/binance/health
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "connected": true,
    "account_type": "spot",
    "balance": "5000.00",
    "trading_enabled": true,
    "last_sync": "2024-01-01T10:00:00Z"
  }
}
```

### Sync External Data
```http
POST /api/sync
```

**Request Body:**
```json
{
  "source": "3commas",
  "force": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "source": "3commas",
    "sync_started": "2024-01-01T10:00:00Z",
    "estimated_duration": "5m",
    "status": "syncing"
  }
}
```

## 📊 Metrics Endpoints

### Trading Metrics
```http
GET /api/metrics/trading
```

**Response:**
```
# Prometheus metrics format
trading_errors_total{error_type="api_error",service="3commas"} 2
dca_failed_attempts_total{reason="insufficient_balance"} 1
dca_successful_attempts_total 15
active_trades_total 3
trading_volume_usd 15000.50
```

### ML Metrics
```http
GET /api/metrics/ml
```

**Response:**
```
# Prometheus metrics format
ml_predictions_total{model_type="safu_exit",status="success"} 1000
ml_model_accuracy{model_type="safu_exit"} 0.85
ml_training_duration_seconds{model_type="safu_exit"} 1800
```

### System Metrics
```http
GET /api/metrics/system
```

**Response:**
```
# Prometheus metrics format
memory_usage_bytes 1073741824
cpu_usage_percent 45.2
disk_usage_bytes 5368709120
```

## 🚨 Error Codes

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Codes
- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_ERROR` - Authentication failed
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMITED` - Rate limit exceeded
- `EXTERNAL_API_ERROR` - External API error
- `TRADING_DISABLED` - Trading is disabled
- `INSUFFICIENT_BALANCE` - Insufficient balance
- `INVALID_SYMBOL` - Invalid trading pair
- `TRADE_NOT_FOUND` - Trade not found
- `DCA_DISABLED` - DCA is disabled
- `ML_MODEL_ERROR` - ML model error
- `CONFIGURATION_ERROR` - Configuration error

## 📝 Rate Limits

### Default Limits
- **General API**: 1000 requests per hour
- **Trading API**: 100 requests per hour
- **ML API**: 500 requests per hour
- **Analytics API**: 200 requests per hour

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🔒 Security

### API Key Security
- Store API keys securely
- Use environment variables
- Rotate keys regularly
- Monitor key usage

### Request Security
- Use HTTPS in production
- Validate all inputs
- Sanitize user data
- Log security events

### Response Security
- Don't expose sensitive data
- Use appropriate HTTP status codes
- Implement proper error handling
- Add security headers

---

**API Documentation Complete! 📡**

For more information, check the interactive API documentation at http://localhost:8000/docs