# MarketPilot VPS Migration Guide

## 🚀 One-Click Deployment

### Option 1: Complete Automated Setup
```bash
# Clone repository
git clone <your-repo-url> marketpilot
cd marketpilot

# Run one-click deployment (handles everything!)
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Step-by-Step

#### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
chmod +x install_dependencies.sh
./install_dependencies.sh

# Log out and back in for Docker group changes
```

#### 2. Project Setup
```bash
# Clone repository
git clone <your-repo-url> marketpilot
cd marketpilot

# Clean up unnecessary files
chmod +x cleanup_for_migration.sh
./cleanup_for_migration.sh

# Activate virtual environment
source venv/bin/activate
```

#### 3. Configuration
```bash
# Create credentials directory
mkdir -p config/credentials

# Copy your credentials (DO NOT COMMIT THESE!)
# See config/credentials/README.md for format
```

#### 4. Start Services
```bash
# Start Redis
sudo systemctl start redis-server

# Start backend
python3 modular_dashboard_api.py

# Start frontend (in another terminal)
cd dashboard_frontend
npm install
npm run build
docker run -d -p 3001:80 -v $(pwd)/build:/usr/share/nginx/html nginx
```

## Critical Files to Keep
- `modular_dashboard_api.py` - Main API server
- `routes/` - All API route modules
- `dashboard_frontend/` - React frontend
- `config/` - Configuration files
- `install_dependencies.sh` - Dependency installer
- `cleanup_for_migration.sh` - Cleanup script
- `.pre-commit-config.yaml` - Code quality hooks

## Files to Remove (handled by cleanup script)
- All `test_*.py` files
- All `fix_*.py` files
- All `*_fix.py` files
- Temporary and backup files
- Old main files

## Environment Variables
Set these on the new VPS:
- `REACT_APP_API_URL=http://YOUR_NEW_IP:3001`
- Update API URLs in frontend config

## Ports
- Frontend: 3001 (Nginx proxy)
- Backend: 8001 (Direct access)
- Redis: 6379
