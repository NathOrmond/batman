# API Testing Framework - Technical Specification

## 1. Project Overview

### 1.1 Purpose
The API Testing Framework is a standalone, configuration-driven testing solution that automatically generates and executes BATS (Bash Automated Testing System) integration tests for any API based on its OpenAPI specification. The framework eliminates the need to manually write integration tests by parsing OpenAPI specs and generating comprehensive test suites.

### 1.2 Objectives
- **Automated Test Generation**: Generate BATS tests automatically from OpenAPI specifications
- **Multi-API Support**: Test any API by pointing to its OpenAPI spec (URL, file, or Git repository)
- **Environment Agnostic**: Support testing against local, staging, and production environments
- **Configuration-Driven**: Flexible configuration system for different API types and testing scenarios
- **Docker Integration**: Optional containerized testing with Docker Compose
- **Extensible**: Easy to add custom test cases and validation rules
- **Comprehensive Reporting**: Multiple output formats with detailed test results

### 1.3 Target Users
- **API Developers**: Test their own APIs during development
- **QA Engineers**: Perform integration testing on various APIs
- **DevOps Teams**: Validate API contracts in CI/CD pipelines
- **API Consumers**: Test third-party APIs they integrate with

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Configuration │    │  OpenAPI Spec   │    │   Target API    │
│   (YAML/JSON)   │    │  (URL/File/Git) │    │  (Any Endpoint) │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Test Generator        │
                    │  (Python Core Engine)     │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Generated BATS Tests   │
                    │   (Bash Test Files)      │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Test Executor         │
                    │  (BATS + Docker)        │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Test Reports          │
                    │  (Console/JSON/JUnit)    │
                    └──────────────────────────┘
