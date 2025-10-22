# BATMAN API Testing Framework - Installation Guide

## Prerequisites

Before installing BATMAN, ensure you have the following dependencies:

### System Requirements
- Python 3.8 or higher
- Bash 4.0 or higher
- curl (for HTTP requests)
- jq (for JSON processing)
- Docker (optional, for containerized testing)

### Required Tools
- BATS (Bash Automated Testing System)
- jsonschema (for JSON schema validation)

## Installation

### 1. Install BATMAN

```bash
# Clone the repository
git clone <repository-url>
cd batman

# Install Python dependencies
pip install -r requirements.txt

# Install BATMAN in development mode
pip install -e .
```

### 2. Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y bats curl jq python3 python3-pip
pip3 install jsonschema
```

#### On macOS:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install bats curl jq python3
pip3 install jsonschema
```

#### On CentOS/RHEL:
```bash
sudo yum install -y curl jq python3 python3-pip
pip3 install jsonschema

# Install BATS from source
git clone https://github.com/bats-core/bats-core.git
cd bats-core
sudo ./install.sh /usr/local
```

### 3. Verify Installation

```bash
# Check BATMAN installation
batman --version

# Check BATS installation
bats --version

# Check other dependencies
curl --version
jq --version
```

## Quick Start

### 1. Initialize a New Project

```bash
batman init my-api-tests
cd my-api-tests
```

### 2. Configure Your API

Edit `config/test-config.yaml`:

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
```

### 3. Generate Tests

```bash
batman generate
```

### 4. Run Tests

```bash
batman run
```

## Docker Installation (Optional)

If you want to use Docker for testing:

### 1. Install Docker

Follow the official Docker installation guide for your platform:
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. Enable Docker in Configuration

```yaml
docker:
  enabled: true
  services: ["api", "database"]
```

### 3. Run Tests with Docker

```bash
batman run --docker
```

## Troubleshooting

### Common Issues

#### BATS Not Found
```bash
# Install BATS manually
git clone https://github.com/bats-core/bats-core.git
cd bats-core
sudo ./install.sh /usr/local
```

#### Permission Denied
```bash
# Make test files executable
chmod +x generated/tests/*.bats
```

#### JSON Schema Validation Fails
```bash
# Install jsonschema
pip3 install jsonschema
```

#### Docker Issues
```bash
# Check Docker status
docker --version
docker-compose --version

# Restart Docker service
sudo systemctl restart docker
```

### Getting Help

- Check the logs in `reports/` directory
- Use `--verbose` flag for detailed output
- Ensure all environment variables are set correctly
- Verify API endpoints are accessible

## Development Setup

For developers working on BATMAN:

### 1. Install Development Dependencies

```bash
pip install -r requirements.txt
pip install -e .[dev]
```

### 2. Run Tests

```bash
# Run unit tests
pytest tests/

# Run linting
flake8 api_testing_framework/
black api_testing_framework/

# Run type checking
mypy api_testing_framework/
```

### 3. Build Documentation

```bash
# Generate documentation
sphinx-build docs/ docs/_build/
```
