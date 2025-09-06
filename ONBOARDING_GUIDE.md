# 🚀 MarketPilot Onboarding Guide

## **QUICK START - Choose Your Setup Method**

### **Method 1: Docker (Recommended for Portability)**
```bash
# One command setup
./docker-onboard.sh

# Start development
./start-dev.sh
```

### **Method 2: Native Installation**
```bash
# One command setup
./onboard.sh

# Start MarketPilot
./start_marketpilot.sh
```

---

## 📋 **OVERVIEW**

MarketPilot is designed to be **100% portable** and ready to run on any machine with minimal setup. This guide provides multiple onboarding methods to suit different environments and preferences.

---

## 🐳 **DOCKER SETUP (Recommended)**

### **Why Docker?**
- ✅ **Zero dependency conflicts** - Everything runs in containers
- ✅ **Identical environment** - Works the same on any machine
- ✅ **Easy cleanup** - Remove everything with one command
- ✅ **Production ready** - Same setup for dev and production
- ✅ **No system pollution** - Doesn't install anything on your machine

### **Quick Start with Docker**
```bash
# 1. Clone the repository
git clone https://github.com/wrayjohn157/marketpilot.git
cd marketpilot

# 2. Run Docker onboarding
./docker-onboard.sh

# 3. Start development environment
./start-dev.sh
```

### **Docker Commands**
```bash
# Development (with hot reload)
./start-dev.sh

# Production
./start-prod.sh

# Stop everything
./stop-docker.sh

# Clean up (removes all data)
./clean-docker.sh
```

### **Docker Services**
- **Backend API**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:3000
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432
- **InfluxDB**: localhost:8086

---

## 🖥️ **NATIVE INSTALLATION**

### **Supported Operating Systems**
- ✅ **Ubuntu/Debian** (apt package manager)
- ✅ **RHEL/CentOS/Fedora** (yum/dnf package manager)
- ✅ **macOS** (Homebrew)
- ⚠️ **Windows** (WSL2 recommended)

### **Quick Start with Native Installation**
```bash
# 1. Clone the repository
git clone https://github.com/wrayjohn157/marketpilot.git
cd marketpilot

# 2. Run native onboarding
./onboard.sh

# 3. Start MarketPilot
./start_marketpilot.sh
```

### **What Gets Installed**
- **Python 3.12+** with virtual environment
- **Redis** for caching and data storage
- **PostgreSQL** for persistent data
- **Node.js & npm** for frontend development
- **Docker** for containerization
- **Development tools** (pytest, black, mypy, etc.)

---

## ⚙️ **CONFIGURATION**

### **1. Environment Variables**
```bash
# Copy and customize environment file
cp .env.prod.template .env.prod

# Edit with your values
nano .env.prod
```

### **2. 3Commas API Credentials**
```bash
# Update paper trading credentials
nano config/paper_cred.json
```

### **3. Database Configuration**
```bash
# Development (Docker)
POSTGRES_HOST=postgres
REDIS_HOST=redis

# Production
POSTGRES_HOST=your-db-host
REDIS_HOST=your-redis-host
```

---

## 🧪 **TESTING YOUR SETUP**

### **Quick Health Check**
```bash
# Test basic functionality
python3 test_paper_trading_config.py

# Run syntax check
make check-syntax

# Run quick smoke test
make quick-smoke
```

### **Full Test Suite**
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run CI checks
make ci-fast
```

---

## 🚀 **RUNNING MARKETPILOT**

### **Development Mode**
```bash
# Start all services
./start_marketpilot.sh all

# Start specific services
./start_marketpilot.sh data    # Data collection
./start_marketpilot.sh fork    # Fork detection
./start_marketpilot.sh dca     # DCA services
./start_marketpilot.sh dashboard # Web dashboard
```

### **Production Mode**
```bash
# Docker production
./start-prod.sh

# Native production
make ci-full && ./start_marketpilot.sh all
```

### **Stopping Services**
```bash
# Stop all services
./stop_marketpilot.sh

# Docker stop
./stop-docker.sh
```

---

## 🔧 **DEVELOPMENT WORKFLOW**

### **Daily Development**
```bash
# Before starting work
make quick-smoke

