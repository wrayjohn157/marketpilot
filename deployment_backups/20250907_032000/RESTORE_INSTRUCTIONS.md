# 🔄 MarketPilot Deployment Restoration Guide

## Quick Restore Commands

### 1. Restore Configuration
```bash
cp -r config/ /path/to/marketpilot/
```

### 2. Restore Working Backend
```bash
cp modular_backend.py /path/to/marketpilot/
cp -r dashboard_backend/ /path/to/marketpilot/
```

### 3. Restore Frontend Configuration
```bash
cp setupProxy.js /path/to/marketpilot/dashboard_frontend/src/
cp package.json /path/to/marketpilot/dashboard_frontend/
```

### 4. Restore Component Fixes
```bash
cp frontend_fixes/* /path/to/marketpilot/dashboard_frontend/src/components/ui/
cp frontend_fixes/* /path/to/marketpilot/dashboard_frontend/src/pages/
cp frontend_fixes/index.js /path/to/marketpilot/dashboard_frontend/src/
```

### 5. Verify Deployment
```bash
./verify_deployment.sh
```

## Critical API Keys to Set
- 3Commas Bot ID: 16477920
- 3Commas Email Token: aa5bba08-4875-41bc-91a0-5e0bb66c72b0
- Pair: USDT_BTC

## Essential Endpoints to Test
- http://localhost:8000/health
- http://localhost:8000/api/trades/active
- http://localhost:8000/api/3commas/metrics
- http://localhost:8000/config/dca

## Frontend Integration Checklist
- [ ] setupProxy.js configured
- [ ] No [object Object] errors in console
- [ ] Real deal IDs displaying (not mock)
- [ ] All config pages load/save/reset
- [ ] DCA Strategy Builder functional
