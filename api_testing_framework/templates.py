"""
Template engine for generating BATS tests from OpenAPI specifications.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, Template
from .parser import Endpoint, Schema


class TemplateEngine:
    """Jinja2-based template engine for test generation."""
    
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['to_snake_case'] = self._to_snake_case
        self.env.filters['to_camel_case'] = self._to_camel_case
        self.env.filters['extract_path_params'] = self._extract_path_params
        self.env.filters['generate_test_data'] = self._generate_test_data
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        components = text.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _extract_path_params(self, path: str) -> List[str]:
        """Extract path parameters from OpenAPI path."""
        import re
        return re.findall(r'\{([^}]+)\}', path)
    
    def _generate_test_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data based on schema."""
        if not schema:
            return {}
        
        test_data = {}
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        for field_name, field_schema in properties.items():
            field_type = field_schema.get('type', 'string')
            
            if field_type == 'string':
                if field_name.lower() in ['email', 'e-mail']:
                    test_data[field_name] = 'test@example.com'
                elif field_name.lower() in ['name', 'title']:
                    test_data[field_name] = f'Test {field_name.title()}'
                elif field_name.lower() in ['id', 'uuid']:
                    test_data[field_name] = 'test-id-123'
                else:
                    test_data[field_name] = f'test_{field_name}'
            elif field_type == 'integer':
                test_data[field_name] = 42
            elif field_type == 'number':
                test_data[field_name] = 42.0
            elif field_type == 'boolean':
                test_data[field_name] = True
            elif field_type == 'array':
                test_data[field_name] = ['item1', 'item2']
            elif field_type == 'object':
                test_data[field_name] = self._generate_test_data(field_schema)
        
        return test_data
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates."""
        return [f.name for f in self.template_dir.glob("*.j2")]
    
    def create_endpoint_context(self, endpoint: Endpoint, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create template context for an endpoint."""
        return {
            'endpoint': endpoint,
            'api': api_config.get('api', {}),
            'target_api': api_config.get('target_api', {}),
            'path_params': self._extract_path_params(endpoint.path),
            'has_request_body': endpoint.request_body is not None,
            'has_parameters': len(endpoint.parameters) > 0,
            'success_responses': {k: v for k, v in endpoint.responses.items() if k.startswith('2')},
            'error_responses': {k: v for k, v in endpoint.responses.items() if k.startswith('4') or k.startswith('5')}
        }
    
    def create_schema_context(self, schema: Schema, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create template context for a schema."""
        return {
            'schema': schema,
            'api': api_config.get('api', {}),
            'test_data': self._generate_test_data(schema.schema)
        }
