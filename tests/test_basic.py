"""
Basic tests for BATMAN API Testing Framework.
"""

import pytest
from api_testing_framework.config import ConfigManager
from api_testing_framework.parser import OpenAPIParser


class TestConfigManager:
    """Test configuration management."""
    
    def test_config_manager_initialization(self):
        """Test ConfigManager can be initialized."""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert config_manager.config_schema is not None
    
    def test_config_schema_structure(self):
        """Test configuration schema has required fields."""
        config_manager = ConfigManager()
        schema = config_manager.config_schema
        
        assert "required" in schema
        assert "properties" in schema
        
        required_fields = schema["required"]
        assert "api" in required_fields
        assert "openapi" in required_fields
        assert "target_api" in required_fields
        assert "test_generation" in required_fields
        assert "execution" in required_fields


class TestOpenAPIParser:
    """Test OpenAPI parsing functionality."""
    
    def test_parser_initialization(self):
        """Test OpenAPIParser can be initialized."""
        parser = OpenAPIParser()
        assert parser is not None
        assert parser.session is not None
    
    def test_extract_path_params(self):
        """Test path parameter extraction."""
        parser = OpenAPIParser()
        
        # Test simple path
        params = parser._extract_path_params("/users")
        assert params == []
        
        # Test path with parameters
        params = parser._extract_path_params("/users/{user_id}")
        assert params == ["user_id"]
        
        # Test multiple parameters
        params = parser._extract_path_params("/users/{user_id}/posts/{post_id}")
        assert params == ["user_id", "post_id"]


if __name__ == "__main__":
    pytest.main([__file__])
