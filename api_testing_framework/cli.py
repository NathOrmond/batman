"""
CLI interface for BATMAN API Testing Framework.
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from .parser import OpenAPIParser
from .generator import TestGenerator
from .executor import TestExecutor


@click.group()
@click.version_option(version="1.0.0", prog_name="BATMAN")
def main():
    """BATMAN - API Testing Framework
    
    A standalone, configuration-driven testing solution that automatically generates
    and executes BATS integration tests for any API based on its OpenAPI specification.
    """
    pass


@main.command()
@click.argument('project_name')
@click.option('--template', '-t', help='Template to use for initialization')
def init(project_name: str, template: Optional[str] = None):
    """Initialize a new BATMAN test project."""
    try:
        project_path = Path(project_name)
        if project_path.exists():
            click.echo(f"Error: Directory '{project_name}' already exists", err=True)
            sys.exit(1)
        
        project_path.mkdir(parents=True)
        
        # Create project structure
        config_dir = project_path / "config"
        config_dir.mkdir()
        
        environments_dir = config_dir / "environments"
        environments_dir.mkdir()
        
        templates_dir = config_dir / "templates"
        templates_dir.mkdir()
        
        generated_dir = project_path / "generated"
        generated_dir.mkdir()
        
        reports_dir = project_path / "reports"
        reports_dir.mkdir()
        
        # Create default configuration
        config_manager = ConfigManager()
        config_manager.create_default_config(project_path)
        
        click.echo(f"✅ Created BATMAN project: {project_name}")
        click.echo(f"📁 Project structure created in: {project_path.absolute()}")
        click.echo(f"⚙️  Edit config/test-config.yaml to configure your API")
        
    except Exception as e:
        click.echo(f"Error initializing project: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--env', '-e', help='Environment to use')
def generate(config: Optional[str] = None, env: Optional[str] = None):
    """Generate BATS tests from OpenAPI specification."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config, env)
        
        # Parse OpenAPI specification
        parser = OpenAPIParser()
        spec_data = parser.fetch_and_parse(config_data)
        
        # Generate tests
        generator = TestGenerator()
        generator.generate_tests(spec_data, config_data)
        
        click.echo("✅ Tests generated successfully")
        
    except Exception as e:
        click.echo(f"Error generating tests: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--env', '-e', help='Environment to use')
@click.option('--docker', is_flag=True, help='Run tests in Docker')
@click.option('--parallel', is_flag=True, help='Run tests in parallel')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(config: Optional[str] = None, env: Optional[str] = None, 
        docker: bool = False, parallel: bool = False, verbose: bool = False):
    """Run generated BATS tests."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config, env)
        
        # Execute tests
        executor = TestExecutor()
        results = executor.run_tests(config_data, docker=docker, parallel=parallel, verbose=verbose)
        
        # Display results
        if results.success:
            click.echo("✅ All tests passed!")
        else:
            click.echo(f"❌ {results.failed_tests} test(s) failed")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error running tests: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', help='Path to configuration file')
def validate(config: Optional[str] = None):
    """Validate configuration and OpenAPI specification."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)
        
        # Validate configuration
        config_manager.validate_config(config_data)
        
        # Parse and validate OpenAPI spec
        parser = OpenAPIParser()
        spec_data = parser.fetch_and_parse(config_data)
        parser.validate_spec(spec_data)
        
        click.echo("✅ Configuration and OpenAPI specification are valid")
        
    except Exception as e:
        click.echo(f"Error validating: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