# Before committing
make ci-fast

# Before pushing
make ci-full
```

### **Code Quality**
```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type

# Fix syntax issues
make fix-syntax
```

### **Testing**
```bash
# Run specific tests
make test-smoke
make test-unit
make test-integration

# Run with coverage
make test-coverage
```

---

## 📊 **MONITORING & LOGS**

### **Service Status**
```bash
# Check system health
make health

# View logs
tail -f logs/*.log

# Docker logs
docker-compose -f docker-compose.dev.yml logs -f
```

### **Monitoring Dashboards**
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application**: http://localhost:8000

---

## 🛠️ **TROUBLESHOOTING**

### **Common Issues**

#### **1. Permission Denied**
```bash
# Fix script permissions
chmod +x *.sh

# Fix directory permissions
sudo chown -R $USER:$USER .
```

#### **2. Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8000

# Kill the process
sudo kill -9 <PID>
```

#### **3. Docker Issues**
```bash
# Restart Docker
sudo systemctl restart docker

# Clean up Docker
./clean-docker.sh
```

#### **4. Python Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **5. Database Connection Issues**
```bash
# Check Redis
redis-cli ping

# Check PostgreSQL
psql -h localhost -U marketpilot -d marketpilot
```

### **Getting Help**
```bash
# Show all available commands
make help

# Check system health
make health

# View logs
tail -f logs/*.log
```

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation**
- **Code Quality Guide**: `CODE_QUALITY_GUIDE.md`
- **Minimal Systemd Setup**: `MINIMAL_SYSTEMD_SETUP.md`
- **Paper Trading Setup**: `PAPER_TRADING_SETUP.md`
- **Architecture Overview**: `ARCHITECTURE.md`

### **Configuration Files**
- **Environment**: `.env.dev`, `.env.prod.template`
- **Docker**: `docker-compose.dev.yml`, `docker-compose.prod.yml`
- **Python**: `requirements.txt`, `requirements-dev.txt`
- **Frontend**: `dashboard_frontend/package.json`

### **Scripts**
- **Onboarding**: `onboard.sh`, `docker-onboard.sh`
- **Startup**: `start_marketpilot.sh`, `start-dev.sh`, `start-prod.sh`
- **Testing**: `quick_smoke.sh`, `smoke.sh`, `run_tests.sh`

---

## 🎯 **NEXT STEPS AFTER ONBOARDING**

### **1. Configure API Keys**
```bash
# Update 3Commas credentials
nano config/paper_cred.json

# Update environment variables
nano .env.prod
```

### **2. Test the System**
```bash
# Run paper trading test
python3 test_paper_trading_config.py

# Start data collection
./start_marketpilot.sh data
```

### **3. Access the Dashboard**
```bash
# Start dashboard
./start_marketpilot.sh dashboard

# Open in browser
open http://localhost:8000
```

### **4. Monitor Performance**
```bash
# Check logs
tail -f logs/*.log

# View metrics
open http://localhost:3001
```

---

## 🚀 **PRODUCTION DEPLOYMENT**

### **Docker Production**
```bash
# Configure production environment
cp .env.prod.template .env.prod
nano .env.prod

# Start production
./start-prod.sh
```

### **Cloud Deployment**
- **AWS**: Use ECS or EKS with the provided Docker configurations
- **Google Cloud**: Use Cloud Run or GKE
- **Azure**: Use Container Instances or AKS
- **DigitalOcean**: Use App Platform or Droplets

### **Monitoring in Production**
- **Grafana**: Custom dashboards for trading metrics
- **Prometheus**: System and application metrics
- **Sentry**: Error tracking and alerting
- **Logs**: Centralized logging with structured logs

---

## 🎉 **SUCCESS!**

You now have MarketPilot running on your machine! The system is designed to be:

- ✅ **Portable** - Works on any machine
- ✅ **Scalable** - From development to production
- ✅ **Maintainable** - Comprehensive testing and quality tools
- ✅ **Monitorable** - Full observability and logging
- ✅ **Secure** - Best practices for API key management

**Happy Trading! 🚀📈**
