# BATMAN - API Testing Framework

A standalone, configuration-driven testing solution that automatically generates and executes BATS (Bash Automated Testing System) integration tests for any API based on its OpenAPI specification.

## Features

- **Automated Test Generation**: Generate BATS tests automatically from OpenAPI specifications
- **Multi-API Support**: Test any API by pointing to its OpenAPI spec (URL, file, or Git repository)
- **Environment Agnostic**: Support testing against local, staging, and production environments
- **Configuration-Driven**: Flexible configuration system for different API types and testing scenarios
- **Docker Integration**: Optional containerized testing with Docker Compose
- **Extensible**: Easy to add custom test cases and validation rules
- **Comprehensive Reporting**: Multiple output formats with detailed test results

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd batman

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Or use make for development setup
make install-dev
```

### Basic Usage

```bash
# Initialize a new test project
batman init my-api-tests

# Configure your API
cd my-api-tests
# Edit config/test-config.yaml

# Generate tests
batman generate

# Run tests
batman run

# Run tests with Docker
batman run --docker

# Run tests in parallel
batman run --parallel
```

### Using Example Configuration

```bash
# Generate tests using example config
batman generate -c example-config.yaml

# Run tests with example config
batman run -c example-config.yaml

# Validate configuration
batman validate -c example-config.yaml
```

## Project Structure

```
batman/
├── api_testing_framework/     # Main Python package
│   ├── __init__.py
│   ├── cli.py                 # CLI interface
│   ├── config.py              # Configuration management
│   ├── parser.py              # OpenAPI parsing
│   ├── templates.py           # Template engine
│   ├── generator.py           # Test generation
│   ├── executor.py            # Test execution
│   ├── validation.py          # Response validation
│   ├── docker_integration.py  # Docker integration
│   └── templates/             # Jinja2 templates
│       ├── helpers.bash.j2    # BATS helper functions
│       ├── basic.bats.j2     # Basic endpoint tests
│       ├── crud.bats.j2      # CRUD operations tests
│       ├── error_handling.bats.j2 # Error handling tests
│       ├── docker-compose.yml.j2 # Docker Compose template
│       └── test-data.json.j2  # Test data generation
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # Architecture overview
│   └── design/                # Design documents
│       └── tech-spec.md       # Technical specification
├── helpers/                   # BATS helper functions
│   └── core.bash              # Core helper functions
├── tests/                     # Unit tests
│   ├── __init__.py
│   └── test_basic.py          # Basic tests
├── .gitignore                 # Git ignore rules
├── .editorconfig              # Editor configuration
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .python-version            # Python version specification
├── Makefile                   # Development automation
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
├── setup.cfg                 # Additional project configuration
├── example-config.yaml       # Example configuration
├── README.md                  # Project documentation
└── INSTALL.md                 # Installation guide
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
make install-dev

# Run code formatting
make format

# Run linting and type checking
make check

# Run tests
make test

# Clean up cache files
make clean
```

### Available Make Commands

- `make help` - Show all available commands
- `make install` - Install package in production mode
- `make install-dev` - Install with development dependencies
- `make clean` - Clean Python cache files and build artifacts
- `make test` - Run tests
- `make test-cov` - Run tests with coverage
- `make lint` - Run linting checks
- `make format` - Format code with black and isort
- `make type-check` - Run type checking with mypy
- `make check` - Run all checks (lint, type-check, test)
- `make build` - Build the package
- `make all` - Clean, install dev deps, run checks, and build

### BATMAN-Specific Commands

- `make init-project` - Initialize a new BATMAN project
- `make generate-tests` - Generate tests from example config
- `make run-tests` - Run generated tests
- `make validate-config` - Validate example configuration

### Code Quality Tools

The project includes comprehensive code quality tools:

- **Black**: Code formatting with 88-character line length
- **isort**: Import sorting with black profile compatibility
- **flake8**: Linting with custom configuration
- **mypy**: Static type checking with strict settings
- **pytest**: Testing framework with coverage support
- **pre-commit**: Automated pre-commit hooks for quality checks

### Installation Options

```bash
# Production installation
pip install -e .

# Development installation with all tools
make install-dev

# Using pip directly
pip install -r requirements.txt
pip install -e .[dev]
```

## Documentation

The project includes comprehensive documentation in the `docs/` directory:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture overview and component descriptions
- **[INSTALL.md](INSTALL.md)** - Complete installation guide with troubleshooting
- **[docs/design/tech-spec.md](docs/design/tech-spec.md)** - Technical specification and requirements

### Key Documentation Sections

- **Architecture**: Component design, data flow, and system interactions
- **Installation**: Step-by-step setup instructions for different platforms
- **Configuration**: YAML configuration options and environment variables
- **Templates**: Customizing and creating new test templates
- **Docker**: Containerized testing setup and configuration
- **Development**: Contributing guidelines and development workflow

## Configuration

BATMAN uses YAML configuration files to define API testing parameters:

```yaml
api:
  name: "My API"
  version: "1.0.0"

openapi:
  spec_url: "https://api.example.com/openapi.json"

target_api:
  base_url: "https://api.example.com"
  headers:
    Authorization: "Bearer YOUR_TOKEN"

test_generation:
  output_dir: "generated/tests"
  templates: ["basic", "crud", "error_handling"]

execution:
  environment: "local"
  parallel: true
  max_parallel: 4
```

See `example-config.yaml` for a complete configuration example.

## License

MIT License
