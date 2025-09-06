#!/bin/bash
# MarketPilot Docker Onboarding Script
# Ultra-portable setup using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🐳 $1${NC}"
}

# Check Docker installation
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        log_info "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Docker is available"
}

# Create Docker Compose file for development
create_dev_compose() {
    log_header "Creating Development Docker Compose"
    
    cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # Redis for caching and data storage
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # PostgreSQL for persistent data
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: marketpilot
      POSTGRES_USER: marketpilot
      POSTGRES_PASSWORD: marketpilot_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U marketpilot"]
      interval: 10s
      timeout: 5s
      retries: 5

  # InfluxDB for time series data
  influxdb:
    image: influxdb:2.7-alpine
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: admin123
      DOCKER_INFLUXDB_INIT_ORG: marketpilot
      DOCKER_INFLUXDB_INIT_BUCKET: marketpilot
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MarketPilot Backend
  marketpilot-backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/venv
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - INFLUXDB_HOST=influxdb
      - ENVIRONMENT=development
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
      influxdb:
        condition: service_healthy
    command: >
      sh -c "
        python3 -m venv venv &&
        source venv/bin/activate &&
        pip install --upgrade pip &&
        pip install -r requirements.txt &&
        pip install -r requirements-dev.txt &&
        pre-commit install &&
        python3 test_paper_trading_config.py &&
        uvicorn dashboard_backend.main:app --host 0.0.0.0 --port 8000 --reload
      "

  # MarketPilot Frontend
  marketpilot-frontend:
    build:
      context: ./dashboard_frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./dashboard_frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    command: >
      sh -c "
        npm install &&
        npm start
      "

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  redis_data:
  postgres_data:
  influxdb_data:
  prometheus_data:
  grafana_data:
EOF

    log_success "Development Docker Compose created"
}

# Create development Dockerfile
create_dev_dockerfile() {
    log_header "Creating Development Dockerfile"
    
    cat > Dockerfile.dev << 'EOF'
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data ml dca fork indicators

# Set permissions
RUN chmod +x onboard.sh docker-onboard.sh start_marketpilot.sh stop_marketpilot.sh

# Expose port
EXPOSE 8000

# Default command
CMD ["python3", "standalone_runner.py"]
EOF

    log_success "Development Dockerfile created"
}

