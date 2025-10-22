# BATMAN API Testing Framework - Architecture Overview

## Project Structure

```
batman/
├── README.md                           # Project overview and quick start
├── INSTALL.md                          # Installation guide
├── pyproject.toml                      # Python project configuration
├── requirements.txt                     # Python dependencies
├── example-config.yaml                 # Example configuration file
├── tech-spec.md                        # Technical specification
│
├── api_testing_framework/              # Main Python package
│   ├── __init__.py                     # Package initialization
│   ├── cli.py                          # Command-line interface
│   ├── config.py                       # Configuration management
│   ├── parser.py                       # OpenAPI specification parser
│   ├── templates.py                    # Jinja2 template engine
│   ├── generator.py                    # Test generation engine
│   ├── executor.py                     # Test execution engine
│   ├── validation.py                   # Response validation system
│   ├── docker_integration.py           # Docker container management
│   │
│   └── templates/                      # Jinja2 templates
│       ├── helpers.bash.j2             # BATS helper functions template
│       ├── basic.bats.j2               # Basic endpoint tests template
│       ├── crud.bats.j2                # CRUD operations template
│       ├── error_handling.bats.j2      # Error handling tests template
│       ├── docker-compose.yml.j2       # Docker Compose template
│       └── test-data.json.j2           # Test data generation template
│
└── helpers/                            # BATS helper functions
    └── core.bash                       # Core helper functions
```

## Core Components

### 1. Configuration System (`config.py`)
- **Purpose**: Manages YAML configuration files and environment-specific settings
- **Features**:
  - Schema validation using jsonschema
  - Environment variable substitution
  - Multi-environment support (local, staging, production)
  - Default configuration generation

### 2. OpenAPI Parser (`parser.py`)
- **Purpose**: Fetches and parses OpenAPI specifications from various sources
- **Features**:
  - URL, file, and Git repository support
  - Endpoint extraction and analysis
  - Schema resolution and validation
  - Test case generation from OpenAPI specs

### 3. Template Engine (`templates.py`)
- **Purpose**: Jinja2-based template rendering for test generation
- **Features**:
  - Custom filters for data transformation
  - Template context creation
  - Test data generation
  - Multiple template types support

### 4. Test Generator (`generator.py`)
- **Purpose**: Creates BATS test files from OpenAPI specifications
- **Features**:
  - Multiple test templates (basic, CRUD, error handling)
  - Endpoint filtering and customization
  - Docker Compose generation
  - Test data template creation

### 5. Test Executor (`executor.py`)
- **Purpose**: Executes generated BATS tests with various options
- **Features**:
  - Sequential and parallel execution
  - Docker containerized testing
  - Comprehensive reporting (JSON, JUnit, HTML)
  - Timeout and retry handling

### 6. Validation System (`validation.py`)
- **Purpose**: Validates API responses against schemas and rules
- **Features**:
  - JSON schema validation
  - OpenAPI contract compliance
  - Custom validation rules
  - Response structure validation

### 7. Docker Integration (`docker_integration.py`)
- **Purpose**: Manages Docker containers and services for testing
- **Features**:
  - Docker Compose orchestration
  - Service health checking
  - Container lifecycle management
  - Dockerfile generation

### 8. CLI Interface (`cli.py`)
- **Purpose**: Command-line interface for user interaction
- **Features**:
  - Project initialization
  - Test generation and execution
  - Configuration validation
  - Multiple output formats

## Template System

### BATS Test Templates
1. **Basic Template** (`basic.bats.j2`): Tests basic endpoint functionality
2. **CRUD Template** (`crud.bats.j2`): Comprehensive CRUD operation testing
3. **Error Handling Template** (`error_handling.bats.j2`): Error response testing

### Helper Templates
1. **Helpers Template** (`helpers.bash.j2`): Generated BATS helper functions
2. **Docker Compose Template** (`docker-compose.yml.j2`): Container orchestration
3. **Test Data Template** (`test-data.json.j2`): Test data generation

## Usage Workflow

1. **Initialize Project**: `batman init my-api-tests`
2. **Configure API**: Edit `config/test-config.yaml`
3. **Generate Tests**: `batman generate`
4. **Run Tests**: `batman run`
5. **View Reports**: Check `reports/` directory

## Key Features

- **Automated Test Generation**: Creates comprehensive BATS tests from OpenAPI specs
- **Multi-Environment Support**: Test against local, staging, and production APIs
- **Docker Integration**: Optional containerized testing environment
- **Parallel Execution**: Run tests concurrently for faster execution
- **Comprehensive Reporting**: Multiple output formats with detailed results
- **Extensible Templates**: Easy to customize and add new test patterns
- **Validation System**: Ensures API responses comply with specifications

## Dependencies

### Python Dependencies
- `pyyaml`: YAML configuration parsing
- `jinja2`: Template rendering
- `requests`: HTTP client for fetching specs
- `jsonschema`: JSON schema validation
- `click`: CLI interface
- `gitpython`: Git repository support

### System Dependencies
- `bats`: Bash Automated Testing System
- `curl`: HTTP client
- `jq`: JSON processing
- `docker`: Container runtime (optional)

## Architecture Benefits

1. **Modular Design**: Each component has a single responsibility
2. **Extensible**: Easy to add new templates and validation rules
3. **Configuration-Driven**: Flexible configuration system
4. **Environment Agnostic**: Works with any API environment
5. **Comprehensive**: Covers all aspects of API testing
6. **Production Ready**: Includes error handling and logging
