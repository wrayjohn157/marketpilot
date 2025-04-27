#!/bin/bash

echo "🚀 Setting up Market7 environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "✅ Setup complete. You can now run trading scripts or start the dashboard."
