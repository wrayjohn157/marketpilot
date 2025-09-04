#!/usr/bin/env python3
"""
Frontend Cleanup Script
Removes duplicate files, organizes components, and prepares for deployment
"""

import os
import shutil
from pathlib import Path
import json

def cleanup_duplicate_files():
    """Remove all duplicate and backup files"""
    print("🧹 Cleaning up duplicate files...")
    
    pages_dir = Path("dashboard_frontend/src/pages")
    components_dir = Path("dashboard_frontend/src/components")
    
    # Files to keep (working versions)
    keep_files = {
        "ActiveTrades.jsx",
        "AskGpt.jsx", 
        "BTCRiskPanel.jsx",
        "BacktestSummary.jsx",
        "DcaConfig.jsx",
        "DcaTracker.jsx",
        "ForkScore.jsx",
        "GptCodeEditor.jsx",
        "MLMonitor.jsx",
        "SafuConfig.jsx",
        "ScanReview.jsx",
        "TradeDashboard.jsx",
        "TvScreenerConfig.jsx",
        "DcaStrategyBuilder.jsx",  # Keep the main one
        "Dashboard.jsx"
    }
    
    # Remove duplicate files
    removed_count = 0
    for file_path in pages_dir.iterdir():
        if file_path.is_file():
            if file_path.name not in keep_files:
                print(f"  Removing: {file_path.name}")
                file_path.unlink()
                removed_count += 1
    
    print(f"✅ Removed {removed_count} duplicate files")
    
    # Clean up components directory
    components_removed = 0
    for file_path in components_dir.rglob("*"):
        if file_path.is_file() and any(suffix in file_path.name for suffix in ["_fallback", "_old", "_backup", "_wasworking", "_design_stub"]):
            print(f"  Removing component: {file_path.name}")
            file_path.unlink()
            components_removed += 1
    
    print(f"✅ Removed {components_removed} duplicate component files")

def create_proper_dockerfile():
    """Create a proper Dockerfile for the frontend"""
    print("🐳 Creating proper Dockerfile...")
    
    dockerfile_content = """# Multi-stage build for React app
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
"""
    
    with open("dashboard_frontend/Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    print("✅ Created proper Dockerfile")

def create_nginx_config():
    """Create nginx configuration for the frontend"""
    print("🌐 Creating nginx configuration...")
    
    nginx_content = """events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # Handle React Router
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # API proxy
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static assets
        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
"""
    
    with open("dashboard_frontend/nginx.conf", "w") as f:
        f.write(nginx_content)
    
    print("✅ Created nginx configuration")

def update_package_json():
    """Update package.json for production deployment"""
    print("📦 Updating package.json...")
    
    package_json_path = Path("dashboard_frontend/package.json")
    
    with open(package_json_path, "r") as f:
        package_data = json.load(f)
    
    # Update package info
    package_data["name"] = "market7-dashboard"
    package_data["version"] = "2.0.0"
    package_data["description"] = "Market7 Trading Dashboard Frontend"
    
    # Remove hardcoded proxy
    if "proxy" in package_data:
        del package_data["proxy"]
    
    # Add environment variables
    package_data["homepage"] = "."
    
    # Add build optimization scripts
    package_data["scripts"]["build:prod"] = "GENERATE_SOURCEMAP=false npm run build"
    package_data["scripts"]["analyze"] = "npm run build && npx bundle-analyzer build/static/js/*.js"
    
    # Add engines
    package_data["engines"] = {
        "node": ">=18.0.0",
        "npm": ">=8.0.0"
    }
    
    with open(package_json_path, "w") as f:
        json.dump(package_data, f, indent=2)
    
    print("✅ Updated package.json")

def create_environment_files():
    """Create environment configuration files"""
    print("🔧 Creating environment files...")
    
    # .env.development
    env_dev = """REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=2.0.0
"""
    with open("dashboard_frontend/.env.development", "w") as f:
        f.write(env_dev)
    
    # .env.production
    env_prod = """REACT_APP_API_URL=/api
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=2.0.0
"""
    with open("dashboard_frontend/.env.production", "w") as f:
        f.write(env_prod)
    
    # .env.example
    env_example = """REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=2.0.0
"""
    with open("dashboard_frontend/.env.example", "w") as f:
        f.write(env_example)
    
    print("✅ Created environment files")

def create_readme():
    """Create proper README for the frontend"""
    print("📚 Creating README...")
    
    readme_content = """# Market7 Trading Dashboard Frontend

A modern React-based frontend for the Market7 trading system.

## Features

- 📊 Real-time trading dashboard
- 📈 Interactive charts and visualizations
- ⚙️ Configuration management
- 🤖 ML monitoring and confidence tracking
- 💰 DCA strategy builder
- 📱 Responsive design

## Quick Start

### Development
```bash
npm install
npm start
```

### Production Build
```bash
npm run build
npm run build:prod
```

### Docker
```bash
docker build -t market7-dashboard .
docker run -p 80:80 market7-dashboard
```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_ENVIRONMENT`: Environment (development/production)
- `REACT_APP_VERSION`: Application version

## Available Scripts

- `npm start`: Start development server
- `npm run build`: Build for production
- `npm run build:prod`: Build with optimizations
- `npm test`: Run tests
- `npm run analyze`: Analyze bundle size

## Architecture

- **React 18**: Modern React with hooks
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Axios**: HTTP client
- **Lucide React**: Icons

## Deployment

The frontend is containerized and ready for deployment with Docker or Kubernetes.

See `deploy/` directory for deployment configurations.
"""
    
    with open("dashboard_frontend/README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created README")

def create_docker_compose():
    """Create docker-compose for frontend"""
    print("🐳 Creating docker-compose...")
    
    compose_content = """version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    image: market7-backend:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
"""
    
    with open("dashboard_frontend/docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    print("✅ Created docker-compose")

def main():
    """Run all cleanup tasks"""
    print("🚀 Starting Frontend Cleanup & Deployment Preparation")
    print("=" * 60)
    
    # Cleanup duplicate files
    cleanup_duplicate_files()
    
    # Create deployment files
    create_proper_dockerfile()
    create_nginx_config()
    update_package_json()
    create_environment_files()
    create_readme()
    create_docker_compose()
    
    print("\\n🎉 Frontend cleanup complete!")
    print("✅ Ready for deployment")
    print("\\nNext steps:")
    print("1. cd dashboard_frontend")
    print("2. npm install")
    print("3. npm run build")
    print("4. docker build -t market7-dashboard .")

if __name__ == "__main__":
    main()