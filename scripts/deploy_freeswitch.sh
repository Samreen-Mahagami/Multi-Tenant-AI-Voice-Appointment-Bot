#!/bin/bash

# Multi-Tenant AI Voice Appointment Bot - FreeSWITCH Deployment Script
# Deploys FreeSWITCH with Bedrock Agent integration for voice appointment booking

set -e

echo "🚀 Deploying FreeSWITCH Voice Integration"
echo "========================================"

# Configuration
FREESWITCH_DIR="freeswitch"
DOCKER_COMPOSE_FILE="$FREESWITCH_DIR/docker-compose.yml"
ENV_FILE="$FREESWITCH_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose (try both old and new syntax)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running as root or in docker group
    if ! docker ps &> /dev/null; then
        print_error "Cannot access Docker. Please run as root or add user to docker group."
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."
    
    mkdir -p "$FREESWITCH_DIR/logs"
    mkdir -p "$FREESWITCH_DIR/recordings"
    mkdir -p "$FREESWITCH_DIR/sounds"
    
    print_success "Directory structure created"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$FREESWITCH_DIR/.env.example" ]; then
            cp "$FREESWITCH_DIR/.env.example" "$ENV_FILE"
            print_warning "Created .env file from example. Please update with your SIP trunk credentials."
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_success "Environment file already exists"
    fi
}

# Validate configuration
validate_configuration() {
    print_status "Validating configuration..."
    
    # Check if required files exist
    local required_files=(
        "$FREESWITCH_DIR/conf/dialplan/default.xml"
        "$FREESWITCH_DIR/conf/sip_profiles/external.xml"
        "$FREESWITCH_DIR/scripts/bedrock_agent_handler.lua"
        "$DOCKER_COMPOSE_FILE"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    print_success "Configuration files validated"
}

# Test backend services
test_backend_services() {
    print_status "Testing backend services connectivity..."
    
    # Test tenant config service
    local tenant_url="https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod/v1/tenants/resolve?did=1001"
    if curl -s -f "$tenant_url" > /dev/null; then
        print_success "Tenant config service is accessible"
    else
        print_error "Cannot reach tenant config service"
        exit 1
    fi
    
    # Test appointment service
    local appointment_url="https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod/v1/health"
    if curl -s -f "$appointment_url" > /dev/null; then
        print_success "Appointment service is accessible"
    else
        print_warning "Appointment service health check failed (may still work)"
    fi
}

# Deploy FreeSWITCH
deploy_freeswitch() {
    print_status "Deploying FreeSWITCH container..."
    
    cd "$FREESWITCH_DIR"
    
    # Pull latest images
    $DOCKER_COMPOSE_CMD pull
    
    # Stop existing containers
    $DOCKER_COMPOSE_CMD down
    
    # Start services
    $DOCKER_COMPOSE_CMD up -d
    
    cd ..
    
    print_success "FreeSWITCH deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T freeswitch fs_cli -x "status" &> /dev/null; then
            print_success "FreeSWITCH is ready"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for FreeSWITCH..."
        sleep 5
        ((attempt++))
    done
    
    print_error "FreeSWITCH failed to start within expected time"
    return 1
}

# Test FreeSWITCH functionality
test_freeswitch() {
    print_status "Testing FreeSWITCH functionality..."
    
    # Test FreeSWITCH status
    if $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T freeswitch fs_cli -x "status" | grep -q "UP"; then
        print_success "FreeSWITCH is running"
    else
        print_error "FreeSWITCH status check failed"
        return 1
    fi
    
    # Test SIP profile
    if $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T freeswitch fs_cli -x "sofia status" | grep -q "external"; then
        print_success "SIP profile loaded"
    else
        print_warning "SIP profile may not be loaded correctly"
    fi
    
    # Test Lua script
    if $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" exec -T freeswitch ls /usr/share/freeswitch/scripts/bedrock_agent_handler.lua &> /dev/null; then
        print_success "Lua script is available"
    else
        print_error "Lua script not found"
        return 1
    fi
}

# Show deployment information
show_deployment_info() {
    print_status "Deployment Information"
    echo "======================"
    
    echo "📋 FreeSWITCH Status:"
    $DOCKER_COMPOSE_CMD -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    echo "🔗 Service Endpoints:"
    echo "   SIP External Profile: 5080/UDP"
    echo "   Event Socket: 8021/TCP"
    echo "   Metrics (if enabled): 9282/TCP"
    
    echo ""
    echo "📞 Configured DIDs:"
    echo "   1001 → Downtown Medical Center"
    echo "   1002 → Westside Family Practice"
    echo "   1003 → Pediatric Care Clinic"
    
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE logs -f"
    echo "   FreeSWITCH CLI: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE exec freeswitch fs_cli"
    echo "   Restart: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE restart"
    echo "   Stop: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE down"
    
    echo ""
    echo "📁 Important Files:"
    echo "   Configuration: $FREESWITCH_DIR/conf/"
    echo "   Scripts: $FREESWITCH_DIR/scripts/"
    echo "   Logs: $FREESWITCH_DIR/logs/"
    echo "   Recordings: $FREESWITCH_DIR/recordings/"
}

# Show next steps
show_next_steps() {
    echo ""
    print_status "Next Steps"
    echo "=========="
    echo "1. Configure your SIP trunk credentials in $ENV_FILE"
    echo "2. Update firewall rules to allow SIP (5080/UDP) and RTP (16384-32768/UDP) traffic"
    echo "3. Configure your SIP trunk provider to route DIDs 1001, 1002, 1003 to this server"
    echo "4. Test voice calls to each DID"
    echo "5. Monitor logs for any issues: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE logs -f"
    echo ""
    echo "🧪 Testing Commands:"
    echo "   Test DID routing: Call 1001, 1002, or 1003"
    echo "   Check FreeSWITCH status: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE exec freeswitch fs_cli -x 'status'"
    echo "   View active calls: $DOCKER_COMPOSE_CMD -f $DOCKER_COMPOSE_FILE exec freeswitch fs_cli -x 'show calls'"
}

# Main deployment function
main() {
    echo "🎯 Starting FreeSWITCH deployment for Multi-Tenant AI Voice Appointment Bot"
    echo ""
    
    check_prerequisites
    create_directories
    setup_environment
    validate_configuration
    test_backend_services
    deploy_freeswitch
    
    if wait_for_services; then
        test_freeswitch
        show_deployment_info
        show_next_steps
        
        print_success "FreeSWITCH deployment completed successfully!"
        echo ""
        print_status "🎉 Phase 6: FreeSWITCH Voice Integration is ready!"
        echo "   Your multi-tenant voice appointment bot can now handle real phone calls."
    else
        print_error "Deployment completed but services may not be fully ready"
        exit 1
    fi
}

# Run main function
main "$@"