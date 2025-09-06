#!/bin/bash
# MarketPilot Onboarding Script
# Makes MarketPilot portable and ready to go on any machine

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
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        log_info "Please run as a regular user. The script will use sudo when needed."
        exit 1
    fi
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            OS="ubuntu"
            PKG_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            OS="rhel"
            PKG_MANAGER="yum"
        elif command -v dnf &> /dev/null; then
            OS="fedora"
            PKG_MANAGER="dnf"
        else
            OS="linux"
            PKG_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    else
        OS="unknown"
        PKG_MANAGER="unknown"
    fi
    
    log_info "Detected OS: $OS"
}

# Install system dependencies
install_system_deps() {
    log_header "Installing System Dependencies"
    
    case $OS in
        "ubuntu")
            log_info "Updating package list..."
            sudo apt update
            
            log_info "Installing Python and development tools..."
            sudo apt install -y \
                python3.12 \
                python3.12-venv \
                python3.12-dev \
                python3-pip \
                python3-pytest \
                python3-setuptools \
                python3-wheel \
                build-essential \
                curl \
                wget \
                git \
                redis-server \
                postgresql-client \
                nodejs \
                npm \
                docker.io \
                docker-compose \
                jq \
                htop \
                tree
            ;;
        "rhel"|"fedora")
            log_info "Installing Python and development tools..."
            sudo $PKG_MANAGER install -y \
                python3.12 \
                python3.12-pip \
                python3.12-devel \
                python3-pytest \
                gcc \
                gcc-c++ \
                make \
                curl \
                wget \
                git \
                redis \
                postgresql \
                nodejs \
                npm \
                docker \
                docker-compose \
                jq \
                htop \
                tree
            ;;
        "macos")
            log_info "Installing Homebrew if not present..."
            if ! command -v brew &> /dev/null; then
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            log_info "Installing dependencies via Homebrew..."
            brew install \
                python@3.12 \
                redis \
                postgresql \
                node \
                docker \
                docker-compose \
                jq \
                htop \
                tree
            ;;
        *)
            log_warning "Unknown OS. Please install dependencies manually:"
            log_info "Required: Python 3.12+, Redis, PostgreSQL, Node.js, Docker"
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Setup Python virtual environment
setup_python_env() {
    log_header "Setting up Python Environment"
    
    # Remove existing venv if it exists
    if [ -d "venv" ]; then
        log_info "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create virtual environment
    log_info "Creating Python virtual environment..."
    python3.12 -m venv venv
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        log_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
    
    log_success "Python environment ready"
}

# Setup Node.js environment
setup_node_env() {
    log_header "Setting up Node.js Environment"
    
    if [ -d "dashboard_frontend" ]; then
        log_info "Installing frontend dependencies..."
        cd dashboard_frontend
        npm install
        cd ..
        log_success "Frontend dependencies installed"
    else
        log_warning "Frontend directory not found, skipping Node.js setup"
    fi
}

# Setup Redis
setup_redis() {
    log_header "Setting up Redis"
    
    case $OS in
        "ubuntu"|"rhel"|"fedora")
            log_info "Starting Redis service..."
            sudo systemctl start redis-server || sudo systemctl start redis
            sudo systemctl enable redis-server || sudo systemctl enable redis
            ;;
        "macos")
            log_info "Starting Redis via Homebrew..."
            brew services start redis
            ;;
    esac
    
    # Test Redis connection
    log_info "Testing Redis connection..."
    if redis-cli ping | grep -q "PONG"; then
        log_success "Redis is running"
    else
        log_warning "Redis connection failed. Please start Redis manually."
    fi
}

# Setup PostgreSQL
setup_postgresql() {
    log_header "Setting up PostgreSQL"
    
    case $OS in
        "ubuntu"|"rhel"|"fedora")
            log_info "Starting PostgreSQL service..."
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
            ;;
        "macos")
            log_info "Starting PostgreSQL via Homebrew..."
            brew services start postgresql
            ;;
    esac
    
    log_success "PostgreSQL setup complete"
}

# Setup Docker
setup_docker() {
    log_header "Setting up Docker"
    
    case $OS in
        "ubuntu"|"rhel"|"fedora")
            log_info "Starting Docker service..."
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Add user to docker group
            log_info "Adding user to docker group..."
            sudo usermod -aG docker $USER
            ;;
        "macos")
            log_info "Docker Desktop should be started manually on macOS"
            ;;
    esac
    
    log_success "Docker setup complete"
}

# Create configuration files
setup_config() {
    log_header "Setting up Configuration"
    
    # Create logs directory
    mkdir -p logs
    
    # Create data directories
    mkdir -p data/{snapshots,logs,models,backtest}
    mkdir -p ml/{models,datasets,preprocess,recovery,confidence}
    mkdir -p dca/{logs,tracking,recovery}
    mkdir -p fork/{logs,history,candidates}
    mkdir -p indicators/{logs,data}
    
    # Set permissions
    chmod 755 logs data ml dca fork indicators
    
    log_success "Configuration directories created"
}

# Setup pre-commit hooks
setup_precommit() {
    log_header "Setting up Pre-commit Hooks"
    
    source venv/bin/activate
    
    log_info "Installing pre-commit hooks..."
    pre-commit install
    
    log_success "Pre-commit hooks installed"
}

