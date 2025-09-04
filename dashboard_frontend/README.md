# Market7 Trading Dashboard Frontend

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
