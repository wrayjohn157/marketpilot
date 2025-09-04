# 🚀 Market7 Installation Guide

This guide will walk you through installing and setting up the Market7 trading system on your machine.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: At least 10GB free space
- **CPU**: 2+ cores recommended
- **Internet**: Stable internet connection for API access

### Required Software
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: For cloning the repository
- **Python**: 3.11+ (for development)

### Optional Software
- **VS Code**: Recommended code editor
- **Postman**: For API testing
- **pgAdmin**: For database management

## 🔧 Installation Methods

### Method 1: Quick Start (Recommended)

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/market7.git
cd market7
```

#### 2. Run the Setup Script
```bash
chmod +x deploy.sh
./deploy.sh
```

#### 3. Access the System
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **Monitoring**: http://localhost:3001

### Method 2: Manual Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/market7.git
cd market7
```

#### 2. Create Environment File
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Start Services
```bash
# Start core services
docker-compose up -d

# Start monitoring (optional)
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

#### 4. Initialize Database
```bash
docker-compose exec backend python -c "from utils.database import init_db; init_db()"
```

### Method 3: Development Installation

#### 1. Clone and Setup
```bash
git clone https://github.com/your-username/market7.git
cd market7
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Start Services
```bash
# Start database and Redis
docker-compose up -d postgres redis

# Start backend
python dashboard_backend/main.py

# Start frontend (in another terminal)
cd dashboard_frontend
npm install
npm start
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the root directory:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=market7
POSTGRES_USER=market7

# Redis Configuration
REDIS_PASSWORD=your_redis_password

# API Keys (Optional for testing)
THREECOMMAS_API_KEY=your_3commas_api_key
THREECOMMAS_API_SECRET=your_3commas_api_secret
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Monitoring (Optional)
GRAFANA_ADMIN_PASSWORD=your_grafana_password
SMTP_PASSWORD=your_smtp_password
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Domain (for remote access)
DOMAIN=your-domain.com
```

### 2. API Keys Setup

#### 3Commas API
1. Go to [3Commas](https://3commas.io/)
2. Navigate to API settings
3. Create a new API key
4. Copy the API key and secret
5. Add to your `.env` file

#### Binance API
1. Go to [Binance](https://www.binance.com/)
2. Navigate to API Management
3. Create a new API key
4. Enable "Enable Trading" and "Enable Futures"
5. Copy the API key and secret
6. Add to your `.env` file

### 3. Credential Files

#### 3Commas Credentials
```bash
# Create credentials directory
mkdir -p config/credentials

# Create 3Commas credentials file
cat > config/credentials/3commas_default.json << EOF
{
  "api_key": "your_3commas_api_key",
  "api_secret": "your_3commas_api_secret",
  "account_id": "your_account_id"
}
EOF
```

#### Binance Credentials
```bash
# Create Binance credentials file
cat > config/credentials/binance_default.json << EOF
{
  "api_key": "your_binance_api_key",
  "api_secret": "your_binance_api_secret"
}
EOF
```

## 🔍 Verification

### 1. Check Services Status
```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### 2. Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test 3Commas connection
curl http://localhost:8000/api/3commas/health

# Test Binance connection
curl http://localhost:8000/api/binance/health
```

### 3. Test Frontend
```bash
# Open browser and navigate to
http://localhost:3000

# Check for any console errors
# Open browser developer tools (F12)
```

### 4. Test Monitoring (if enabled)
```bash
# Check Grafana
curl http://localhost:3001/api/health

# Check Prometheus
curl http://localhost:9090/-/healthy

# Run monitoring test
python3 monitoring/test_monitoring.py
```

## 🐛 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Check Docker status
docker --version
docker-compose --version

# Restart Docker service
sudo systemctl restart docker

# Clean up Docker
docker system prune -a
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000

# Kill processes using ports
sudo kill -9 $(sudo lsof -t -i:3000)
sudo kill -9 $(sudo lsof -t -i:8000)
```

#### Database Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Redis Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### Frontend Issues
```bash
# Rebuild frontend
cd dashboard_frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Log Analysis

#### View All Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Log Files
```bash
# Application logs
tail -f logs/application.log

# Error logs
tail -f logs/error.log

# Access logs
tail -f logs/access.log
```

### Performance Issues

#### Resource Usage
```bash
# Check resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

#### Optimization
```bash
# Increase Docker memory limit
# Edit docker-compose.yml
# Add memory limits to services

# Optimize database
docker-compose exec postgres psql -U market7 -d market7 -c "VACUUM ANALYZE;"
```

## 🔄 Updates

### Updating Market7
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Update monitoring (if enabled)
cd monitoring
docker-compose -f docker-compose.monitoring.yml down
docker-compose -f docker-compose.monitoring.yml up -d --build
```

### Backup Before Update
```bash
# Backup database
docker-compose exec postgres pg_dump -U market7 market7 > backup.sql

# Backup configuration
tar -czf config_backup.tar.gz config/

# Backup data
tar -czf data_backup.tar.gz data/
```

## 🚀 Production Deployment

### Production Checklist
- [ ] Change all default passwords
- [ ] Configure SSL certificates
- [ ] Set up proper firewall rules
- [ ] Configure monitoring and alerts
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Test disaster recovery procedures

### Security Hardening
```bash
# Change default passwords
# Update .env file with strong passwords

# Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Update system
sudo apt update && sudo apt upgrade -y
```

### Monitoring Setup
```bash
# Start monitoring stack
cd monitoring
./setup_monitoring.sh

# Configure alerts
# Edit monitoring/alertmanager/alertmanager.yml
# Add your email/Slack webhook
```

## 📞 Support

### Getting Help
- **Documentation**: Check this guide and other docs
- **GitHub Issues**: Report bugs and request features
- **Community**: Join our Discord/Telegram
- **Email**: support@market7.local

### Useful Commands
```bash
# System status
docker-compose ps

# Service logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Update system
git pull && docker-compose up -d --build

# Clean up
docker system prune -a
```

---

**Installation complete! 🎉**

Your Market7 trading system should now be running. Access the dashboard at http://localhost:3000 to get started!
