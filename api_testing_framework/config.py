"""
Configuration management for BATMAN API Testing Framework.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema
from jsonschema import validate


class ConfigManager:
    """Manages configuration loading, validation, and environment handling."""
    
    def __init__(self):
        self.config_schema = self._load_config_schema()
    
    def _load_config_schema(self) -> Dict[str, Any]:
        """Load the configuration schema for validation."""
        return {
            "type": "object",
            "required": ["api", "openapi", "target_api", "test_generation", "execution"],
            "properties": {
                "api": {
                    "type": "object",
                    "required": ["name", "version"],
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "openapi": {
                    "type": "object",
                    "properties": {
                        "spec_url": {"type": "string"},
                        "spec_file": {"type": "string"},
                        "spec_git": {
                            "type": "object",
                            "required": ["repo", "path"],
                            "properties": {
                                "repo": {"type": "string"},
                                "path": {"type": "string"},
                                "branch": {"type": "string"},
                                "token": {"type": "string"}
                            }
                        }
                    }
                },
                "target_api": {
                    "type": "object",
                    "required": ["base_url"],
                    "properties": {
                        "base_url": {"type": "string"},
                        "timeout": {"type": "integer", "minimum": 1},
                        "retries": {"type": "integer", "minimum": 0},
                        "headers": {"type": "object"},
                        "auth": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["bearer", "basic", "api_key"]},
                                "token": {"type": "string"},
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "api_key": {"type": "string"},
                                "api_key_header": {"type": "string"}
                            }
                        }
                    }
                },
                "test_generation": {
                    "type": "object",
                    "required": ["output_dir"],
                    "properties": {
                        "output_dir": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "custom_tests": {"type": "array", "items": {"type": "string"}},
                        "exclude_endpoints": {"type": "array", "items": {"type": "string"}},
                        "include_only": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "execution": {
                    "type": "object",
                    "required": ["environment"],
                    "properties": {
                        "environment": {"type": "string"},
                        "parallel": {"type": "boolean"},
                        "max_parallel": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "integer", "minimum": 1},
                        "retry_failed": {"type": "integer", "minimum": 0},
                        "read_only": {"type": "boolean"}
                    }
                },
                "validation": {
                    "type": "object",
                    "properties": {
                        "strict_mode": {"type": "boolean"},
                        "validate_responses": {"type": "boolean"},
                        "validate_schemas": {"type": "boolean"},
                        "check_contract_compliance": {"type": "boolean"}
                    }
                },
                "docker": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "compose_file": {"type": "string"},
                        "services": {"type": "array", "items": {"type": "string"}},
                        "build_context": {"type": "string"}
                    }
                },
                "reporting": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "array", "items": {"type": "string", "enum": ["console", "json", "junit", "html"]}},
                        "output_dir": {"type": "string"},
                        "include_request_logs": {"type": "boolean"},
                        "include_response_logs": {"type": "boolean"}
                    }
                }
            }
        }
    
    def load_config(self, config_path: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        if config_path is None:
            config_path = "config/test-config.yaml"
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load main configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load environment-specific configuration if specified
        if environment:
            env_config_path = config_file.parent / "environments" / f"{environment}.yaml"
            if env_config_path.exists():
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                    config = self._merge_configs(config, env_config)
        
        # Process environment variables
        config = self._process_env_variables(config)
        
        return config
    
    def _merge_configs(self, base_config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment configuration into base configuration."""
        merged = base_config.copy()
        
        for key, value in env_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _process_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variable substitutions in configuration."""
        def process_value(value):
            if isinstance(value, str):
                # Simple environment variable substitution
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    return os.getenv(env_var, value)
                return value
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            else:
                return value
        
        return process_value(config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        try:
            validate(instance=config, schema=self.config_schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation error: {e.message}")
    
    def create_default_config(self, project_path: Path) -> None:
        """Create default configuration files for a new project."""
        config_dir = project_path / "config"
        
        # Main configuration
        main_config = {
            "api": {
                "name": "My API",
                "version": "1.0.0",
                "description": "API description"
            },
            "openapi": {
                "spec_url": "https://api.example.com/openapi.json"
            },
            "target_api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "retries": 3,
                "headers": {
                    "Content-Type": "application/json"
                }
            },
            "test_generation": {
                "output_dir": "generated/tests",
                "templates": ["basic", "crud", "error_handling"]
            },
            "execution": {
                "environment": "local",
                "parallel": True,
                "max_parallel": 4,
                "timeout": 300,
                "retry_failed": 1,
                "read_only": False
            },
            "validation": {
                "strict_mode": False,
                "validate_responses": True,
                "validate_schemas": True,
                "check_contract_compliance": True
            },
            "docker": {
                "enabled": False
            },
            "reporting": {
                "format": ["console", "json"],
                "output_dir": "reports",
                "include_request_logs": True,
                "include_response_logs": True
            }
        }
        
        with open(config_dir / "test-config.yaml", 'w') as f:
            yaml.dump(main_config, f, default_flow_style=False, sort_keys=False)
        
        # Environment configurations
        environments = {
            "local": {
                "target_api": {
                    "base_url": "http://localhost:5000"
                },
                "docker": {
                    "enabled": True,
                    "services": ["api", "database"]
                }
            },
            "staging": {
                "target_api": {
                    "base_url": "https://staging-api.example.com",
                    "timeout": 60,
                    "headers": {
                        "Authorization": "Bearer ${STAGING_TOKEN}"
                    }
                }
            },
            "production": {
                "target_api": {
                    "base_url": "https://api.example.com",
                    "timeout": 120,
                    "headers": {
                        "Authorization": "Bearer ${PROD_TOKEN}"
                    }
                },
                "execution": {
                    "read_only": True
                }
            }
        }
        
        for env_name, env_config in environments.items():
            with open(config_dir / "environments" / f"{env_name}.yaml", 'w') as f:
                yaml.dump(env_config, f, default_flow_style=False, sort_keys=False)
