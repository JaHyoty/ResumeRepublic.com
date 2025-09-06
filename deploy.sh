#!/bin/bash

# CareerPathPro Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to deploy development environment
deploy_dev() {
    print_status "Deploying development environment..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning "No .env file found. Creating one with default values..."
        cat > .env << EOF
POSTGRES_DB=careerpathpro
POSTGRES_USER=careeruser
POSTGRES_PASSWORD=careerpass
SECRET_KEY=dev-secret-key-not-for-production
ENVIRONMENT=development
VITE_API_URL=http://localhost:8000
EOF
    fi
    
    docker-compose -f docker-compose.dev.yml up -d
    print_status "Development environment deployed!"
    print_status "Database: http://localhost:5432"
    print_status "Backend API: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
}

# Function to deploy production environment
deploy_prod() {
    print_status "Deploying production environment..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_error "No .env file found. Please create one with production values."
        print_error "See .env.example for reference."
        exit 1
    fi
    
    docker-compose -f docker-compose.prod.yml up -d
    print_status "Production environment deployed!"
    print_status "Database: http://localhost:5432"
    print_status "Backend API: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
}

# Function to stop all services
stop_all() {
    print_status "Stopping all services..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_status "All services stopped!"
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        docker-compose -f docker-compose.prod.yml logs -f "$service"
    else
        docker-compose -f docker-compose.prod.yml logs -f
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker-compose -f docker-compose.prod.yml ps
}

# Main script logic
case "${1:-help}" in
    "dev")
        check_docker
        deploy_dev
        ;;
    "prod")
        check_docker
        deploy_prod
        ;;
    "stop")
        stop_all
        ;;
    "logs")
        show_logs "$2"
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        echo "CareerPathPro Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  dev     Deploy development environment"
        echo "  prod    Deploy production environment"
        echo "  stop    Stop all services"
        echo "  logs    Show logs (optionally specify service name)"
        echo "  status  Show service status"
        echo "  help    Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 dev              # Deploy development"
        echo "  $0 prod             # Deploy production"
        echo "  $0 logs backend     # Show backend logs"
        echo "  $0 status           # Show service status"
        ;;
esac
