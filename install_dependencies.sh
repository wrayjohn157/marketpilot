#!/bin/bash
# Complete dependency installation script for MarketPilot
# Run this on the new VPS to install all required dependencies

echo "🚀 Installing MarketPilot dependencies on new VPS..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and essential tools
echo "🐍 Installing Python and essential tools..."
sudo apt install -y python3 python3-pip python3-venv python3-dev python3-full
sudo apt install -y git curl wget build-essential
sudo apt install -y redis-server nginx docker.io docker-compose

# Install system dependencies for Python packages
echo "🔧 Installing system dependencies..."
sudo apt install -y libffi-dev libssl-dev libxml2-dev libxslt1-dev
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev
sudo apt install -y libblas-dev liblapack-dev gfortran
sudo apt install -y pkg-config

# Create virtual environment
echo "🌐 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo "📚 Installing Python packages..."
pip install fastapi uvicorn redis requests python-dotenv
pip install pandas numpy scipy scikit-learn
pip install ta-lib-bin  # Technical analysis library
pip install websockets aiohttp
pip install pydantic python-multipart
pip install bandit safety pre-commit
pip install pbr  # Required for bandit
pip install types-PyYAML types-redis types-requests types-python-dateutil

# Install additional ML packages
echo "🤖 Installing ML packages..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers datasets
pip install xgboost lightgbm

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Start Redis
echo "🔴 Starting Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start Docker
echo "🐳 Starting Docker..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

echo "✅ All dependencies installed successfully!"
echo "🔄 Please log out and back in for Docker group changes to take effect"
echo "📋 Next steps:"
echo "   1. Copy your credentials to config/credentials/"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: python3 modular_dashboard_api.py"
