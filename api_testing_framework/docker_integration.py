"""
Docker integration for BATMAN API Testing Framework.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


class DockerManager:
    """Manages Docker containers and services for testing."""
    
    def __init__(self):
        self.compose_file = None
        self.temp_dir = None
    
    def setup_docker_environment(self, config: Dict[str, Any]) -> bool:
        """Setup Docker environment for testing."""
        docker_config = config.get('docker', {})
        
        if not docker_config.get('enabled', False):
            return False
        
        # Check if Docker is available
        if not self._check_docker_available():
            raise RuntimeError("Docker is not installed or not available")
        
        # Generate Docker Compose file if needed
        compose_file = docker_config.get('compose_file', 'docker-compose.yml')
        if not Path(compose_file).exists():
            self._generate_docker_compose(config)
        
        self.compose_file = compose_file
        return True
    
    def start_services(self, services: Optional[List[str]] = None) -> bool:
        """Start Docker services."""
        if not self.compose_file:
            return False
        
        try:
            cmd = ['docker-compose', '-f', self.compose_file, 'up', '-d']
            if services:
                cmd.extend(services)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error starting Docker services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop Docker services."""
        if not self.compose_file:
            return False
        
        try:
            cmd = ['docker-compose', '-f', self.compose_file, 'down']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error stopping Docker services: {e}")
            return False
    
    def wait_for_service(self, service_name: str, health_check_url: str, 
                        timeout: int = 60) -> bool:
        """Wait for a service to be ready."""
        import time
        import requests
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_check_url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        return False
    
    def get_service_url(self, service_name: str, port: int) -> str:
        """Get URL for a Docker service."""
        return f"http://localhost:{port}"
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _generate_docker_compose(self, config: Dict[str, Any]) -> None:
        """Generate Docker Compose file."""
        from .generator import TestGenerator
        generator = TestGenerator()
        generator.generate_docker_compose(config)


class DockerfileGenerator:
    """Generates Dockerfile for BATMAN testing."""
    
    def generate_dockerfile(self, config: Dict[str, Any], output_path: str = "Dockerfile") -> None:
        """Generate Dockerfile for testing."""
        dockerfile_content = '''FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    jq \\
    git \\
    python3 \\
    python3-pip \\
    bats \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Install jsonschema for validation
RUN pip3 install jsonschema

# Set working directory
WORKDIR /tests

# Copy test files
COPY generated/tests/ /tests/
COPY config/ /config/

# Set environment variables
ENV API_BASE_URL=""
ENV TEST_ENVIRONMENT="docker"

# Make test files executable
RUN chmod +x /tests/*.bats

# Default command
CMD ["bats", "/tests"]
'''
        
        with open(output_path, 'w') as f:
            f.write(dockerfile_content)


class DockerTestRunner:
    """Runs tests in Docker containers."""
    
    def __init__(self):
        self.docker_manager = DockerManager()
        self.dockerfile_generator = DockerfileGenerator()
    
    def run_tests_in_docker(self, config: Dict[str, Any], test_files: List[Path]) -> Dict[str, Any]:
        """Run tests in Docker container."""
        # Setup Docker environment
        if not self.docker_manager.setup_docker_environment(config):
            raise RuntimeError("Failed to setup Docker environment")
        
        # Generate Dockerfile
        self.dockerfile_generator.generate_dockerfile(config)
        
        # Start services
        docker_config = config.get('docker', {})
        services = docker_config.get('services', [])
        
        if services:
            if not self.docker_manager.start_services(services):
                raise RuntimeError("Failed to start Docker services")
            
            # Wait for services to be ready
            for service in services:
                health_url = f"http://localhost:8080/health"  # Default health check
                if not self.docker_manager.wait_for_service(service, health_url):
                    print(f"Warning: Service {service} may not be ready")
        
        # Run tests in container
        try:
            cmd = [
                'docker-compose', '-f', 'docker-compose.yml', 
                'run', '--rm', 'api-testing'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'exit_code': result.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'exit_code': 1
            }
        
        finally:
            # Cleanup
            self.docker_manager.stop_services()
    
    def build_test_image(self, config: Dict[str, Any]) -> bool:
        """Build Docker image for testing."""
        try:
            cmd = ['docker-compose', '-f', 'docker-compose.yml', 'build']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error building Docker image: {e}")
            return False
