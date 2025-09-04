# Market7 Deployment Guide

This guide provides comprehensive deployment options for the Market7 trading system across different environments and platforms.

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Development)
```bash
# Clone the repository
git clone https://github.com/wrayjohn157/market7.git
cd market7

# Copy environment template
cp deploy/.env.template .env

# Edit configuration
nano .env

# Start all services
docker-compose -f deploy/docker-compose.yml up -d

# Check status
docker-compose -f deploy/docker-compose.yml ps

# View logs
docker-compose -f deploy/docker-compose.yml logs -f
```

### Option 2: Native Installation (Recommended for Production)
```bash
# Clone the repository
git clone https://github.com/wrayjohn157/market7.git
cd market7

# Run setup script
chmod +x deploy/setup.sh
./deploy/setup.sh

# Configure credentials
cp config/credentials/*.template config/credentials/
nano config/credentials/*.json

# Start services
sudo systemctl start market7-trading
sudo systemctl status market7-trading
```

### Option 3: Kubernetes (Recommended for Scale)
```bash
# Create namespace
kubectl apply -f deploy/kubernetes/namespace.yaml

# Apply configurations
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.yaml
kubectl apply -f deploy/kubernetes/pvc.yaml

# Deploy services
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml

# Check status
kubectl get pods -n market7
kubectl get services -n market7
```

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+, CentOS 8+, macOS 10.15+, or Windows 10+
- **Python**: 3.8+ (3.11+ recommended)
- **Memory**: 4GB+ RAM (8GB+ recommended)
- **Storage**: 20GB+ free space (100GB+ recommended)
- **Network**: Stable internet connection

### Dependencies
- **Redis**: 6.0+ (for caching and queues)
- **PostgreSQL**: 13+ (for persistent data)
- **InfluxDB**: 2.0+ (for time-series data, optional)

### External Services
- **Binance API**: For market data and trading
- **3Commas API**: For DCA signals
- **OpenAI API**: For ML features (optional)

## 🔧 Configuration

### Environment Variables
Copy `deploy/.env.template` to `.env` and configure:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password

# API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
THREE_COMMAS_API_KEY=your_3commas_api_key
THREE_COMMAS_SECRET_KEY=your_3commas_secret_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

### Credential Files
Configure API credentials in `config/credentials/`:

```bash
# Copy templates
cp config/credentials/*.template config/credentials/

# Edit credentials
nano config/credentials/binance_default.json
nano config/credentials/3commas_default.json
```

## 🐳 Docker Deployment

### Docker Compose
The `docker-compose.yml` includes:
- **Redis**: Caching and queues
- **PostgreSQL**: Persistent data
- **InfluxDB**: Time-series data
- **Trading App**: Main application
- **ML Pipeline**: Machine learning service
- **Indicator Service**: Technical indicators
- **DCA Service**: Dollar-cost averaging
- **Nginx**: Reverse proxy
- **Prometheus**: Monitoring
- **Grafana**: Dashboards

### Custom Docker Image
```bash
# Build custom image
docker build -f deploy/Dockerfile -t market7:latest .

# Run with custom image
docker-compose -f deploy/docker-compose.yml up -d
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- Persistent volume support
- Ingress controller (optional)

### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace market7

# Apply configurations
kubectl apply -f deploy/kubernetes/

# Check deployment
kubectl get all -n market7
```

### Scaling
```bash
# Scale trading app
kubectl scale deployment market7-trading --replicas=3 -n market7

# Scale ML pipeline
kubectl scale deployment market7-ml --replicas=2 -n market7
```

## 🔍 Monitoring & Observability

### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check individual services
curl http://localhost:8001/health  # ML Pipeline
curl http://localhost:8002/health  # Indicators
curl http://localhost:8003/health  # DCA
```

### Logs
```bash
# Docker Compose
docker-compose -f deploy/docker-compose.yml logs -f trading-app

# Kubernetes
kubectl logs -f deployment/market7-trading -n market7

# Systemd
journalctl -u market7-trading -f
```

### Metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Application Metrics**: http://localhost:8000/metrics

## 🛠️ Development Setup

### Local Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
export ENVIRONMENT=development
python3 main_orchestrator.py
```

### Testing
```bash
# Run tests
python3 -m pytest tests/

# Run integration tests
python3 test_integration_workflows.py

# Run with coverage
python3 -m pytest --cov=. tests/
```

## 🔒 Security Considerations

### Production Security
1. **Change default passwords**
2. **Use HTTPS/TLS**
3. **Enable firewall rules**
4. **Regular security updates**
5. **Monitor access logs**
6. **Use secrets management**

### API Security
- Rate limiting enabled
- Input validation
- Authentication required
- Audit logging

## 📊 Performance Tuning

### Resource Limits
```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

### Database Optimization
- Enable connection pooling
- Configure appropriate indexes
- Regular maintenance tasks
- Monitor query performance

### Redis Optimization
- Configure memory limits
- Enable persistence
- Monitor memory usage
- Use appropriate data structures

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose -f deploy/docker-compose.yml logs trading-app

# Check configuration
python3 -c "from config.unified_config_manager import get_config; print(get_config('unified_pipeline_config'))"

# Check dependencies
python3 -c "import redis, pandas, sklearn; print('Dependencies OK')"
```

#### Database Connection Issues
```bash
# Check PostgreSQL
docker-compose -f deploy/docker-compose.yml exec postgres psql -U market7 -d market7

# Check Redis
docker-compose -f deploy/docker-compose.yml exec redis redis-cli ping
```

#### API Connection Issues
```bash
# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/metrics

# Check network connectivity
telnet localhost 8000
```

### Performance Issues
1. **Check resource usage**: `htop`, `docker stats`
2. **Monitor database performance**: Query slow logs
3. **Check Redis memory usage**: `redis-cli info memory`
4. **Review application logs**: Look for errors and warnings

## 📈 Scaling

### Horizontal Scaling
- Add more application replicas
- Use load balancer
- Implement database read replicas
- Cache frequently accessed data

### Vertical Scaling
- Increase CPU and memory
- Optimize database queries
- Use faster storage (SSD)
- Tune application parameters

## 🔄 Updates & Maintenance

### Rolling Updates
```bash
# Docker Compose
docker-compose -f deploy/docker-compose.yml pull
docker-compose -f deploy/docker-compose.yml up -d

# Kubernetes
kubectl rollout restart deployment/market7-trading -n market7
```

### Backup & Recovery
```bash
# Database backup
pg_dump -h localhost -U market7 market7 > backup.sql

# Redis backup
redis-cli --rdb backup.rdb

# Application backup
tar -czf market7-backup.tar.gz logs/ data/ models/ config/
```

## 📞 Support

### Getting Help
1. Check the logs first
2. Review this documentation
3. Check GitHub issues
4. Contact support team

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Trading! 🚀**
