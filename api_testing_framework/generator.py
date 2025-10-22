"""
Test generator for creating BATS tests from OpenAPI specifications.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from .parser import OpenAPIParser, Endpoint
from .templates import TemplateEngine
from .config import ConfigManager


class TestGenerator:
    """Generates BATS tests from OpenAPI specifications."""
    
    def __init__(self):
        self.parser = OpenAPIParser()
        self.template_engine = TemplateEngine()
        self.config_manager = ConfigManager()
    
    def generate_tests(self, spec: Dict[str, Any], config: Dict[str, Any]) -> None:
        """Generate BATS tests from OpenAPI specification."""
        # Parse endpoints and schemas
        endpoints = self.parser.parse_endpoints(spec)
        schemas = self.parser.extract_schemas(spec)
        
        # Get test generation configuration
        test_config = config.get('test_generation', {})
        output_dir = Path(test_config.get('output_dir', 'generated/tests'))
        templates = test_config.get('templates', ['basic'])
        exclude_endpoints = test_config.get('exclude_endpoints', [])
        include_only = test_config.get('include_only', [])
        
        # Filter endpoints
        filtered_endpoints = self._filter_endpoints(endpoints, exclude_endpoints, include_only)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate helper functions
        self._generate_helpers(output_dir, config)
        
        # Generate tests for each template
        for template_name in templates:
            self._generate_template_tests(template_name, filtered_endpoints, schemas, config, output_dir)
        
        # Generate custom tests if specified
        custom_tests = test_config.get('custom_tests', [])
        for custom_test in custom_tests:
            self._copy_custom_test(custom_test, output_dir)
    
    def _filter_endpoints(self, endpoints: List[Endpoint], exclude: List[str], include_only: List[str]) -> List[Endpoint]:
        """Filter endpoints based on configuration."""
        if include_only:
            return [ep for ep in endpoints if ep.path in include_only]
        
        if exclude:
            return [ep for ep in endpoints if ep.path not in exclude]
        
        return endpoints
    
    def _generate_helpers(self, output_dir: Path, config: Dict[str, Any]) -> None:
        """Generate BATS helper functions."""
        helpers_content = self.template_engine.render_template('helpers.bash.j2', {
            'api': config.get('api', {}),
            'target_api': config.get('target_api', {})
        })
        
        helpers_file = output_dir / 'helpers.bash'
        with open(helpers_file, 'w') as f:
            f.write(helpers_content)
        
        # Make helpers executable
        os.chmod(helpers_file, 0o755)
    
    def _generate_template_tests(self, template_name: str, endpoints: List[Endpoint], 
                                schemas: Dict[str, Any], config: Dict[str, Any], output_dir: Path) -> None:
        """Generate tests using a specific template."""
        template_file = f"{template_name}.bats.j2"
        
        # Group endpoints by tag for better organization
        endpoints_by_tag = {}
        for endpoint in endpoints:
            for tag in endpoint.tags or ['default']:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        # Generate test files for each tag
        for tag, tag_endpoints in endpoints_by_tag.items():
            context = {
                'endpoints': tag_endpoints,
                'schemas': schemas,
                'api': config.get('api', {}),
                'target_api': config.get('target_api', {}),
                'tag': tag
            }
            
            test_content = self.template_engine.render_template(template_file, context)
            
            # Create test file
            test_file = output_dir / f"{template_name}_{self.template_engine._to_snake_case(tag)}.bats"
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Make test file executable
            os.chmod(test_file, 0o755)
    
    def _copy_custom_test(self, custom_test_path: str, output_dir: Path) -> None:
        """Copy custom test file to output directory."""
        source_path = Path(custom_test_path)
        if source_path.exists():
            dest_path = output_dir / source_path.name
            import shutil
            shutil.copy2(source_path, dest_path)
            os.chmod(dest_path, 0o755)
    
    def generate_docker_compose(self, config: Dict[str, Any]) -> None:
        """Generate Docker Compose file for testing."""
        docker_config = config.get('docker', {})
        if not docker_config.get('enabled', False):
            return
        
        context = {
            'docker': docker_config,
            'api': config.get('api', {}),
            'target_api': config.get('target_api', {})
        }
        
        compose_content = self.template_engine.render_template('docker-compose.yml.j2', context)
        
        compose_file = Path('docker-compose.yml')
        with open(compose_file, 'w') as f:
            f.write(compose_content)
    
    def generate_test_data_templates(self, schemas: Dict[str, Any], output_dir: Path) -> None:
        """Generate test data templates for schemas."""
        test_data_dir = output_dir / 'test-data'
        test_data_dir.mkdir(exist_ok=True)
        
        for schema_name, schema in schemas.items():
            context = {
                'schema': schema,
                'schema_name': schema_name
            }
            
            test_data_content = self.template_engine.render_template('test-data.json.j2', context)
            
            test_data_file = test_data_dir / f"{schema_name}.json"
            with open(test_data_file, 'w') as f:
                f.write(test_data_content)
