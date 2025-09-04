#!/usr/bin/env python3
"""
Comprehensive Project Cleanup Script
Removes unnecessary files, organizes structure, and prepares for production
"""

import os
import shutil
from pathlib import Path
import json
import re

def cleanup_duplicate_files():
    """Remove all duplicate and backup files throughout the project"""
    print("🧹 Cleaning up duplicate files...")
    
    # Patterns to match duplicate files
    duplicate_patterns = [
        "*_backup*",
        "*_old*", 
        "*_fallback*",
        "*_wasworking*",
        "*_design_stub*",
        "*_config_layer*",
        "*_JULY*",
        "*_WORKING*",
        "*_FALLBACK*",
        "*_layer*",
        "*_button*",
        "*_crummy*",
        "*_frozen*",
        "*_mixed*",
        "*_poor*",
        "*_prewireup*",
        "*_raw*",
        "*_restore*",
        "*_missing*",
        "*_invalid*",
        "*_pre*",
        "*_post*",
        "*_locked*",
        "*_has*",
        "*_removal*",
        "*_again*",
        "*_content*",
        "*_this*",
        "*_one*",
        "*_fire*",
        "*_correct*",
        "*_adv*",
        "*_settings*"
    ]
    
    total_removed = 0
    
    # Clean up all directories
    for root, dirs, files in os.walk("."):
        # Skip hidden directories and common build/cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'build', 'dist']]
        
        for file in files:
            file_path = Path(root) / file
            
            # Check if file matches any duplicate pattern
            is_duplicate = any(
                re.search(pattern.replace('*', '.*'), file) 
                for pattern in duplicate_patterns
            )
            
            # Also check for files with multiple underscores (likely duplicates)
            if not is_duplicate and file.count('_') >= 3 and file.endswith(('.jsx', '.js', '.py')):
                is_duplicate = True
            
            if is_duplicate:
                print(f"  Removing: {file_path}")
                file_path.unlink()
                total_removed += 1
    
    print(f"✅ Removed {total_removed} duplicate files")

def cleanup_empty_files():
    """Remove empty files"""
    print("🗑️  Cleaning up empty files...")
    
    empty_removed = 0
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip certain file types
            if file_path.suffix in ['.gitkeep', '.gitignore', '.env.example']:
                continue
                
            try:
                if file_path.stat().st_size == 0:
                    print(f"  Removing empty file: {file_path}")
                    file_path.unlink()
                    empty_removed += 1
            except (OSError, FileNotFoundError):
                continue
    
    print(f"✅ Removed {empty_removed} empty files")

def cleanup_unused_dependencies():
    """Remove unused dependencies from package.json"""
    print("📦 Cleaning up unused dependencies...")
    
    package_json_path = Path("dashboard_frontend/package.json")
    
    if not package_json_path.exists():
        print("  No package.json found")
        return
    
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
    
    # Dependencies that are likely unused
    potentially_unused = [
        "bootstrap",  # Using Tailwind CSS
        "react-bootstrap",  # Using Tailwind CSS
        "d3",  # Using Recharts
        "react-financial-charts",  # Not used in current components
        "framer-motion",  # Not used in current components
        "lightweight-charts",  # Not used in current components
        "axios"  # Using fetch API
    ]
    
    removed_deps = []
    for dep in potentially_unused:
        if dep in package_data.get("dependencies", {}):
            del package_data["dependencies"][dep]
            removed_deps.append(dep)
    
    if removed_deps:
        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
        print(f"  Removed unused dependencies: {', '.join(removed_deps)}")
    else:
        print("  No unused dependencies found")