```

### 2.2 Core Components

#### 2.2.1 Configuration System
- **Main Config**: `config/test-config.yaml` - Primary configuration file
- **Environment Configs**: `config/environments/*.yaml` - Environment-specific settings
- **Template Configs**: `config/templates/*.yaml` - Test generation templates

#### 2.2.2 Test Generator Engine
- **OpenAPI Parser**: Fetches and parses OpenAPI specifications
- **Template Engine**: Jinja2-based template rendering
- **Test Generator**: Creates BATS test files from templates
- **Schema Validator**: Validates generated tests against schemas

#### 2.2.3 Test Execution Engine
- **BATS Runner**: Executes generated BATS tests
- **Docker Runner**: Containerized test execution
- **Parallel Runner**: Concurrent test execution
- **Result Aggregator**: Collects and processes test results

#### 2.2.4 Validation System
- **Response Validator**: Validates API responses
- **Schema Validator**: JSON schema validation
- **Contract Validator**: OpenAPI contract compliance
- **Custom Validators**: User-defined validation rules

## 3. Detailed Component Specifications

### 3.1 Configuration System

#### 3.1.1 Main Configuration Schema

```yaml
# API Testing Framework Configuration Schema
api:
  name: string                    # API name for identification
  version: string                 # API version
  description?: string            # Optional description

openapi:
  spec_url?: string              # External OpenAPI spec URL
  spec_file?: string             # Local OpenAPI spec file path
  spec_git?:                     # Git repository configuration
    repo: string                 # Git repository URL
    path: string                 # Path to spec file in repo
    branch?: string              # Git branch (default: main)
    token?: string               # Authentication token for private repos

target_api:
  base_url: string               # Base URL of target API
  timeout: integer               # Request timeout in seconds
  retries: integer               # Number of retry attempts
  headers:                       # Default headers
    [key: string]: string
  auth?:                         # Authentication configuration
    type: "bearer" | "basic" | "api_key"
    token?: string
    username?: string
    password?: string
    api_key?: string
    api_key_header?: string

test_generation:
  output_dir: string             # Output directory for generated tests
  templates:                     # List of templates to use
    - string
  custom_tests?:                 # Custom test files to include
    - string
  exclude_endpoints?:            # Endpoints to exclude from testing
    - string
  include_only?:                # Only test these endpoints
    - string

execution:
  environment: string            # Target environment
  parallel: boolean              # Enable parallel execution
  max_parallel: integer          # Maximum parallel processes
  timeout: integer               # Overall test timeout
  retry_failed: integer          # Retry failed tests
  read_only: boolean             # Only run read-only tests

validation:
  strict_mode: boolean          # Enable strict validation
  validate_responses: boolean    # Validate response schemas
  validate_schemas: boolean     # Validate JSON schemas
  check_contract_compliance: boolean # Check OpenAPI compliance

docker:
  enabled: boolean              # Enable Docker integration
  compose_file?: string          # Custom docker-compose file
  services?:                    # Required services
    - string
  build_context?: string        # Docker build context

reporting:
  format:                       # Output formats
    - "console" | "json" | "junit" | "html"
  output_dir: string            # Report output directory
  include_request_logs: boolean # Include request logs
  include_response_logs: boolean # Include response logs
```

#### 3.1.2 Environment Configuration

```yaml
# config/environments/local.yaml
target_api:
  base_url: "http://localhost:5000"
  timeout: 30

docker:
  enabled: true
  services: ["api", "database"]

# config/environments/staging.yaml
target_api:
  base_url: "https://staging-api.example.com"
  timeout: 60
  headers:
    Authorization: "Bearer ${STAGING_TOKEN}"

# config/environments/production.yaml
target_api:
  base_url: "https://api.example.com"
  timeout: 120
  headers:
    Authorization: "Bearer ${PROD_TOKEN}"

execution:
  read_only: true  # Only run GET requests in production
```

### 3.2 Test Generation System

#### 3.2.1 OpenAPI Parser

**Responsibilities:**
- Fetch OpenAPI specifications from various sources
- Parse and validate OpenAPI documents
- Extract endpoint definitions and schemas
- Resolve $ref references
- Generate test case metadata

**Key Functions:**
```python
class OpenAPIParser:
    def fetch_spec(self, config: dict) -> dict
    def parse_endpoints(self, spec: dict) -> List[Endpoint]
    def extract_schemas(self, spec: dict) -> Dict[str, dict]
    def resolve_refs(self, spec: dict) -> dict
    def validate_spec(self, spec: dict) -> bool
```

#### 3.2.2 Template Engine

**Template Types:**
1. **Basic Endpoint Template**: Tests basic CRUD operations
2. **CRUD Operations Template**: Comprehensive CRUD testing
3. **Error Handling Template**: Tests error responses and edge cases
4. **Authentication Template**: Tests authentication flows
5. **Custom Template**: User-defined test patterns

**Template Variables:**
- `{{ endpoint.path }}` - API endpoint path
- `{{ endpoint.method }}` - HTTP method
- `{{ endpoint.operation_id }}` - OpenAPI operation ID
- `{{ endpoint.responses }}` - Expected responses
- `{{ endpoint.request_body }}` - Request body schema
- `{{ api.name }}` - API name from config
- `{{ target_api.base_url }}` - Target API base URL

#### 3.2.3 Generated Test Structure

**Example Generated Test:**
```bash
#!/usr/bin/env bats

# Generated test for Weather API
# Endpoint: GET /weather/{city}
# Operation ID: get_city_weather

load helpers

@test "GET /weather/{city} returns 200 OK" {
  local city="London"
  local endpoint="/weather/${city}"
  
  response=$(make_request "GET" "$endpoint")
  
  check_status_code "$response" "200"
  validate_json_schema "$response" "WeatherReport"
  
  # Verify required fields
  city_name=$(extract_json_field "$response" "city")
  [ "$city_name" = "$city" ]
}

@test "GET /weather/{city} returns 404 for non-existent city" {
  local city="NonExistentCity"
  local endpoint="/weather/${city}"
  
  response=$(make_request "GET" "$endpoint")
  
  check_status_code "$response" "404"
  validate_error_response "$response" "NotFoundError"
}
```

### 3.3 Test Execution Engine

#### 3.3.1 BATS Runner

**Features:**
- Execute generated BATS test files
- Support for parallel execution
- Timeout handling
- Retry logic for failed tests
- Real-time output streaming

**Implementation:**
```python
class BATSRunner:
    def run_tests(self, test_dir: str, config: dict) -> TestResults
    def run_parallel(self, test_files: List[str], max_parallel: int) -> TestResults
    def setup_environment(self, config: dict) -> bool
    def cleanup_environment(self) -> None
```

#### 3.3.2 Docker Integration

**Docker Compose Template:**
```yaml
version: '3.8'

services:
  api-testing:
    build: .
    container_name: api-testing-framework
    volumes:
      - ./generated/tests:/tests
      - ./reports:/reports
    environment:
      - API_BASE_URL=${API_BASE_URL}
      - TEST_ENVIRONMENT=${TEST_ENVIRONMENT}
    depends_on:
      {% for service in docker.services %}
      - {{ service }}
      {% endfor %}
    command: ["bats", "/tests/integration"]
```

### 3.4 Validation System

#### 3.4.1 Response Validator

**Validation Types:**
- HTTP status code validation
- Response header validation
- JSON schema validation
- Response time validation
- Content type validation

#### 3.4.2 Schema Validator

**Features:**
- JSON Schema validation using jsonschema library
- OpenAPI schema validation
- Custom validation rules
- Detailed error reporting

#### 3.4.3 Contract Validator

**Contract Compliance Checks:**
- Endpoint availability
- Request/response schema compliance
- Error response format compliance
- Authentication requirement compliance

### 3.5 Helper Functions

#### 3.5.1 Generic HTTP Client

```bash
# Generic HTTP request function
make_request() {
  local method="$1"
  local endpoint="$2"
  local data="$3"
  local headers="$4"
  
  local url="${API_BASE_URL}${endpoint}"
  local curl_opts=(-s -X "$method" "$url" -i)
  
  # Add default headers
  for header in "${DEFAULT_HEADERS[@]}"; do
    curl_opts+=(-H "$header")
  done
  
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
```

#### 3.5.2 Validation Functions

```bash
# Status code validation
check_status_code() {
  local response="$1"
  local expected="$2"
  local status=$(extract_status_code "$response")
  
  if [ "$status" != "$expected" ]; then
    echo "Expected status $expected, got $status"
    return 1
  fi
}

# JSON schema validation
validate_json_schema() {
  local response="$1"
  local schema_name="$2"
  local body=$(extract_response_body "$response")
  
  echo "$body" | jsonschema "${SCHEMA_DIR}/${schema_name}.json"
}

# Test data generation
generate_test_data() {
  local schema_name="$1"
  local template_file="${TEMPLATE_DIR}/test-data/${schema_name}.json.template"
  
  if [ -f "$template_file" ]; then
    envsubst < "$template_file"
  else
    generate_basic_test_data "$schema_name"
  fi
}
```

## 4. Implementation Plan

### 4.1 Phase 1: Core Framework (Weeks 1-2)
- [ ] Project structure setup
- [ ] Configuration system implementation
- [ ] OpenAPI parser development
- [ ] Basic template engine
- [ ] Simple test generation

### 4.2 Phase 2: Test Execution (Weeks 3-4)
- [ ] BATS runner implementation
- [ ] Docker integration
- [ ] Parallel execution support
- [ ] Basic reporting system

### 4.3 Phase 3: Validation & Templates (Weeks 5-6)
- [ ] Response validation system
- [ ] Schema validation
- [ ] Template library expansion
- [ ] Custom validation rules

### 4.4 Phase 4: Advanced Features (Weeks 7-8)
- [ ] Contract validation
- [ ] Advanced reporting
- [ ] CI/CD integration
- [ ] Documentation and examples

## 5. Usage Examples

### 5.1 Basic Usage

```bash
# 1. Initialize project
api-test init my-api-tests

# 2. Configure for external API
cat > config/test-config.yaml << EOF
api:
  name: "External Weather API"
openapi:
  spec_url: "https://api.openweathermap.org/openapi.json"
target_api:
  base_url: "https://api.openweathermap.org/data/2.5"
  headers:
    Authorization: "Bearer YOUR_API_KEY"
EOF

# 3. Generate tests
api-test generate

# 4. Run tests
api-test run
```

### 5.2 Docker-based Testing

```bash
# Configure for local development with Docker
cat > config/test-config.yaml << EOF
api:
  name: "Local Weather API"
openapi:
  spec_file: "./specs/weather-api.yaml"
target_api:
  base_url: "http://localhost:5000"
docker:
  enabled: true
  services: ["weather-api", "postgres"]
EOF

# Generate and run with Docker
api-test generate
api-test run --docker
```

### 5.3 Multi-Environment Testing

```bash
# Test against staging
api-test run --env staging

# Test against production (read-only)
api-test run --env production --read-only

# Test all environments
api-test run --env all
```

## 6. Technical Requirements

### 6.1 Dependencies

**Python Dependencies:**
- `pyyaml` - YAML configuration parsing
- `jinja2` - Template rendering
- `requests` - HTTP client for fetching specs
- `jsonschema` - JSON schema validation
- `click` - CLI interface

**System Dependencies:**
- `bats` - Bash Automated Testing System
- `curl` - HTTP client
- `jq` - JSON processing
- `docker` - Container runtime
- `docker-compose` - Container orchestration

### 6.2 Performance Requirements

- **Test Generation**: < 30 seconds for APIs with < 100 endpoints
- **Test Execution**: Support parallel execution with configurable concurrency
- **Memory Usage**: < 512MB for typical API testing scenarios
- **Disk Usage**: < 100MB for generated test files and reports

### 6.3 Compatibility

- **Python**: 3.8+
- **Bash**: 4.0+
- **Docker**: 20.10+
- **OpenAPI**: 3.0+ specifications
- **Operating Systems**: Linux, macOS, Windows (with WSL)

## 7. Security Considerations

### 7.1 API Key Management
- Support for environment variables for sensitive data
- Secure storage of authentication tokens
- Masking of sensitive data in logs and reports

### 7.2 Network Security
- Support for HTTPS endpoints
- Certificate validation options
- Proxy support for corporate environments

### 7.3 Container Security
- Non-root user execution in containers
- Minimal base images
- Security scanning of dependencies

## 8. Testing Strategy

### 8.1 Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Achieve > 90% code coverage

### 8.2 Integration Tests
- Test component interactions
- Use real OpenAPI specifications
- Validate generated test quality

### 8.3 End-to-End Tests
- Test complete workflows
- Use sample APIs for validation
- Performance and reliability testing

## 9. Documentation Requirements

### 9.1 User Documentation
- Getting started guide
- Configuration reference
- Template development guide
- Troubleshooting guide

### 9.2 Developer Documentation
- Architecture overview
- API reference
- Contributing guidelines
- Release notes

### 9.3 Examples
- Sample configurations for common APIs
- Custom template examples
- CI/CD integration examples

## 10. Future Enhancements

### 10.1 Advanced Features
- GraphQL API support
- gRPC API testing
- Performance testing integration
- Load testing capabilities

### 10.2 Integration Features
- GitHub Actions integration
- Jenkins plugin
- Slack/Teams notifications
- Test result dashboards

### 10.3 Developer Experience
- IDE plugins
- VS Code extension
- IntelliJ plugin
- Command-line autocompletion

---