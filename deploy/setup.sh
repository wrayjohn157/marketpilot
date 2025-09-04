#!/bin/bash
"""
Market7 Deployment Setup Script
Supports: Ubuntu/Debian, CentOS/RHEL, macOS, Docker
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
PROJECT_NAME="market7"
VENV_NAME="venv"
LOG_FILE="setup.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a $LOG_FILE
    exit 1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
    log "Detected OS: $OS"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [[ $(echo "$PYTHON_VER >= 3.8" | bc -l) -eq 1 ]]; then
            success "Python $PYTHON_VER found"
        else
            error "Python 3.8+ required, found $PYTHON_VER"
        fi
    else
        error "Python3 not found. Please install Python 3.8+"
    fi

    # Check available memory
    if [[ "$OS" == "linux" ]]; then
        MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
        if [ $MEMORY_GB -lt 2 ]; then
            warning "Low memory detected: ${MEMORY_GB}GB. Recommended: 4GB+"
        else
            success "Memory: ${MEMORY_GB}GB"
        fi
    fi

    # Check disk space
    DISK_SPACE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ $DISK_SPACE -lt 5 ]; then
        warning "Low disk space: ${DISK_SPACE}GB. Recommended: 10GB+"
    else
        success "Disk space: ${DISK_SPACE}GB"
    fi
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."

    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                python3-venv \
                python3-pip \
                python3-dev \
                build-essential \
                redis-server \
                postgresql-client \
                curl \
                wget \
                git \
                bc
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y \
                python3 \
                python3-pip \
                python3-devel \
                gcc \
                gcc-c++ \
                redis \
                postgresql \
                curl \
                wget \
                git \
                bc
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                error "Homebrew not found. Please install Homebrew first: https://brew.sh"
            fi
            brew install python@3.11 redis postgresql curl wget git
            ;;
        *)
            warning "Unknown OS. Please install dependencies manually."
            ;;
    esac

    success "System dependencies installed"
}

# Create virtual environment
create_venv() {
    log "Creating Python virtual environment..."

    if [ -d "$VENV_NAME" ]; then
        warning "Virtual environment already exists. Removing..."
        rm -rf $VENV_NAME
    fi

    python3 -m venv $VENV_NAME
    source $VENV_NAME/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    success "Virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."

    source $VENV_NAME/bin/activate

    # Install from requirements.txt
    pip install -r requirements.txt

    # Install additional production dependencies
    pip install \
        gunicorn \
        supervisor \
        psutil \
        prometheus-client \
        sentry-sdk

    success "Python dependencies installed"
}

# Setup configuration
setup_config() {
    log "Setting up configuration..."

    # Create environment-specific configs
    mkdir -p config/environments

    # Create development config
    cat > config/environments/development.yaml << EOF
environment: development
debug: true
log_level: DEBUG
redis:
  host: localhost
  port: 6379
  db: 0
database:
  host: localhost
  port: 5432
  name: market7_dev
api:
  rate_limit: 1000
  timeout: 30
EOF

    # Create production config
    cat > config/environments/production.yaml << EOF
environment: production
debug: false
log_level: INFO
redis:
  host: localhost
  port: 6379
  db: 0
database:
  host: localhost
  port: 5432
  name: market7_prod
api:
  rate_limit: 100
  timeout: 60
EOF

    # Create staging config
    cat > config/environments/staging.yaml << EOF
environment: staging
debug: false
log_level: INFO
redis:
  host: localhost
  port: 6379
  db: 1
database:
  host: localhost
  port: 5432
  name: market7_staging
api:
  rate_limit: 500
  timeout: 45
EOF

    success "Configuration files created"
}

# Setup directories
setup_directories() {
    log "Setting up project directories..."

    # Create necessary directories
    mkdir -p {logs,data,models,cache,backups,output}
    mkdir -p logs/{trading,ml,indicators,dca}
    mkdir -p data/{historical,realtime,backtest}
    mkdir -p models/{safu,recovery,confidence,dca_spend,trade_success}
    mkdir -p cache/{indicators,ml,redis}
    mkdir -p backups/{config,models,data}
    mkdir -p output/{trades,reports,logs}

    # Set permissions
    chmod 755 logs data models cache backups output
    chmod 755 logs/* data/* models/* cache/* backups/* output/*

    success "Project directories created"
}

# Setup services
setup_services() {
    log "Setting up system services..."

    # Create systemd service files
    sudo tee /etc/systemd/system/market7-trading.service > /dev/null << EOF
[Unit]
Description=Market7 Trading System
After=network.target redis.service postgresql.service
Requires=redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/$VENV_NAME/bin
ExecStart=$(pwd)/$VENV_NAME/bin/python main_orchestrator.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Create Redis service if not exists
    if ! systemctl is-active --quiet redis; then
        sudo systemctl enable redis
        sudo systemctl start redis
    fi

    # Reload systemd
    sudo systemctl daemon-reload

    success "System services configured"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."

    # Create health check script
    cat > health_check.py << 'EOF'
#!/usr/bin/env python3
import sys
import json
from datetime import datetime
from utils.redis_manager import get_redis_manager
from config.unified_config_manager import get_config

def health_check():
    try:
        # Check Redis
        redis_manager = get_redis_manager()
        redis_healthy = redis_manager.ping()

        # Check config
        config_healthy = True
        try:
            get_config("unified_pipeline_config")
        except:
            config_healthy = False

        status = "healthy" if redis_healthy and config_healthy else "unhealthy"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": redis_healthy,
                "config": config_healthy
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    result = health_check()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "healthy" else 1)
EOF

    chmod +x health_check.py

    success "Monitoring setup complete"
}

# Validate installation
validate_installation() {
    log "Validating installation..."

    source $VENV_NAME/bin/activate

    # Test imports
    python3 -c "
import sys
try:
    from config.unified_config_manager import get_config
    from utils.redis_manager import get_redis_manager
    from main_orchestrator import MainOrchestrator
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

    # Test configuration
    python3 -c "
from config.unified_config_manager import get_config
try:
    config = get_config('unified_pipeline_config')
    print('✅ Configuration loading successful')
except Exception as e:
    print(f'❌ Configuration failed: {e}')
    sys.exit(1)
"

    # Test Redis connection
    python3 -c "
from utils.redis_manager import get_redis_manager
try:
    redis_manager = get_redis_manager()
    if redis_manager.ping():
        print('✅ Redis connection successful')
    else:
        print('❌ Redis ping failed')
        sys.exit(1)
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"

    success "Installation validation passed"
}

# Main setup function
main() {
    log "🚀 Starting Market7 deployment setup..."
    log "=========================================="

    # Detect OS
    detect_os

    # Check requirements
    check_requirements

    # Install system dependencies
    install_system_deps

    # Create virtual environment
    create_venv

    # Install Python dependencies
    install_python_deps

    # Setup configuration
    setup_config

    # Setup directories
    setup_directories

    # Setup services
    setup_services

    # Setup monitoring
    setup_monitoring

    # Validate installation
    validate_installation

    log "=========================================="
    success "🎉 Market7 deployment setup complete!"
    log ""
    log "Next steps:"
    log "1. Configure credentials: cp config/credentials/*.template config/credentials/"
    log "2. Edit credentials: nano config/credentials/*.json"
    log "3. Start services: sudo systemctl start market7-trading"
    log "4. Check status: sudo systemctl status market7-trading"
    log "5. View logs: journalctl -u market7-trading -f"
    log "6. Health check: python3 health_check.py"
    log ""
    log "For development:"
    log "  source venv/bin/activate"
    log "  python3 main_orchestrator.py"
    log ""
    log "For production:"
    log "  sudo systemctl enable market7-trading"
    log "  sudo systemctl start market7-trading"
}

# Run main function
main "$@"
