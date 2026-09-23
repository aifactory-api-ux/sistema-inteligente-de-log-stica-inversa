#!/bin/bash
# =============================================================================
# Startup Script - Sistema Inteligente de Logistica Inversa
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Print colored message
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env exists, create from .env.example if missing
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status ".env created from .env.example"
        print_warning "Please update .env with your JWT_SECRET for production"
    else
        print_error ".env.example not found. Cannot create .env"
        exit 1
    fi
else
    print_status ".env already exists"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Determine docker compose command
if command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Parse command line arguments
ACTION="${1:-up}"
case "$ACTION" in
    up|start)
        print_status "Building and starting services..."
        $COMPOSE_CMD up --build -d
        print_status "Waiting for services to be healthy..."

        # Wait for backend to be healthy
        print_status "Checking backend health..."
        MAX_WAIT=60
        WAITED=0
        while [ $WAITED -lt $MAX_WAIT ]; do
            if curl -sf http://localhost:21001/health/live > /dev/null 2>&1; then
                print_status "Backend is healthy"
                break
            fi
            sleep 2
            WAITED=$((WAITED + 2))
        done

        if [ $WAITED -ge $MAX_WAIT ]; then
            print_warning "Backend health check timed out, but services are starting"
        fi

        echo ""
        echo "=============================================="
        echo "  Sistema Inteligente de Logistica Inversa"
        echo "=============================================="
        echo ""
        echo -e "  ${GREEN}Frontend:${NC}  http://localhost:3000"
        echo -e "  ${GREEN}Backend:${NC}   http://localhost:21001"
        echo -e "  ${GREEN}API Docs:${NC}  http://localhost:21001/docs"
        echo ""
        echo "  Press Ctrl+C to stop"
        echo "=============================================="
        echo ""

        # Follow logs by default
        $COMPOSE_CMD logs -f
        ;;
    down|stop)
        print_status "Stopping services..."
        $COMPOSE_CMD down
        print_status "Services stopped"
        ;;
    restart)
        print_status "Restarting services..."
        $COMPOSE_CMD down && $COMPOSE_CMD up --build -d
        print_status "Services restarted"
        ;;
    logs)
        shift
        $COMPOSE_CMD logs "$@"
        ;;
    status)
        $COMPOSE_CMD ps
        ;;
    clean)
        print_warning "This will remove all containers, volumes, and images!"
        read -p "Are you sure? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $COMPOSE_CMD down -v --remove-orphans
            print_status "Clean complete"
        else
            print_status "Clean cancelled"
        fi
        ;;
    *)
        echo "Usage: $0 {up|down|restart|logs|status|clean}"
        echo ""
        echo "  up      - Build and start all services (default)"
        echo "  down    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs (use: ./run.sh logs [service])"
        echo "  status  - Show service status"
        echo "  clean   - Remove all containers and volumes"
        exit 1
        ;;
esac
