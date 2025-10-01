#!/bin/bash

# LangPlug Production Deployment Script
set -e

echo "🚀 Starting LangPlug deployment..."

# Configuration
PROJECT_DIR="/opt/langplug"
BACKUP_DIR="/opt/langplug/backups"
LOG_FILE="/opt/langplug/logs/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check required tools
command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required but not installed"
command -v git >/dev/null 2>&1 || error "Git is required but not installed"

# Change to project directory
cd "$PROJECT_DIR" || error "Cannot change to project directory: $PROJECT_DIR"

# Create necessary directories
mkdir -p logs backups

# Backup database before deployment
log "Creating database backup..."
if ! ./scripts/backup.sh; then
    warn "Database backup failed, continuing anyway..."
fi

# Pull latest code
log "Pulling latest code from repository..."
git fetch origin
git reset --hard origin/main

# Load environment variables
if [[ -f .env ]]; then
    source .env
else
    error "Environment file .env not found"
fi

# Validate required environment variables
required_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "DATABASE_URL")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "Required environment variable $var is not set"
    fi
done

# Build and pull new images
log "Building and pulling new Docker images..."
docker-compose -f docker-compose.production.yml pull

# Stop services gracefully
log "Stopping services gracefully..."
docker-compose -f docker-compose.production.yml down --timeout 30

# Run database migrations
log "Running database migrations..."
docker-compose -f docker-compose.production.yml run --rm backend alembic upgrade head

# Start services
log "Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 30

# Health checks
log "Performing health checks..."

# Check backend health
if ! curl -f -s http://localhost:8000/health > /dev/null; then
    error "Backend health check failed"
fi

# Check frontend
if ! curl -f -s http://localhost:3000/ > /dev/null; then
    error "Frontend health check failed"
fi

# Check database connection
if ! docker-compose -f docker-compose.production.yml exec -T db pg_isready -U langplug > /dev/null; then
    error "Database health check failed"
fi

# Check Redis
if ! docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping > /dev/null; then
    error "Redis health check failed"
fi

# Clean up old Docker images
log "Cleaning up old Docker images..."
docker image prune -f

# Show service status
log "Deployment completed successfully!"
echo ""
log "Service Status:"
docker-compose -f docker-compose.production.yml ps

# Show logs for monitoring
echo ""
log "Recent logs (last 20 lines):"
docker-compose -f docker-compose.production.yml logs --tail=20

log "Deployment completed at $(date)"
log "Application is available at: http://localhost"
