# OmniDesk AI - Production Deployment Guide

This guide provides comprehensive instructions for deploying OmniDesk AI in a production environment.

## 🚀 Quick Start

### Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+)
- 4GB+ RAM
- 20GB+ disk space
- Domain name (for production)

### One-Command Deployment

```bash
# For Linux/macOS
./scripts/deploy.sh --domain yourdomain.com --email your@email.com

# For Windows PowerShell
.\scripts\deploy-production.ps1 -Domain yourdomain.com -Email your@email.com
```

## 📋 Detailed Setup

### 1. Environment Configuration

Copy and configure the production environment file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` with your settings:

```env
# Basic Configuration
DOMAIN=yourdomain.com
ENVIRONMENT=production
DEBUG=false

# Database
POSTGRES_DB=omni_desk_prod
POSTGRES_USER=omni_user
POSTGRES_PASSWORD=your_secure_password_here

# Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_app_password

# AI Service
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Redis
REDIS_URL=redis://redis:6379/0

# Optional: External Services
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your-backup-bucket
```

### 2. SSL Certificate Setup

For production with HTTPS:

1. **Let's Encrypt (Recommended)**:
   ```bash
   # Install certbot
   sudo apt-get install certbot python3-certbot-nginx
   
   # Get certificate
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Custom Certificate**:
   Place your certificate files in `./ssl/`:
   - `cert.pem`
   - `key.pem`

### 3. Manual Deployment

If you prefer manual deployment:

```bash
# 1. Create directories
mkdir -p logs data/{postgres,qdrant,redis} monitoring/grafana/data

# 2. Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Verify deployment
./scripts/verify-deployment.sh
```

## 🐳 Docker Configuration

### Services Overview

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy & SSL termination |
| frontend | 3000 | Next.js frontend (internal) |
| backend | 8000 | FastAPI backend (internal) |
| postgres | 5432 | PostgreSQL database (internal) |
| redis | 6379 | Redis cache (internal) |
| qdrant | 6333 | Vector database (internal) |
| prometheus | 9090 | Metrics collection (internal) |
| grafana | 3001 | Monitoring dashboard (internal) |

### Resource Requirements

**Minimum (Development)**:
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB

**Recommended (Production)**:
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD

## 📊 Monitoring & Alerting

### Accessing Monitoring

1. **Grafana Dashboard**: http://yourdomain.com:3001
   - Default credentials: admin/admin (change on first login)
   - Pre-configured OmniDesk AI dashboard

2. **Prometheus Metrics**: http://yourdomain.com:9090
   - Raw metrics and query interface
   - Service discovery and targets

### Key Metrics Monitored

- **Service Health**: Up/down status of all services
- **Response Times**: API response latencies (95th percentile)
- **Error Rates**: HTTP 5xx error percentage
- **Resource Usage**: CPU, memory, disk utilization
- **Database Performance**: Connection pool, query times
- **Business Metrics**: Ticket creation rate, AI processing time

### Alert Rules

Configured alerts for:
- Service downtime (>1 minute)
- High CPU usage (>80% for 5 minutes)
- High memory usage (>85% for 5 minutes)
- Database connection failures
- High error rates (>5% for 5 minutes)
- Disk space warnings (<10% free)

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Set up secure environment variables
- [ ] Enable database encryption at rest
- [ ] Configure backup encryption
- [ ] Set up log monitoring
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up VPN access for admin interfaces

### Network Security

```nginx
# Example Nginx security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
```

## 💾 Backup & Recovery

### Automated Backups

The system includes automated backup functionality:

```bash
# Run manual backup
./scripts/backup.sh

# Schedule daily backups (crontab)
0 2 * * * /path/to/omni-desk/scripts/backup.sh
```

### Backup Components

1. **PostgreSQL Database**: Full database dump
2. **Qdrant Vector Data**: Vector embeddings and indices
3. **Redis Data**: Session and cache data
4. **Application Logs**: Recent log files
5. **Configuration Files**: Environment and config files

### Recovery Process

1. **Database Recovery**:
   ```bash
   # Restore PostgreSQL
   docker exec -i omni-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < backup_postgres.sql
   
   # Restore Qdrant
   docker cp backup_qdrant/ omni-qdrant:/qdrant/storage/
   ```

2. **Full System Recovery**:
   ```bash
   # Stop services
   docker-compose -f docker-compose.prod.yml down
   
   # Restore data directories
   tar -xzf backup_$(date +%Y%m%d).tar.gz
   
   # Restart services
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🔧 Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Check disk space usage
   - Review error logs
   - Monitor response times
   - Verify backup integrity

2. **Monthly**:
   - Update Docker images
   - Review security logs
   - Clean up old logs
   - Performance optimization

3. **Quarterly**:
   - Security audit
   - Dependency updates
   - Disaster recovery testing
   - Capacity planning

### Log Management

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f [service_name]

# Log rotation (configure in docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs [service_name]

# Check system resources
docker system df
docker system prune
```

#### Database Connection Issues
```bash
# Test database connectivity
docker exec omni-backend python -c "from app.core.database import test_db_connection; test_db_connection()"

# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres
```

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart [service_name]
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Renew Let's Encrypt certificate
sudo certbot renew
```

### Performance Optimization

1. **Database Optimization**:
   ```sql
   -- Check slow queries
   SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
   
   -- Analyze table statistics
   ANALYZE;
   ```

2. **Application Optimization**:
   - Enable Redis caching
   - Optimize API response sizes
   - Use CDN for static assets
   - Enable gzip compression

3. **System Optimization**:
   - Monitor disk I/O
   - Optimize Docker image sizes
   - Configure swap if needed
   - Use SSD storage for database

## 📞 Support

### Emergency Contacts

- **System Administrator**: [Your Contact]
- **Database Administrator**: [Your Contact]
- **DevOps Team**: [Your Contact]

### Monitoring Endpoints

- **Health Check**: `/api/health`
- **Metrics**: `/metrics`
- **Status Page**: `/api/status`

### Escalation Procedures

1. **Level 1**: Service degradation
   - Check monitoring dashboard
   - Review recent deployments
   - Check system resources

2. **Level 2**: Service outage
   - Execute incident response plan
   - Notify stakeholders
   - Begin recovery procedures

3. **Level 3**: Data loss or security incident
   - Engage security team
   - Begin forensic procedures
   - Execute disaster recovery plan

---

**Last Updated**: $(date +%Y-%m-%d)
**Version**: 1.0
**Maintainer**: OmniDesk AI Team