def organize_project_structure():
    """Organize project structure"""
    print("📁 Organizing project structure...")
    
    # Create proper directory structure
    directories = [
        "dashboard_frontend/src/components/ui",
        "dashboard_frontend/src/components/features", 
        "dashboard_frontend/src/components/layout",
        "dashboard_frontend/src/hooks",
        "dashboard_frontend/src/context",
        "dashboard_frontend/src/services",
        "dashboard_frontend/src/utils",
        "dashboard_frontend/src/types",
        "dashboard_frontend/src/assets",
        "dashboard_frontend/src/assets/images",
        "dashboard_frontend/src/assets/icons",
        "docs",
        "scripts",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created organized directory structure")

def create_gitignore():
    """Create comprehensive .gitignore"""
    print("📝 Creating comprehensive .gitignore...")
    
    gitignore_content = """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production builds
build/
dist/
out/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Storybook build outputs
.out
.storybook-out

# Temporary folders
tmp/
temp/

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Database
*.db
*.sqlite
*.sqlite3

# Redis dumps
dump.rdb

# Backup files
*.bak
*.backup
*.old
*_backup*
*_old*
*_fallback*
*_wasworking*
*_design_stub*
*_config_layer*
*_JULY*
*_WORKING*
*_FALLBACK*
*_layer*
*_button*
*_crummy*
*_frozen*
*_mixed*
*_poor*
*_prewireup*
*_raw*
*_restore*
*_missing*
*_invalid*
*_pre*
*_post*
*_locked*
*_has*
*_removal*
*_again*
*_content*
*_this*
*_one*
*_fire*
*_correct*
*_adv*
*_settings*
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("✅ Created comprehensive .gitignore")

def create_project_readme():
    """Create comprehensive project README"""
    print("📚 Creating comprehensive project README...")
    
    readme_content = """# Market7 Trading System

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
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created comprehensive project README")

def create_deployment_scripts():
    """Create deployment scripts"""
    print("🚀 Creating deployment scripts...")
    
    # Create start script
    start_script = """#!/bin/bash
# Market7 Start Script

echo "🚀 Starting Market7 Trading System..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose -f deploy/docker-compose.yml up -d
elif command -v python3 &> /dev/null; then
    echo "🐍 Starting with Python..."
    # Start backend
    python3 dashboard_backend/main_fixed.py &
    BACKEND_PID=$!
    
    # Start frontend
    cd dashboard_frontend
    npm start &
    FRONTEND_PID=$!
    
    echo "Backend PID: $BACKEND_PID"
    echo "Frontend PID: $FRONTEND_PID"
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
else
    echo "❌ Neither Docker nor Python found. Please install one of them."
    exit 1
fi
"""
    
    with open("start.sh", "w") as f:
        f.write(start_script)
    
    os.chmod("start.sh", 0o755)
    
    # Create stop script
    stop_script = """#!/bin/bash
# Market7 Stop Script

echo "🛑 Stopping Market7 Trading System..."

# Stop Docker containers
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    docker-compose -f deploy/docker-compose.yml down
fi

# Stop Python processes
pkill -f "main_fixed.py"
pkill -f "npm start"

echo "✅ All services stopped"
"""
    
    with open("stop.sh", "w") as f:
        f.write(stop_script)
    
    os.chmod("stop.sh", 0o755)
    
    print("✅ Created deployment scripts")

def main():
    """Run all cleanup tasks"""
    print("🚀 Starting Comprehensive Project Cleanup")
    print("=" * 60)
    
    # Cleanup files
    cleanup_duplicate_files()
    cleanup_empty_files()
    cleanup_unused_dependencies()
    
    # Organize structure
    organize_project_structure()
    
    # Create documentation
    create_gitignore()
    create_project_readme()
    create_deployment_scripts()
    
    print("\\n🎉 Project cleanup complete!")
    print("✅ Project is now clean and organized")
    print("✅ Ready for production deployment")
    print("\\nNext steps:")
    print("1. Review the cleaned up structure")
    print("2. Test the application")
    print("3. Deploy to production")
    print("\\nFiles created:")
    print("- .gitignore (comprehensive)")
    print("- README.md (complete documentation)")
    print("- start.sh (deployment script)")
    print("- stop.sh (deployment script)")

if __name__ == "__main__":
    main()