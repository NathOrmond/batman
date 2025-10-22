#!/usr/bin/env bash

# BATMAN API Testing Framework - Core Helper Functions
# This file contains the essential helper functions for BATS testing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration from environment
API_BASE_URL="${API_BASE_URL:-http://localhost:5000}"
TIMEOUT="${TIMEOUT:-30}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Default headers array
declare -a DEFAULT_HEADERS=()

# Authentication variables
AUTH_TOKEN="${AUTH_TOKEN:-}"
AUTH_USERNAME="${AUTH_USERNAME:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
API_KEY="${API_KEY:-}"
API_KEY_HEADER="${API_KEY_HEADER:-X-API-Key}"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Utility functions
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

# Generic HTTP request function
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local headers="$4"
    
    local url="${API_BASE_URL}${endpoint}"
    local curl_opts=(-s -X "$method" "$url" -i --max-time "$TIMEOUT")
    
    # Add default headers
    for header in "${DEFAULT_HEADERS[@]}"; do
        curl_opts+=(-H "$header")
    done
    
    # Add authentication
    if [ -n "$AUTH_TOKEN" ]; then
        curl_opts+=(-H "Authorization: Bearer $AUTH_TOKEN")
    elif [ -n "$AUTH_USERNAME" ] && [ -n "$AUTH_PASSWORD" ]; then
        curl_opts+=(-u "$AUTH_USERNAME:$AUTH_PASSWORD")
    elif [ -n "$API_KEY" ]; then
        curl_opts+=(-H "$API_KEY_HEADER: $API_KEY")
    fi
    
    # Add custom headers
    if [ -n "$headers" ]; then
        curl_opts+=(-H "$headers")
    fi
    
    # Add data for POST/PUT requests
    if [ -n "$data" ]; then
        curl_opts+=(-H "Content-Type: application/json" -d "$data")
    fi
    
    curl "${curl_opts[@]}"
}

# Extract status code from response
extract_status_code() {
    local response="$1"
    echo "$response" | head -n 1 | cut -d' ' -f2
}

# Extract response body
extract_response_body() {
    local response="$1"
    echo "$response" | sed '1,/^$/d'
}

# Extract JSON field value
extract_json_field() {
    local response="$1"
    local field="$2"
    local body=$(extract_response_body "$response")
    echo "$body" | jq -r ".$field" 2>/dev/null || echo ""
}

# Check status code
check_status_code() {
    local response="$1"
    local expected="$2"
    local status=$(extract_status_code "$response")
    
    if [ "$status" = "$expected" ]; then
        log_success "Status code $status"
        return 0
    else
        log_error "Expected status $expected, got $status"
        return 1
    fi
}

# Validate JSON schema
validate_json_schema() {
    local response="$1"
    local schema_name="$2"
    local body=$(extract_response_body "$response")
    
    if command -v jsonschema >/dev/null 2>&1; then
        if [ -f "${SCHEMA_DIR}/${schema_name}.json" ]; then
            echo "$body" | jsonschema "${SCHEMA_DIR}/${schema_name}.json" 2>/dev/null
            if [ $? -eq 0 ]; then
                log_success "JSON schema validation passed"
                return 0
            else
                log_error "JSON schema validation failed"
                return 1
            fi
        else
            log_warning "Schema file not found: ${SCHEMA_DIR}/${schema_name}.json"
            return 0
        fi
    else
        log_warning "jsonschema not available, skipping validation"
        return 0
    fi
}

# Validate error response
validate_error_response() {
    local response="$1"
    local error_type="$2"
    local body=$(extract_response_body "$response")
    
    # Check if error response has expected structure
    local error_field=$(echo "$body" | jq -r '.error // .message // .detail' 2>/dev/null)
    if [ -n "$error_field" ] && [ "$error_field" != "null" ]; then
        log_success "Error response validation passed"
        return 0
    else
        log_error "Error response validation failed"
        return 1
    fi
}

# Generate test data
generate_test_data() {
    local schema_name="$1"
    local template_file="${TEMPLATE_DIR}/test-data/${schema_name}.json"
    
    if [ -f "$template_file" ]; then
        cat "$template_file"
    else
        generate_basic_test_data "$schema_name"
    fi
}

# Generate basic test data
generate_basic_test_data() {
    local schema_name="$1"
    case "$schema_name" in
        "User"|"user")
            echo '{"name": "Test User", "email": "test@example.com"}'
            ;;
        "Product"|"product")
            echo '{"name": "Test Product", "price": 99.99}'
            ;;
        "WeatherReport"|"weather_report")
            echo '{"city": "London", "temperature": 20, "condition": "sunny"}'
            ;;
        *)
            echo '{"id": "test-id", "name": "Test Item"}'
            ;;
    esac
}

# Test setup
setup_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $1"
}

# Test teardown
teardown_test() {
    if [ $? -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "Test passed"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "Test failed"
    fi
    echo ""
}

# Print test summary
print_test_summary() {
    echo -e "${CYAN}=== Test Summary ===${NC}"
    echo -e "Total tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "All tests passed!"
        return 0
    else
        log_error "Some tests failed!"
        return 1
    fi
}

# Wait for API to be ready
wait_for_api() {
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if make_request "GET" "/health" >/dev/null 2>&1; then
            log_success "API is ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - API not ready yet"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "API failed to become ready"
    return 1
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Add any cleanup logic here
}

# Setup function for BATS
setup() {
    # Initialize test environment
    log_info "Setting up test environment"
    
    # Set default directories
    export SCHEMA_DIR="${SCHEMA_DIR:-./schemas}"
    export TEMPLATE_DIR="${TEMPLATE_DIR:-./templates}"
    
    # Create directories if they don't exist
    mkdir -p "$SCHEMA_DIR"
    mkdir -p "$TEMPLATE_DIR/test-data"
    
    # Wait for API if needed
    if [ "${WAIT_FOR_API:-false}" = "true" ]; then
        wait_for_api
    fi
}

# Teardown function for BATS
teardown() {
    # Cleanup test environment
    cleanup
}
