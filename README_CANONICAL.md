# MarketPilot Canonical System

## 🚀 Quick Start

The MarketPilot trading system is now fully operational with real 3commas integration.

### **Canonical Commands:**

```bash
# Start the system
./start_canonical.sh

# Check status
./status_canonical.sh

# Stop the system
./stop_canonical.sh
```

### **System Status:**
- ✅ **Backend:** Running on http://localhost:8000
- ✅ **Frontend:** Running on http://localhost:3000
- ✅ **Redis:** Connected and operational
- ✅ **PostgreSQL:** Connected and operational
- ✅ **3commas API:** Live data integration active

## 📊 Real Trading Data

The system is now connected to your live 3commas bot:

- **Bot ID:** 16477920
- **Pair:** USDT_BTC
- **Active Trades:** 2 (BTC and XRP)
- **Current P&L:** -$1.89
- **Total Spent:** $400.92

## 🔗 API Endpoints

| Endpoint | Description | Status |
|----------|-------------|--------|
| `/health` | System health check | ✅ Working |
| `/active-trades` | Real 3commas active deals | ✅ Working |
| `/api/btc/context` | BTC market context with RSI/ADX | ✅ Working |
| `/fork/metrics` | Account summary data | ✅ Working |
| `/3commas/metrics` | Full 3commas trading metrics | ✅ Working |
| `/docs` | Interactive API documentation | ✅ Working |

## 🏗️ Architecture

### **Backend (modular_backend.py)**
- FastAPI-based REST API
- Real 3commas API integration
- Redis caching
- PostgreSQL data storage
- Modular route structure

### **Frontend (React Dashboard)**
- Real-time trading data display
- Account summary with P&L
- Market sentiment indicators
- Active trades monitoring

### **Data Flow**
1. **3commas API** → Real trading data
2. **Backend Processing** → Data normalization and caching
3. **Frontend Display** → Real-time dashboard updates

## 🔧 Configuration

### **3commas Credentials**
Located in `config/paper_cred.json`:
```json
{
  "3commas_api_key": "25f6324914564bed9faddce0a7295b80dba6030f554445a7bbe987a206c7c319",
  "3commas_api_secret": "5ebde1934e3c881d6bcf1bb34307f96a34b2d04fab2da9b9feb725f0a2b6b35761328c9b3ea3abfddf1a666dd98936602fe2e23dbb902cf409185ca2c3cb06c15d33cfb63b08f43cf7096df19c52eee5ee01d19d648ce85141e5becb92503862d4452e32",
  "3commas_bot_id": 16477920,
  "3commas_account_id": 16477920,
  "3commas_email_token": "aa5bba08-4875-41bc-91a0-5e0bb66c72b0",
  "pair": "USDT_BTC"
}
```

## 📈 Features

### **Real-Time Trading Data**
- Live P&L tracking
- Active deals monitoring
- Market sentiment analysis
- BTC price and indicators

### **Modular Backend**
- DCA trading routes
- ML confidence scoring
- Configuration management
- Analytics and simulation
- 3commas integration

### **Production Ready**
- Error handling and logging
- Health monitoring
- Graceful shutdown
- Process management

## 🛠️ Development

### **Available Scripts**
- `onboard.sh` - Full system setup
- `quick-setup.sh` - Minimal setup
- `deploy.sh` - Universal deployment
- `smoke.sh` - Full test suite

### **Code Quality**
- Black formatting
- Ruff linting
- MyPy type checking
- Pytest testing

## 🚨 Troubleshooting

### **Common Issues**

1. **Backend not starting:**
   ```bash
   # Check Redis
   redis-cli ping
   
   # Check Python environment
   source venv/bin/activate
   python3 modular_backend.py
   ```

2. **Frontend not loading:**
   ```bash
   # Check if frontend is running
   ps aux | grep "npm start"
   
   # Restart frontend
   cd dashboard_frontend
   npm start
   ```

3. **API errors:**
   ```bash
   # Check backend logs
   curl http://localhost:8000/health
   
   # Check 3commas connection
   curl http://localhost:8000/3commas/metrics
   ```

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs
- **Code Quality Guide:** CODE_QUALITY_GUIDE.md
- **Deployment Guide:** MINIMAL_SYSTEMD_SETUP.md
- **Paper Trading Setup:** PAPER_TRADING_SETUP.md

## 🎯 Next Steps

1. **Monitor Performance:** Use the dashboard to track trading performance
2. **Configure Alerts:** Set up notifications for important events
3. **Scale Up:** Add more trading pairs and strategies
4. **Production Deploy:** Use the deployment scripts for production

---

**Status:** ✅ **FULLY OPERATIONAL**  
**Last Updated:** September 7, 2025  
**Version:** Canonical v1.0


