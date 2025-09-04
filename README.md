# Market7 Trading System

A comprehensive trading system with machine learning, DCA strategies, and real-time market analysis.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Redis
- PostgreSQL
- Docker (optional)

### Installation

#### Backend
```bash
# Clone repository
git clone https://github.com/wrayjohn157/market7.git
cd market7

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config/credentials/*.template config/credentials/
# Edit credential files

# Run backend
python3 dashboard_backend/main_fixed.py
```

#### Frontend
```bash
cd dashboard_frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### Docker (Full Stack)
```bash
# Build and run all services
docker-compose -f deploy/docker-compose.yml up -d
```

## 📁 Project Structure

```
market7/
├── dashboard_backend/         # FastAPI backend
├── dashboard_frontend/        # React frontend
├── dca/                       # DCA trading system
├── ml/                        # Machine learning pipeline
├── indicators/                # Technical indicators
├── pipeline/                  # Trading pipeline
├── utils/                     # Shared utilities
├── config/                    # Configuration files
├── deploy/                    # Deployment configurations
└── tests/                     # Test suites
```

## 🏗️ Architecture

### Backend
- **FastAPI**: Modern Python web framework
- **Redis**: Caching and message queues
- **PostgreSQL**: Persistent data storage
- **InfluxDB**: Time-series data (optional)

### Frontend
- **React 18**: Modern React with hooks
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Context API**: State management

### Trading System
- **3Commas API**: Trading execution
- **Binance API**: Market data
- **ML Pipeline**: Predictive models
- **DCA System**: Dollar-cost averaging

## 🔧 Configuration

### Environment Variables
```bash
# Backend
ENVIRONMENT=production
REDIS_HOST=localhost
POSTGRES_HOST=localhost

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=production
```

### Credentials
Configure API credentials in `config/credentials/`:
- `3commas_default.json`
- `binance_default.json`
- `openai_default.json`

## 🚀 Deployment

### Docker Compose
```bash
docker-compose -f deploy/docker-compose.yml up -d
```

### Kubernetes
```bash
kubectl apply -f deploy/kubernetes/
```

### Native Installation
```bash
./deploy/setup.sh
```

## 📊 Features

- **Real-time Trading Dashboard**
- **DCA Strategy Builder**
- **ML Model Monitoring**
- **Technical Indicators**
- **Risk Management**
- **Performance Analytics**

## 🧪 Testing

### Backend Tests
```bash
python3 -m pytest tests/
```

### Frontend Tests
```bash
cd dashboard_frontend
npm test
```

### Integration Tests
```bash
python3 test_backend_frontend_integration.py
```

## 📈 Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus integration
- **Logs**: Centralized logging
- **Alerts**: Error notifications

## 🔒 Security

- **HTTPS**: SSL/TLS encryption
- **Secrets Management**: Encrypted credentials
- **Rate Limiting**: API protection
- **Input Validation**: Data sanitization

## 📚 Documentation

- [Backend API Documentation](docs/api.md)
- [Frontend Component Guide](docs/components.md)
- [Deployment Guide](docs/deployment.md)
- [Architecture Overview](docs/architecture.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/wrayjohn157/market7/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wrayjohn157/market7/discussions)
- **Documentation**: [Project Wiki](https://github.com/wrayjohn157/market7/wiki)

---

**Happy Trading! 🚀**
