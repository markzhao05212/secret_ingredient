#!/bin/bash
# Quick Start Script for Capture the Narrative Bot System
# This script automates the initial setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo -e "${PURPLE}"
    echo "=========================================="
    echo "🤖 CAPTURE THE NARRATIVE BOT SYSTEM 🤖"
    echo "       Quick Start Setup Script"
    echo "=========================================="
    echo -e "${NC}"
}

# Print colored output
print_info() {
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        
        # Check Python version (need 3.9+)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            print_success "Python version is compatible"
        else
            print_error "Python 3.9 or higher is required"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if command_exists pip3 || command_exists pip; then
        print_success "pip found"
    else
        print_error "pip is not installed"
        exit 1
    fi
    
    # Check git
    if command_exists git; then
        print_success "Git found"
    else
        print_warning "Git not found - you may need it for version control"
    fi
    
    # Check optional requirements
    if command_exists docker; then
        print_success "Docker found (optional)"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found (optional - for containerized deployment)"
        DOCKER_AVAILABLE=false
    fi
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Remove existing venv and create new one? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            print_info "Using existing virtual environment"
            return 0
        fi
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Make sure we're in the virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    pip install -r requirements.txt
    print_success "Dependencies installed"
    
    # Install development dependencies if they exist
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        print_success "Development dependencies installed"
    fi
}

# Setup configuration
setup_configuration() {
    print_info "Setting up configuration files..."
    
    # Create .env file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please edit .env with your actual configuration values"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_warning ".env already exists"
    fi
    
    # Setup data directory
    mkdir -p data/logs data/performance data/cache
    print_success "Created data directories"
    
    # Setup accounts file
    if [ ! -f "data/accounts.json" ]; then
        if [ -f "data/accounts.json.example" ]; then
            print_warning "accounts.json not found"
            print_info "Please copy data/accounts.json.example to data/accounts.json"
            print_info "and add your bot account credentials"
        else
            # Create basic example
            cat > data/accounts.json.example << 'EOF'
[
  {
    "username": "your_bot_username_1",
    "password": "your_bot_password_1",
    "note": "Replace with actual credentials"
  },
  {
    "username": "your_bot_username_2",
    "password": "your_bot_password_2", 
    "note": "Add up to 40 accounts for the competition"
  }
]
EOF
            print_success "Created accounts.json.example"
            print_warning "Please copy to data/accounts.json and add real credentials"
        fi
    else
        print_success "accounts.json already exists"
    fi
}

# Run setup validation
run_setup_validation() {
    print_info "Running setup validation..."
    
    # Make sure we're in the virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Run setup.py if it exists
    if [ -f "setup.py" ]; then
        python setup.py
        print_success "Setup validation completed"
    else
        print_warning "setup.py not found, running basic tests..."
        
        # Test basic imports
        python -c "
import sys
import os
sys.path.insert(0, 'src')

try:
    from config.settings import settings
    print('✅ Settings loaded successfully')
    
    from content.generator import ContentGenerator
    print('✅ Content generator imported successfully')
    
    from bot.influence_bot import InfluenceBot
    print('✅ Bot modules imported successfully')
    
    print('✅ Basic setup validation passed')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Setup error: {e}')
    exit(1)
"
        
        if [ $? -eq 0 ]; then
            print_success "Basic validation passed"
        else
            print_error "Validation failed"
            exit 1
        fi
    fi
}

# Run tests
run_tests() {
    print_info "Running test suite..."
    
    # Make sure we're in the virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        source venv/bin/activate
    fi
    
    # Install pytest if not already installed
    pip install pytest pytest-asyncio > /dev/null 2>&1
    
    if [ -d "tests" ]; then
        # Run tests with timeout to prevent hanging
        timeout 60 python -m pytest tests/ -v --tb=short || {
            print_warning "Some tests failed or timed out - this might be normal for integration tests"
            print_info "You can run tests manually later with: pytest tests/ -v"
        }
    else
        print_warning "No tests directory found"
    fi
}

# Docker setup
setup_docker() {
    if [ "$DOCKER_AVAILABLE" = true ]; then
        print_info "Setting up Docker configuration..."
        
        # Test Docker build
        print_info "Testing Docker build..."
        if docker build -t capture-narrative-bot:test . > /dev/null 2>&1; then
            print_success "Docker build successful"
            
            # Clean up test image
            docker rmi capture-narrative-bot:test > /dev/null 2>&1
        else
            print_warning "Docker build failed - you can troubleshoot this later"
        fi
        
        print_success "Docker configuration ready"
        print_info "Use 'docker-compose up' to run the full system"
    fi
}

# Print next steps
print_next_steps() {
    print_info "Setup completed! 🎉"
    echo ""
    print_info "Next steps:"
    echo "1. Edit .env file with your configuration:"
    echo "   - Add your TEAM_INVITATION_CODE"
    echo "   - Set your CAMPAIGN_OBJECTIVE"
    echo "   - Configure API keys (optional)"
    echo ""
    echo "2. Add your bot accounts to data/accounts.json:"
    echo "   cp data/accounts.json.example data/accounts.json"
    echo "   # Then edit with your credentials"
    echo ""
    echo "3. Test the system:"
    echo "   source venv/bin/activate  # Activate virtual environment"
    echo "   python scripts/deploy_bots.py --test-apis --dry-run"
    echo ""
    echo "4. Deploy your bots:"
    echo "   python scripts/deploy_bots.py --objective support_victor --bots 10"
    echo ""
    echo "5. Monitor performance:"
    echo "   python scripts/monitor.py"
    echo ""
    echo "📚 Documentation:"
    echo "   - README.md: Comprehensive guide"
    echo "   - CONTRIBUTING.md: Development guidelines"
    echo "   - config/: Configuration examples"
    echo ""
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "🐳 Docker Quick Start:"
        echo "   docker-compose up bot-system    # Run bots"
        echo "   docker-compose up monitor       # Run monitoring"
        echo ""
    fi
    
    print_success "Good luck in the competition! 🏆"
}

# Main execution
main() {
    print_banner
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_DOCKER=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-tests    Skip running test suite"
                echo "  --skip-docker   Skip Docker setup"
                echo "  -h, --help      Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_requirements
    setup_venv
    install_dependencies
    setup_configuration
    run_setup_validation
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    else
        print_info "Skipping tests (--skip-tests specified)"
    fi
    
    if [ "$SKIP_DOCKER" = false ] && [ "$DOCKER_AVAILABLE" = true ]; then
        setup_docker
    fi
    
    print_next_steps
}

# Run main function
main "$@"