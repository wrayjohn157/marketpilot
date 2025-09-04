#!/bin/bash
"""
Market7 Universal Deployment Script
Automatically detects environment and deploys accordingly
"""

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Detect environment
detect_environment() {
    log "🔍 Detecting deployment environment..."

    # Check for Docker
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        DOCKER_AVAILABLE=true
        log "Docker and Docker Compose detected"
    else
        DOCKER_AVAILABLE=false
        log "Docker not available"
    fi

    # Check for Kubernetes
    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        KUBERNETES_AVAILABLE=true
        log "Kubernetes cluster detected"
    else
        KUBERNETES_AVAILABLE=false
        log "Kubernetes not available"
    fi

    # Check for systemd
    if command -v systemctl &> /dev/null; then
        SYSTEMD_AVAILABLE=true
        log "Systemd detected"
    else
        SYSTEMD_AVAILABLE=false
        log "Systemd not available"
    fi

    # Determine best deployment method
    if [ "$KUBERNETES_AVAILABLE" = true ]; then
        DEPLOYMENT_METHOD="kubernetes"
        log "🎯 Selected deployment method: Kubernetes"
    elif [ "$DOCKER_AVAILABLE" = true ]; then
        DEPLOYMENT_METHOD="docker"
        log "🎯 Selected deployment method: Docker Compose"
    elif [ "$SYSTEMD_AVAILABLE" = true ]; then
        DEPLOYMENT_METHOD="native"
        log "🎯 Selected deployment method: Native (Systemd)"
    else
        DEPLOYMENT_METHOD="manual"
        log "🎯 Selected deployment method: Manual"
    fi
}

# Deploy with Docker Compose
deploy_docker() {
    log "🐳 Deploying with Docker Compose..."

    # Check if docker-compose.yml exists
    if [ ! -f "deploy/docker-compose.yml" ]; then
        error "docker-compose.yml not found"
    fi

    # Copy environment template if .env doesn't exist
    if [ ! -f ".env" ]; then
        log "Creating .env file from template..."
        cp deploy/.env.template .env
        warning "Please edit .env file with your configuration before continuing"
        read -p "Press Enter to continue after editing .env..."
    fi

    # Start services
    log "Starting Docker Compose services..."
    docker-compose -f deploy/docker-compose.yml up -d

    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30

    # Check health
    if curl -f http://localhost:8000/health &> /dev/null; then
        success "Docker Compose deployment successful"
    else
        warning "Health check failed, but services may still be starting"
    fi
}

# Deploy with Kubernetes
deploy_kubernetes() {
    log "☸️  Deploying with Kubernetes..."

    # Check if kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        error "Kubernetes cluster not accessible"
    fi

    # Apply configurations
    log "Applying Kubernetes configurations..."
    kubectl apply -f deploy/kubernetes/namespace.yaml
    kubectl apply -f deploy/kubernetes/configmap.yaml
    kubectl apply -f deploy/kubernetes/secret.yaml
    kubectl apply -f deploy/kubernetes/pvc.yaml
    kubectl apply -f deploy/kubernetes/deployment.yaml
    kubectl apply -f deploy/kubernetes/service.yaml
    kubectl apply -f deploy/kubernetes/ingress.yaml

    # Wait for deployments
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/market7-trading -n market7

    # Check status
    kubectl get pods -n market7
    success "Kubernetes deployment successful"
}

# Deploy natively
deploy_native() {
    log "🖥️  Deploying natively..."

    # Run setup script
    if [ -f "deploy/setup.sh" ]; then
        log "Running setup script..."
        chmod +x deploy/setup.sh
        ./deploy/setup.sh
    else
        error "Setup script not found"
    fi

    # Start services
    log "Starting systemd services..."
    sudo systemctl start market7-trading
    sudo systemctl enable market7-trading

    # Check status
    if systemctl is-active --quiet market7-trading; then
        success "Native deployment successful"
    else
        error "Service failed to start"
    fi
}

# Deploy manually
deploy_manual() {
    log "🔧 Manual deployment instructions..."

    echo "Since no automated deployment method is available, please follow these steps:"
    echo ""
    echo "1. Install Python 3.8+ and pip"
    echo "2. Install Redis and PostgreSQL"
    echo "3. Create virtual environment: python3 -m venv venv"
    echo "4. Activate virtual environment: source venv/bin/activate"
    echo "5. Install dependencies: pip install -r requirements.txt"
    echo "6. Configure credentials in config/credentials/"
    echo "7. Run the application: python3 main_orchestrator.py"
    echo ""
    echo "For detailed instructions, see deploy/README.md"
}

# Show deployment status
show_status() {
    log "📊 Deployment Status"
    echo "=================="

    case $DEPLOYMENT_METHOD in
        "docker")
            echo "🐳 Docker Compose Services:"
            docker-compose -f deploy/docker-compose.yml ps
            echo ""
            echo "🌐 Health Check:"
            curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "Health check endpoint not available"
            ;;
        "kubernetes")
            echo "☸️  Kubernetes Pods:"
            kubectl get pods -n market7
            echo ""
            echo "☸️  Kubernetes Services:"
            kubectl get services -n market7
            ;;
        "native")
            echo "🖥️  Systemd Services:"
            systemctl status market7-trading --no-pager
            ;;
        *)
            echo "Manual deployment - check application logs"
            ;;
    esac
}

# Main function
main() {
    log "🚀 Market7 Universal Deployment Script"
    log "====================================="

    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            detect_environment

            case $DEPLOYMENT_METHOD in
                "docker")
                    deploy_docker
                    ;;
                "kubernetes")
                    deploy_kubernetes
                    ;;
                "native")
                    deploy_native
                    ;;
                "manual")
                    deploy_manual
                    ;;
            esac
            ;;
        "status")
            detect_environment
            show_status
            ;;
        "stop")
            log "🛑 Stopping services..."
            case $DEPLOYMENT_METHOD in
                "docker")
                    docker-compose -f deploy/docker-compose.yml down
                    ;;
                "kubernetes")
                    kubectl delete -f deploy/kubernetes/
                    ;;
                "native")
                    sudo systemctl stop market7-trading
                    ;;
            esac
            success "Services stopped"
            ;;
        "logs")
            log "📋 Showing logs..."
            case $DEPLOYMENT_METHOD in
                "docker")
                    docker-compose -f deploy/docker-compose.yml logs -f
                    ;;
                "kubernetes")
                    kubectl logs -f deployment/market7-trading -n market7
                    ;;
                "native")
                    journalctl -u market7-trading -f
                    ;;
            esac
            ;;
        "help")
            echo "Usage: $0 [deploy|status|stop|logs|help]"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy the application (default)"
            echo "  status  - Show deployment status"
            echo "  stop    - Stop all services"
            echo "  logs    - Show application logs"
            echo "  help    - Show this help message"
            ;;
        *)
            error "Unknown command: $1. Use 'help' for usage information."
            ;;
    esac
}

# Run main function
main "$@"
