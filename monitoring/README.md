# 📊 Market7 Monitoring Stack

A comprehensive monitoring solution for the Market7 trading system using Prometheus, Grafana, and Alertmanager with remote browser access.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Traefik       │    │   Prometheus    │    │   Grafana       │
│   (Reverse      │────│   (Metrics      │────│   (Dashboards   │
│    Proxy)       │    │    Collection)  │    │    & Alerts)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Alertmanager  │    │   Node Exporter │    │   cAdvisor      │
│   (Notifications│    │   (System       │    │   (Container    │
│    & Alerts)    │    │    Metrics)     │    │    Metrics)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports 80, 443, 3001, 9090, 9093 available
- Domain name configured (optional for remote access)

### 1. Setup Monitoring Stack
```bash
cd monitoring
./setup_monitoring.sh
```

### 2. Configure Remote Access (Optional)
Edit your `/etc/hosts` file or DNS:
```
your-server-ip grafana.market7.local
your-server-ip prometheus.market7.local
your-server-ip alerts.market7.local
```

### 3. Access Dashboards
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 📊 Available Dashboards

### 1. System Overview
- **URL**: `/d/market7-overview`
- **Description**: High-level system health and resource usage
- **Metrics**: CPU, Memory, Service Status, Database Health

### 2. Trading Metrics
- **URL**: `/d/market7-trading`
- **Description**: Trading system performance and errors
- **Metrics**: API Response Times, Error Rates, Trading Errors, DCA Performance

### 3. Custom Dashboards
- **ML Pipeline**: ML model performance and accuracy
- **DCA System**: DCA success rates and failures
- **External APIs**: 3Commas and Binance API health
- **Redis Performance**: Cache hit rates and memory usage

## 🔔 Alerting Rules

### Critical Alerts
- **Backend Down**: Service unavailable for >1 minute
- **Frontend Down**: Service unavailable for >1 minute
- **Database Down**: PostgreSQL/Redis unavailable
- **High Error Rate**: API error rate >5%
- **Low Disk Space**: Disk usage >90%

### Warning Alerts
- **High CPU Usage**: CPU usage >80%
- **High Memory Usage**: Memory usage >85%
- **Trading Errors**: Trading error rate >0.1/sec
- **API Issues**: External API error rate >0.1/sec

### Trading-Specific Alerts
- **DCA Failures**: DCA failure rate >0.05/sec
- **ML Pipeline Down**: ML system unavailable
- **High Trading Volume**: Unusual trading activity

## 📈 Metrics Collection

### System Metrics
- **CPU Usage**: Per-core and overall CPU utilization
- **Memory Usage**: RAM usage and available memory
- **Disk Usage**: Disk space and I/O operations
- **Network**: Network traffic and connections

### Application Metrics
- **HTTP Requests**: Request rate, response times, error rates
- **Trading Operations**: DCA attempts, success rates, errors
- **ML Pipeline**: Model accuracy, prediction counts, training time
- **External APIs**: 3Commas and Binance API health

### Database Metrics
- **PostgreSQL**: Connection count, query performance, locks
- **Redis**: Memory usage, hit rates, operations per second

## 🛠️ Configuration

### Environment Variables
```bash
# Grafana
GRAFANA_ADMIN_PASSWORD=admin123

# Database
POSTGRES_PASSWORD=postgres
POSTGRES_DB=market7

# SMTP (for email alerts)
SMTP_PASSWORD=your_smtp_password

# Slack (for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### Prometheus Configuration
- **Scrape Interval**: 15 seconds
- **Retention**: 30 days
- **Rules**: Custom alerting rules for Market7
- **Targets**: Backend, Frontend, Databases, External APIs

### Grafana Configuration
- **Datasources**: Prometheus, Alertmanager
- **Dashboards**: Pre-configured Market7 dashboards
- **Users**: Admin user with secure password
- **Plugins**: Pie chart, World map, Clock panel

## 🔧 Management Commands

### Start Services
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.monitoring.yml logs -f

# Specific service
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### Restart Services
```bash
docker-compose -f docker-compose.monitoring.yml restart
```

### Update Configuration
```bash
# After editing config files
docker-compose -f docker-compose.monitoring.yml restart
```

## 🌐 Remote Access Setup

### 1. DNS Configuration
Configure your domain to point to your server:
```
grafana.market7.local    -> your-server-ip
prometheus.market7.local -> your-server-ip
alerts.market7.local     -> your-server-ip
```

### 2. SSL Certificates
Traefik automatically handles SSL certificates using Let's Encrypt:
- **Email**: admin@market7.local
- **Storage**: `/etc/traefik/certs/acme.json`
- **Challenge**: HTTP challenge

### 3. Firewall Configuration
Ensure these ports are open:
- **80**: HTTP (redirects to HTTPS)
- **443**: HTTPS (main access)
- **3001**: Grafana (if direct access needed)
- **9090**: Prometheus (if direct access needed)
- **9093**: Alertmanager (if direct access needed)

## 📊 Custom Metrics

### Backend Metrics Endpoints
- `/metrics` - All metrics
- `/metrics/trading` - Trading-specific metrics
- `/metrics/ml` - ML pipeline metrics
- `/metrics/dca` - DCA system metrics
- `/metrics/3commas` - 3Commas API metrics
- `/metrics/redis` - Redis metrics

### Metric Types
- **Counters**: Total requests, errors, operations
- **Histograms**: Response times, durations
- **Gauges**: Current values, rates
- **Summaries**: Quantiles, averages

## 🔍 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose -f docker-compose.monitoring.yml logs

# Check resource usage
docker stats

# Restart services
docker-compose -f docker-compose.monitoring.yml restart
```

#### Metrics Not Appearing
1. Check if backend metrics endpoint is accessible
2. Verify Prometheus targets are up
3. Check scrape configuration in prometheus.yml
4. Restart Prometheus service

#### Grafana Not Loading
1. Check if Grafana container is running
2. Verify port 3001 is accessible
3. Check Grafana logs for errors
4. Restart Grafana service

#### Alerts Not Working
1. Check Alertmanager configuration
2. Verify SMTP/Slack settings
3. Check alert rules in Prometheus
4. Test alert rules manually

### Log Locations
- **Traefik**: `monitoring/logs/traefik/`
- **Prometheus**: `monitoring/logs/prometheus/`
- **Grafana**: `monitoring/logs/grafana/`
- **Alertmanager**: `monitoring/logs/alertmanager/`

## 📚 Additional Resources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

### Community
- [Prometheus Community](https://prometheus.io/community/)
- [Grafana Community](https://community.grafana.com/)

### Support
- Create an issue in the Market7 repository
- Check the troubleshooting section above
- Review logs for error messages

## 🎯 Best Practices

### Security
- Change default passwords
- Use HTTPS for remote access
- Restrict access to monitoring ports
- Regular security updates

### Performance
- Monitor resource usage
- Adjust scrape intervals as needed
- Clean up old metrics data
- Optimize dashboard queries

### Maintenance
- Regular backups of Grafana dashboards
- Monitor disk space usage
- Update components regularly
- Test alerting rules periodically

---

**Happy Monitoring! 📊🚀**