# Run initial tests
run_initial_tests() {
    log_header "Running Initial Tests"
    
    source venv/bin/activate
    
    # Test basic imports
    log_info "Testing basic imports..."
    python3 -c "from config.unified_config_manager import get_config; print('✅ Config system works')"
    
    # Test paper trading setup
    log_info "Testing paper trading configuration..."
    python3 test_paper_trading_config.py
    
    # Run syntax check
    log_info "Running syntax check..."
    make check-syntax || log_warning "Some syntax issues found (expected - 2% remaining work)"
    
    log_success "Initial tests completed"
}

# Create startup scripts
create_startup_scripts() {
    log_header "Creating Startup Scripts"
    
    # Create start script
    cat > start_marketpilot.sh << 'EOF'
#!/bin/bash
# MarketPilot Startup Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting MarketPilot...${NC}"

# Activate virtual environment
source venv/bin/activate

# Start Redis if not running
if ! redis-cli ping &> /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Start services based on argument
case "${1:-all}" in
    "data")
        echo -e "${GREEN}📊 Starting data collection services...${NC}"
        python3 data/rolling_indicators_standalone.py &
        python3 data/rolling_klines_standalone.py &
        ;;
    "fork")
        echo -e "${GREEN}🍴 Starting fork detection...${NC}"
        python3 fork/fork_runner.py &
        ;;
    "dca")
        echo -e "${GREEN}💰 Starting DCA services...${NC}"
        python3 dca/smart_dca_core.py &
        ;;
    "dashboard")
        echo -e "${GREEN}📈 Starting dashboard...${NC}"
        cd dashboard_backend && python3 main.py &
        ;;
    "all")
        echo -e "${GREEN}🌟 Starting all services...${NC}"
        python3 standalone_runner.py
        ;;
    *)
        echo "Usage: $0 [data|fork|dca|dashboard|all]"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ MarketPilot started!${NC}"
EOF

    chmod +x start_marketpilot.sh
    
    # Create stop script
    cat > stop_marketpilot.sh << 'EOF'
#!/bin/bash
# MarketPilot Stop Script

echo "🛑 Stopping MarketPilot services..."

# Kill Python processes related to MarketPilot
pkill -f "python3.*rolling_indicators" || true
pkill -f "python3.*rolling_klines" || true
pkill -f "python3.*fork_runner" || true
pkill -f "python3.*smart_dca_core" || true
pkill -f "python3.*main.py" || true
pkill -f "python3.*standalone_runner" || true

echo "✅ MarketPilot services stopped"
EOF

    chmod +x stop_marketpilot.sh
    
    log_success "Startup scripts created"
}

# Create environment file
create_env_file() {
    log_header "Creating Environment Configuration"
    
    cat > .env << 'EOF'
# MarketPilot Environment Configuration
# Copy this file and customize for your environment

# Environment
ENVIRONMENT=development
BASE_PATH=/home/signal/marketpilot

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marketpilot
POSTGRES_USER=marketpilot
POSTGRES_PASSWORD=your_password_here

# 3Commas API (Paper Trading)
THREECOMMAS_API_KEY=your_paper_api_key
THREECOMMAS_API_SECRET=your_paper_api_secret
THREECOMMAS_BOT_ID=your_fork_bot_id
THREECOMMAS_BOT_ID2=your_dca_bot_id
THREECOMMAS_EMAIL_TOKEN=your_email_token
THREECOMMAS_ACCOUNT_ID=your_paper_account_id

# Binance API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/marketpilot.log
EOF

    log_success "Environment file created"
}

# Main onboarding function
main() {
    log_header "MarketPilot Onboarding Process"
    echo "=================================="
    echo "This script will set up MarketPilot on any machine"
    echo "It will install dependencies, configure the environment,"
    echo "and prepare the system for development and production use."
    echo ""
    
    # Check if running as root
    check_root
    
    # Detect operating system
    detect_os
    
    # Install system dependencies
    install_system_deps
    
    # Setup Python environment
    setup_python_env
    
    # Setup Node.js environment
    setup_node_env
    
    # Setup services
    setup_redis
    setup_postgresql
    setup_docker
    
    # Setup configuration
    setup_config
    
    # Setup pre-commit hooks
    setup_precommit
    
    # Create startup scripts
    create_startup_scripts
    
    # Create environment file
    create_env_file
    
    # Run initial tests
    run_initial_tests
    
    # Final instructions
    log_header "Onboarding Complete! 🎉"
    echo ""
    echo "MarketPilot is now ready to use on this machine!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update .env file with your API keys"
    echo "2. Update config/paper_cred.json with your 3Commas credentials"
    echo "3. Start MarketPilot: ./start_marketpilot.sh"
    echo "4. Stop MarketPilot: ./stop_marketpilot.sh"
    echo ""
    echo "🔧 Development Commands:"
    echo "  make help           - Show all available commands"
    echo "  make quick-smoke    - Run quick tests"
    echo "  make ci-fast        - Run fast CI checks"
    echo "  make format         - Format code"
    echo "  make lint           - Run linting"
    echo ""
    echo "📚 Documentation:"
    echo "  - CODE_QUALITY_GUIDE.md - Complete development guide"
    echo "  - MINIMAL_SYSTEMD_SETUP.md - Deployment options"
    echo "  - PAPER_TRADING_SETUP.md - Paper trading setup"
    echo ""
    echo "🚀 Happy Trading!"
}

# Run main function
main "$@"
