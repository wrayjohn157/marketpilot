#!/bin/bash

# Market7 Monitoring Setup Script
# This script sets up Prometheus, Grafana, and Alertmanager for remote access

set -e

echo "🚀 Setting up Market7 Monitoring Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create necessary directories
print_status "Creating monitoring directories..."
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/alertmanager
mkdir -p monitoring/traefik/dynamic
mkdir -p monitoring/logs

# Set proper permissions
chmod 755 monitoring/setup_monitoring.sh
chmod 644 monitoring/prometheus/prometheus.yml
chmod 644 monitoring/alertmanager/alertmanager.yml
chmod 644 monitoring/grafana/provisioning/datasources/prometheus.yml
chmod 644 monitoring/grafana/provisioning/dashboards/dashboard.yml
chmod 644 monitoring/traefik/traefik.yml
chmod 644 monitoring/traefik/dynamic/tls.yml

# Create .env file if it doesn't exist
if [ ! -f monitoring/.env ]; then
    print_status "Creating environment configuration..."
    cat > monitoring/.env << EOF
# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=admin123

# Database Configuration
POSTGRES_PASSWORD=postgres
POSTGRES_DB=marketpilot

# SMTP Configuration (for alerts)
SMTP_PASSWORD=your_smtp_password

# Slack Configuration (for alerts)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Domain Configuration
DOMAIN=marketpilot.local
EOF
    print_warning "Please edit monitoring/.env with your actual configuration values"
fi

# Create Traefik certificates directory
print_status "Creating Traefik certificates directory..."
mkdir -p monitoring/traefik/certs
touch monitoring/traefik/certs/acme.json
chmod 600 monitoring/traefik/certs/acme.json

# Create log directories
print_status "Creating log directories..."
mkdir -p monitoring/logs/traefik
mkdir -p monitoring/logs/prometheus
mkdir -p monitoring/logs/grafana
mkdir -p monitoring/logs/alertmanager

# Start the monitoring stack
print_status "Starting monitoring stack..."
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Check if services are running
print_status "Checking service status..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    print_success "Prometheus is running at http://localhost:9090"
else
    print_error "Prometheus failed to start"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    print_success "Grafana is running at http://localhost:3001"
else
    print_error "Grafana failed to start"
fi

# Check Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    print_success "Alertmanager is running at http://localhost:9093"
else
    print_error "Alertmanager failed to start"
fi

# Display access information
echo ""
echo "🎉 Monitoring stack is now running!"
echo ""
echo "📊 Access URLs:"
echo "  • Grafana: http://localhost:3001 (admin/admin123)"
echo "  • Prometheus: http://localhost:9090"
echo "  • Alertmanager: http://localhost:9093"
echo "  • Traefik Dashboard: http://localhost:8080"
echo ""
echo "🌐 For remote access, configure your DNS:"
echo "  • grafana.marketpilot.local -> your-server-ip"
echo "  • prometheus.marketpilot.local -> your-server-ip"
echo "  • alerts.marketpilot.local -> your-server-ip"
echo ""
echo "📋 Next steps:"
echo "  1. Configure your DNS to point to this server"
echo "  2. Update monitoring/.env with your actual values"
echo "  3. Access Grafana and import dashboards"
echo "  4. Configure alerting rules and notifications"
echo ""
echo "🔧 Management commands:"
echo "  • Start: docker-compose -f docker-compose.monitoring.yml up -d"
echo "  • Stop: docker-compose -f docker-compose.monitoring.yml down"
echo "  • Logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  • Restart: docker-compose -f docker-compose.monitoring.yml restart"
echo ""

print_success "Monitoring setup complete!"
