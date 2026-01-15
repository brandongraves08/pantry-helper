#!/bin/bash
# Production deployment script for Pantry Inventory

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Pantry Inventory - Docker Compose Deployment Script          ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
check_docker() {
    echo -e "\n${YELLOW}Checking Docker installation...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: $DOCKER_VERSION${NC}"
}

check_docker_compose() {
    echo -e "\n${YELLOW}Checking Docker Compose installation...${NC}"
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed.${NC}"
        exit 1
    fi
    DC_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose found: $DC_VERSION${NC}"
}

setup_env() {
    echo -e "\n${YELLOW}Setting up environment...${NC}"
    
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env and set OPENAI_API_KEY${NC}"
        read -p "Press Enter to continue..."
    fi
    
    echo -e "${GREEN}✓ Environment configured${NC}"
}

build_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    docker-compose build
    echo -e "${GREEN}✓ Images built successfully${NC}"
}

start_services() {
    echo -e "\n${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
    
    # Wait for backend
    echo -n "Waiting for API..."
    for i in {1..30}; do
        if docker-compose exec backend curl -f http://localhost:8000/health &> /dev/null; then
            echo -e "${GREEN} ✓${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for database
    echo -n "Waiting for database..."
    for i in {1..30}; do
        if docker-compose exec db pg_isready -U pantry &> /dev/null; then
            echo -e "${GREEN} ✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${GREEN}✓ All services started${NC}"
}

run_migrations() {
    echo -e "\n${YELLOW}Running database migrations...${NC}"
    docker-compose exec -T backend alembic upgrade head
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

seed_database() {
    echo -e "\n${YELLOW}Seeding database with sample data...${NC}"
    docker-compose exec -T backend python scripts/seed_db.py
    echo -e "${GREEN}✓ Database seeded${NC}"
}

show_services() {
    echo -e "\n${YELLOW}Service Status:${NC}"
    docker-compose ps
}

show_urls() {
    echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Services are running! Access them at:${NC}"
    echo -e "\n${YELLOW}Web UI:${NC}          http://localhost:3000"
    echo -e "${YELLOW}API Docs:${NC}        http://localhost:8000/docs"
    echo -e "${YELLOW}API Health:${NC}      http://localhost:8000/health"
    echo -e "${YELLOW}Task Monitor:${NC}    http://localhost:5555"
    echo -e "\n${GREEN}Database:${NC}        postgresql://pantry@localhost:5432/pantry_db"
    echo -e "${GREEN}Redis:${NC}           redis://localhost:6379"
    echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
}

main() {
    case "${1:-start}" in
        start)
            check_docker
            check_docker_compose
            setup_env
            build_images
            start_services
            run_migrations
            seed_database
            show_services
            show_urls
            ;;
        stop)
            echo -e "\n${YELLOW}Stopping services...${NC}"
            docker-compose down
            echo -e "${GREEN}✓ Services stopped${NC}"
            ;;
        restart)
            echo -e "\n${YELLOW}Restarting services...${NC}"
            docker-compose restart
            echo -e "${GREEN}✓ Services restarted${NC}"
            show_services
            ;;
        logs)
            docker-compose logs -f
            ;;
        status)
            show_services
            show_urls
            ;;
        clean)
            echo -e "\n${YELLOW}Cleaning up containers and volumes...${NC}"
            docker-compose down -v
            echo -e "${GREEN}✓ Cleanup complete${NC}"
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 {start|stop|restart|logs|status|clean}${NC}"
            exit 1
            ;;
    esac
}

main "$@"
