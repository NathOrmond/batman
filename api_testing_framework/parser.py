"""
OpenAPI specification parser for BATMAN API Testing Framework.
"""

import json
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import git
import tempfile
import shutil


@dataclass
class Endpoint:
    """Represents an API endpoint."""
    path: str
    method: str
    operation_id: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    tags: List[str]
    security: List[Dict[str, Any]]


@dataclass
class Schema:
    """Represents a JSON schema."""
    name: str
    schema: Dict[str, Any]
    required_fields: List[str]
    properties: Dict[str, Any]


class OpenAPIParser:
    """Parses OpenAPI specifications from various sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BATMAN-API-Testing-Framework/1.0.0'
        })
    
    def fetch_and_parse(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and parse OpenAPI specification based on configuration."""
        openapi_config = config.get('openapi', {})
        
        if 'spec_url' in openapi_config:
            return self._fetch_from_url(openapi_config['spec_url'])
        elif 'spec_file' in openapi_config:
            return self._fetch_from_file(openapi_config['spec_file'])
        elif 'spec_git' in openapi_config:
            return self._fetch_from_git(openapi_config['spec_git'])
        else:
            raise ValueError("No OpenAPI specification source specified")
    
    def _fetch_from_url(self, url: str) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            elif 'application/yaml' in content_type or 'text/yaml' in content_type:
                return yaml.safe_load(response.text)
            else:
                # Try to parse as JSON first, then YAML
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return yaml.safe_load(response.text)
        
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch OpenAPI spec from URL: {e}")
    
    def _fetch_from_file(self, file_path: str) -> Dict[str, Any]:
        """Fetch OpenAPI specification from local file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to parse as JSON first, then YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)
    
    def _fetch_from_git(self, git_config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch OpenAPI specification from Git repository."""
        repo_url = git_config['repo']
        spec_path = git_config['path']
        branch = git_config.get('branch', 'main')
        token = git_config.get('token')
        
        # Clone repository to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Prepare repository URL with token if provided
                if token:
                    parsed_url = urlparse(repo_url)
                    repo_url = f"{parsed_url.scheme}://{token}@{parsed_url.netloc}{parsed_url.path}"
                
                # Clone repository
                repo = git.Repo.clone_from(repo_url, temp_dir, branch=branch)
                
                # Read spec file
                spec_file = Path(temp_dir) / spec_path
                if not spec_file.exists():
                    raise FileNotFoundError(f"OpenAPI spec file not found in repository: {spec_path}")
                
                with open(spec_file, 'r') as f:
                    content = f.read()
                
                # Try to parse as JSON first, then YAML
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return yaml.safe_load(content)
            
            except git.GitCommandError as e:
                raise ValueError(f"Failed to clone Git repository: {e}")
    
    def parse_endpoints(self, spec: Dict[str, Any]) -> List[Endpoint]:
        """Parse endpoints from OpenAPI specification."""
        endpoints = []
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                    endpoint = Endpoint(
                        path=path,
                        method=method.upper(),
                        operation_id=operation.get('operationId'),
                        summary=operation.get('summary'),
                        description=operation.get('description'),
                        parameters=operation.get('parameters', []),
                        request_body=operation.get('requestBody'),
                        responses=operation.get('responses', {}),
                        tags=operation.get('tags', []),
                        security=operation.get('security', [])
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def extract_schemas(self, spec: Dict[str, Any]) -> Dict[str, Schema]:
        """Extract schemas from OpenAPI specification."""
        schemas = {}
        components = spec.get('components', {})
        schema_definitions = components.get('schemas', {})
        
        for name, schema_def in schema_definitions.items():
            schema = Schema(
                name=name,
                schema=schema_def,
                required_fields=schema_def.get('required', []),
                properties=schema_def.get('properties', {})
            )
            schemas[name] = schema
        
        return schemas
    
    def resolve_refs(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $ref references in OpenAPI specification."""
        def resolve_ref(obj, spec_root):
            if isinstance(obj, dict):
                if '$ref' in obj:
                    ref_path = obj['$ref']
                    if ref_path.startswith('#'):
                        # Internal reference
                        path_parts = ref_path[2:].split('/')
                        resolved = spec_root
                        for part in path_parts:
                            resolved = resolved[part]
                        return resolved
                    else:
                        # External reference - simplified handling
                        return obj
                else:
                    return {k: resolve_ref(v, spec_root) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_ref(item, spec_root) for item in obj]
            else:
                return obj
        
        return resolve_ref(spec, spec)
    
    def validate_spec(self, spec: Dict[str, Any]) -> bool:
        """Validate OpenAPI specification structure."""
        required_fields = ['openapi', 'info', 'paths']
        
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate OpenAPI version
        openapi_version = spec.get('openapi', '')
        if not openapi_version.startswith('3.'):
            raise ValueError(f"Unsupported OpenAPI version: {openapi_version}")
        
        # Validate info section
        info = spec.get('info', {})
        if 'title' not in info:
            raise ValueError("Missing required 'title' in info section")
        
        return True
    
    def get_endpoint_test_cases(self, endpoint: Endpoint) -> List[Dict[str, Any]]:
        """Generate test cases for an endpoint."""
        test_cases = []
        
        # Basic success test case
        success_response = None
        for status_code, response_def in endpoint.responses.items():
            if status_code.startswith('2'):
                success_response = response_def
                break
        
        if success_response:
            test_case = {
                'name': f"{endpoint.method} {endpoint.path} returns {success_response.get('description', 'success')}",
                'method': endpoint.method,
                'path': endpoint.path,
                'expected_status': int(status_code),
                'response_schema': success_response.get('content', {}).get('application/json', {}).get('schema'),
                'test_type': 'success'
            }
            test_cases.append(test_case)
        
        # Error test cases
        for status_code, response_def in endpoint.responses.items():
            if status_code.startswith('4') or status_code.startswith('5'):
                test_case = {
                    'name': f"{endpoint.method} {endpoint.path} returns {status_code}",
                    'method': endpoint.method,
                    'path': endpoint.path,
                    'expected_status': int(status_code),
                    'response_schema': response_def.get('content', {}).get('application/json', {}).get('schema'),
                    'test_type': 'error'
                }
                test_cases.append(test_case)
        
        return test_cases