# Create production Docker Compose
create_prod_compose() {
    log_header "Creating Production Docker Compose"
    
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-marketpilot}
      POSTGRES_USER: ${POSTGRES_USER:-marketpilot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # InfluxDB
  influxdb:
    image: influxdb:2.7-alpine
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: ${INFLUXDB_USER:-admin}
      DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
      DOCKER_INFLUXDB_INIT_ORG: ${INFLUXDB_ORG:-marketpilot}
      DOCKER_INFLUXDB_INIT_BUCKET: ${INFLUXDB_BUCKET:-marketpilot}
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
    restart: unless-stopped

  # MarketPilot Backend
  marketpilot-backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - INFLUXDB_HOST=influxdb
      - ENVIRONMENT=production
    depends_on:
      - redis
      - postgres
      - influxdb
    restart: unless-stopped

  # MarketPilot Frontend
  marketpilot-frontend:
    build:
      context: ./dashboard_frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=${API_URL:-http://localhost:8000}
    depends_on:
      - marketpilot-backend
    restart: unless-stopped

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
      - ./deploy/ssl:/etc/nginx/ssl
    depends_on:
      - marketpilot-backend
      - marketpilot-frontend
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  influxdb_data:
EOF

    log_success "Production Docker Compose created"
}

# Create production Dockerfile
create_prod_dockerfile() {
    log_header "Creating Production Dockerfile"
    
    cat > Dockerfile.prod << 'EOF'
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 marketpilot && \
    chown -R marketpilot:marketpilot /app

# Switch to non-root user
USER marketpilot

# Create necessary directories
RUN mkdir -p logs data ml dca fork indicators

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python3", "standalone_runner.py"]
EOF

    log_success "Production Dockerfile created"
}

# Create environment files
create_env_files() {
    log_header "Creating Environment Files"
    
    # Development environment
    cat > .env.dev << 'EOF'
# Development Environment
ENVIRONMENT=development
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_DB=marketpilot
POSTGRES_USER=marketpilot
POSTGRES_PASSWORD=marketpilot_dev
INFLUXDB_HOST=influxdb
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=admin123
INFLUXDB_ORG=marketpilot
INFLUXDB_BUCKET=marketpilot
API_URL=http://localhost:8000
LOG_LEVEL=DEBUG
EOF

    # Production environment template
    cat > .env.prod.template << 'EOF'
# Production Environment Template
# Copy this file to .env.prod and fill in your values

ENVIRONMENT=production
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_DB=marketpilot
POSTGRES_USER=marketpilot
POSTGRES_PASSWORD=your_secure_password_here
INFLUXDB_HOST=influxdb
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=your_secure_password_here
INFLUXDB_ORG=marketpilot
INFLUXDB_BUCKET=marketpilot
API_URL=https://your-domain.com
LOG_LEVEL=INFO

# 3Commas API Keys
THREECOMMAS_API_KEY=your_api_key
THREECOMMAS_API_SECRET=your_api_secret
THREECOMMAS_BOT_ID=your_bot_id
THREECOMMAS_BOT_ID2=your_dca_bot_id
THREECOMMAS_EMAIL_TOKEN=your_email_token
THREECOMMAS_ACCOUNT_ID=your_account_id

# Binance API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
EOF

    log_success "Environment files created"
}

# Create startup scripts
create_docker_scripts() {
    log_header "Creating Docker Startup Scripts"
    
    # Development start script
    cat > start-dev.sh << 'EOF'
#!/bin/bash
# Start MarketPilot in Development Mode

echo "🐳 Starting MarketPilot Development Environment..."

# Load development environment
export $(cat .env.dev | xargs)

# Start services
docker-compose -f docker-compose.dev.yml up --build

echo "✅ Development environment started!"
echo "📊 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo "📈 Grafana: http://localhost:3001 (admin/admin)"
echo "🔍 Prometheus: http://localhost:9090"
EOF

    # Production start script
    cat > start-prod.sh << 'EOF'
#!/bin/bash
# Start MarketPilot in Production Mode

echo "🚀 Starting MarketPilot Production Environment..."

# Check if production environment file exists
if [ ! -f ".env.prod" ]; then
    echo "❌ Production environment file not found!"
    echo "Please copy .env.prod.template to .env.prod and configure it."
    exit 1
fi

# Load production environment
export $(cat .env.prod | xargs)

# Start services
docker-compose -f docker-compose.prod.yml up -d --build

echo "✅ Production environment started!"
echo "🌐 Application: http://localhost"
EOF

    # Stop script
    cat > stop-docker.sh << 'EOF'
#!/bin/bash
# Stop MarketPilot Docker Environment

echo "🛑 Stopping MarketPilot..."

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# Stop production environment
docker-compose -f docker-compose.prod.yml down

echo "✅ MarketPilot stopped!"
EOF

    # Clean script
    cat > clean-docker.sh << 'EOF'
#!/bin/bash
# Clean MarketPilot Docker Environment

echo "🧹 Cleaning MarketPilot Docker environment..."

# Stop and remove containers
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.prod.yml down -v

# Remove images
docker rmi marketpilot_marketpilot-backend marketpilot_marketpilot-frontend || true

# Clean up unused resources
docker system prune -f

echo "✅ Docker environment cleaned!"
EOF

    chmod +x start-dev.sh start-prod.sh stop-docker.sh clean-docker.sh

    log_success "Docker startup scripts created"
}

# Main function
main() {
    log_header "MarketPilot Docker Onboarding"
    echo "=================================="
    echo "This script will set up MarketPilot using Docker"
    echo "for maximum portability across any machine."
    echo ""
    
    # Check Docker
    check_docker
    
    # Create Docker configurations
    create_dev_compose
    create_dev_dockerfile
    create_prod_compose
    create_prod_dockerfile
    
    # Create environment files
    create_env_files
    
    # Create startup scripts
    create_docker_scripts
    
    # Final instructions
    log_header "Docker Onboarding Complete! 🎉"
    echo ""
    echo "MarketPilot is now ready to run with Docker!"
    echo ""
    echo "📋 Quick Start:"
    echo "  Development: ./start-dev.sh"
    echo "  Production:  ./start-prod.sh"
    echo "  Stop:        ./stop-docker.sh"
    echo "  Clean:       ./clean-docker.sh"
    echo ""
    echo "🔧 Manual Commands:"
    echo "  Development: docker-compose -f docker-compose.dev.yml up"
    echo "  Production:  docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "📚 Next Steps:"
    echo "1. Copy .env.prod.template to .env.prod and configure"
    echo "2. Update config/paper_cred.json with your credentials"
    echo "3. Start development: ./start-dev.sh"
    echo ""
    echo "🚀 Happy Trading with Docker!"
}

# Run main function
main "$@"
