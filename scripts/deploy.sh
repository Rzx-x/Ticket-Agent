#!/bin/bash

# =============================================================================
# OmniDesk AI Production Deployment Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOGS_DIR="$PROJECT_ROOT/logs"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=============================================================="
    echo "  $1"
    echo "=============================================================="
    echo -e "${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker is installed"
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_success "Docker Compose is installed"
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for production deployments"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 10485760 ]]; then  # 10GB in KB
        log_warning "Less than 10GB disk space available. This may cause issues."
    else
        log_success "Sufficient disk space available"
    fi
    
    # Check available memory (minimum 2GB)
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [[ $available_memory -lt 2048 ]]; then
        log_warning "Less than 2GB memory available. This may cause performance issues."
    else
        log_success "Sufficient memory available"
    fi
}

setup_environment() {
    print_header "Setting Up Environment"
    
    cd "$PROJECT_ROOT"
    
    # Create necessary directories
    log_info "Creating necessary directories..."
    mkdir -p "$BACKUP_DIR" "$LOGS_DIR" uploads nginx/ssl nginx/logs monitoring/grafana monitoring/prometheus
    
    # Check if production environment file exists
    if [[ ! -f ".env.prod" ]]; then
        if [[ -f ".env.production" ]]; then
            log_info "Copying .env.production to .env.prod"
            cp .env.production .env.prod
        else
            log_error "Production environment file not found!"
            log_info "Please copy .env.production to .env.prod and configure it with your production values."
            exit 1
        fi
    fi
    
    # Validate critical environment variables
    log_info "Validating environment configuration..."
    source .env.prod
    
    critical_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "ANTHROPIC_API_KEY")
    for var in "${critical_vars[@]}"; do
        if [[ -z "${!var}" ]] || [[ "${!var}" == "your_"* ]]; then
            log_error "Critical environment variable $var is not properly configured!"
            exit 1
        fi
    done
    
    log_success "Environment configuration validated"
}

generate_ssl_certificates() {
    print_header "SSL Certificate Setup"
    
    if [[ ! -f "nginx/ssl/fullchain.pem" ]] || [[ ! -f "nginx/ssl/privkey.pem" ]]; then
        log_warning "SSL certificates not found. Generating self-signed certificates for testing..."
        log_warning "For production, please use proper SSL certificates from a CA like Let's Encrypt"
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/fullchain.pem \
            -subj "/C=IN/ST=State/L=City/O=OmniDesk/CN=localhost"
        
        log_success "Self-signed certificates generated"
    else
        log_success "SSL certificates found"
    fi
}

create_configs() {
    print_header "Creating Configuration Files"
    
    # Create Nginx configuration
    log_info "Creating Nginx configuration..."
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name _;
        
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
        }
        
        # Health checks
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
EOF
    
    # Create Redis configuration
    log_info "Creating Redis configuration..."
    cat > redis/redis.conf << 'EOF'
# Redis production configuration
bind 0.0.0.0
port 6379
timeout 300
keepalive 60
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
    
    # Create monitoring configuration
    log_info "Creating monitoring configuration..."
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'omnidesk-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF
    
    log_success "Configuration files created"
}

build_and_deploy() {
    print_header "Building and Deploying Application"
    
    cd "$PROJECT_ROOT"
    
    # Pull latest base images
    log_info "Pulling latest base images..."
    docker-compose -f docker-compose.prod.yml pull

    # Build application images
    log_info "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    log_info "Checking service health..."
    if docker-compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend service is healthy"
    else
        log_error "Backend service health check failed"
        return 1
    fi
    
    if docker-compose -f docker-compose.prod.yml exec -T frontend curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend service is healthy"
    else
        log_error "Frontend service health check failed"
        return 1
    fi
}

setup_backup() {
    print_header "Setting Up Backup System"
    
    # Create backup script
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/omnidesk_backup_$DATE.sql"

echo "Starting backup at $(date)"

# Create database backup
pg_dump $DATABASE_URL > "$DB_BACKUP_FILE"
gzip "$DB_BACKUP_FILE"

# Create application data backup
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" -C /app uploads/

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed at $(date)"
EOF
    
    chmod +x scripts/backup.sh
    log_success "Backup system configured"
}

run_post_deployment_tests() {
    print_header "Running Post-Deployment Tests"
    
    # Test basic functionality
    log_info "Testing API endpoints..."
    
    # Test health endpoint
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Health endpoint is working"
    else
        log_error "Health endpoint test failed"
        return 1
    fi
    
    # Test frontend
    if curl -f http://localhost/ > /dev/null 2>&1; then
        log_success "Frontend is accessible"
    else
        log_error "Frontend accessibility test failed"
        return 1
    fi
    
    log_success "All post-deployment tests passed"
}

display_summary() {
    print_header "Deployment Summary"
    
    echo "🎉 OmniDesk AI has been successfully deployed!"
    echo ""
    echo "📊 Service Status:"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    echo "🌐 Access URLs:"
    echo "  Frontend: http://localhost (redirects to HTTPS)"
    echo "  API: http://localhost/api"
    echo "  Health Check: http://localhost/health"
    echo "  Monitoring: http://localhost:3001 (Grafana)"
    echo ""
    echo "📁 Important Directories:"
    echo "  Logs: $LOGS_DIR"
    echo "  Backups: $BACKUP_DIR"
    echo "  SSL Certificates: nginx/ssl/"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
    echo "  Update application: git pull && ./scripts/deploy.sh"
    echo ""
    echo "⚠️  Important Notes:"
    echo "  - Update SSL certificates for production use"
    echo "  - Configure proper domain names"
    echo "  - Set up automated backups"
    echo "  - Monitor application logs regularly"
    echo ""
    log_success "Deployment completed successfully!"
}

cleanup_on_error() {
    log_error "Deployment failed! Cleaning up..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    exit 1
}

# Main deployment process
main() {
    trap cleanup_on_error ERR
    
    print_header "OmniDesk AI Production Deployment"
    
    check_prerequisites
    setup_environment
    generate_ssl_certificates
    create_configs
    build_and_deploy
    setup_backup
    run_post_deployment_tests
    display_summary
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi