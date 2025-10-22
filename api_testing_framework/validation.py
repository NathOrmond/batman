"""
Validation system for BATMAN API Testing Framework.
"""

import json
import jsonschema
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Represents the result of a validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]


class ResponseValidator:
    """Validates API responses against schemas and rules."""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
    
    def validate_response(self, response_data: Dict[str, Any], 
                         expected_schema: Optional[Dict[str, Any]] = None,
                         validation_rules: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate API response data."""
        errors = []
        warnings = []
        
        # Validate JSON schema if provided
        if expected_schema:
            schema_result = self.schema_validator.validate_schema(response_data, expected_schema)
            if not schema_result.valid:
                errors.extend(schema_result.errors)
        
        # Apply custom validation rules
        if validation_rules:
            custom_result = self._validate_custom_rules(response_data, validation_rules)
            if not custom_result.valid:
                errors.extend(custom_result.errors)
                warnings.extend(custom_result.warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_custom_rules(self, data: Dict[str, Any], rules: Dict[str, Any]) -> ValidationResult:
        """Apply custom validation rules."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = rules.get('required_fields', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
        
        # Check field types
        field_types = rules.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if actual_type != expected_type:
                    errors.append(f"Field '{field}' should be {expected_type}, got {actual_type}")
        
        # Check value ranges
        value_ranges = rules.get('value_ranges', {})
        for field, range_config in value_ranges.items():
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    min_val = range_config.get('min')
                    max_val = range_config.get('max')
                    if min_val is not None and value < min_val:
                        errors.append(f"Field '{field}' value {value} is below minimum {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"Field '{field}' value {value} is above maximum {max_val}")
        
        # Check string patterns
        string_patterns = rules.get('string_patterns', {})
        for field, pattern in string_patterns.items():
            if field in data and isinstance(data[field], str):
                import re
                if not re.match(pattern, data[field]):
                    errors.append(f"Field '{field}' does not match pattern {pattern}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class SchemaValidator:
    """Validates data against JSON schemas."""
    
    def __init__(self):
        self.validator = jsonschema.Draft7Validator
    
    def validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """Validate data against a JSON schema."""
        try:
            validator = self.validator(schema)
            errors = []
            
            for error in validator.iter_errors(data):
                errors.append(f"{error.message} at {'.'.join(str(p) for p in error.absolute_path)}")
            
            return ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=[]
            )
            
        except jsonschema.SchemaError as e:
            return ValidationResult(
                valid=False,
                errors=[f"Schema error: {str(e)}"],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    def validate_openapi_schema(self, data: Dict[str, Any], schema_ref: str, 
                              openapi_spec: Dict[str, Any]) -> ValidationResult:
        """Validate data against an OpenAPI schema reference."""
        try:
            # Resolve schema reference
            schema = self._resolve_schema_ref(schema_ref, openapi_spec)
            return self.validate_schema(data, schema)
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"OpenAPI schema validation error: {str(e)}"],
                warnings=[]
            )
    
    def _resolve_schema_ref(self, schema_ref: str, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a schema reference in OpenAPI specification."""
        if not schema_ref.startswith('#/'):
            raise ValueError(f"Invalid schema reference: {schema_ref}")
        
        # Remove the #/ prefix and split the path
        path_parts = schema_ref[2:].split('/')
        
        # Navigate to the schema
        schema = openapi_spec
        for part in path_parts:
            if part not in schema:
                raise ValueError(f"Schema reference not found: {schema_ref}")
            schema = schema[part]
        
        return schema


class ContractValidator:
    """Validates API contract compliance."""
    
    def __init__(self):
        self.response_validator = ResponseValidator()
    
    def validate_contract_compliance(self, endpoint_data: Dict[str, Any], 
                                   openapi_spec: Dict[str, Any]) -> ValidationResult:
        """Validate that API responses comply with OpenAPI contract."""
        errors = []
        warnings = []
        
        # Check if endpoint exists in spec
        path = endpoint_data.get('path')
        method = endpoint_data.get('method')
        
        if not self._endpoint_exists_in_spec(path, method, openapi_spec):
            errors.append(f"Endpoint {method} {path} not found in OpenAPI specification")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # Get endpoint definition
        endpoint_spec = openapi_spec['paths'][path][method.lower()]
        
        # Validate response structure
        response_data = endpoint_data.get('response_data')
        if response_data:
            status_code = str(endpoint_data.get('status_code', 200))
            expected_response = endpoint_spec.get('responses', {}).get(status_code)
            
            if expected_response:
                response_schema = self._extract_response_schema(expected_response)
                if response_schema:
                    validation_result = self.response_validator.validate_response(
                        response_data, response_schema
                    )
                    if not validation_result.valid:
                        errors.extend(validation_result.errors)
                    warnings.extend(validation_result.warnings)
            else:
                warnings.append(f"No response definition found for status code {status_code}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _endpoint_exists_in_spec(self, path: str, method: str, spec: Dict[str, Any]) -> bool:
        """Check if endpoint exists in OpenAPI specification."""
        paths = spec.get('paths', {})
        if path not in paths:
            return False
        
        path_item = paths[path]
        return method.lower() in path_item
    
    def _extract_response_schema(self, response_def: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract JSON schema from response definition."""
        content = response_def.get('content', {})
        json_content = content.get('application/json', {})
        return json_content.get('schema')


class ValidationRule:
    """Represents a custom validation rule."""
    
    def __init__(self, name: str, rule_type: str, config: Dict[str, Any]):
        self.name = name
        self.rule_type = rule_type
        self.config = config
    
    def validate(self, data: Any) -> ValidationResult:
        """Apply the validation rule to data."""
        if self.rule_type == 'required_field':
            return self._validate_required_field(data)
        elif self.rule_type == 'field_type':
            return self._validate_field_type(data)
        elif self.rule_type == 'value_range':
            return self._validate_value_range(data)
        elif self.rule_type == 'string_pattern':
            return self._validate_string_pattern(data)
        elif self.rule_type == 'custom_function':
            return self._validate_custom_function(data)
        else:
            return ValidationResult(
                valid=False,
                errors=[f"Unknown validation rule type: {self.rule_type}"],
                warnings=[]
            )
    
    def _validate_required_field(self, data: Any) -> ValidationResult:
        """Validate that a required field is present."""
        field_name = self.config.get('field_name')
        if isinstance(data, dict) and field_name not in data:
            return ValidationResult(
                valid=False,
                errors=[f"Required field '{field_name}' is missing"],
                warnings=[]
            )
        return ValidationResult(valid=True, errors=[], warnings=[])
    
    def _validate_field_type(self, data: Any) -> ValidationResult:
        """Validate field type."""
        field_name = self.config.get('field_name')
        expected_type = self.config.get('expected_type')
        
        if isinstance(data, dict) and field_name in data:
            actual_type = type(data[field_name]).__name__
            if actual_type != expected_type:
                return ValidationResult(
                    valid=False,
                    errors=[f"Field '{field_name}' should be {expected_type}, got {actual_type}"],
                    warnings=[]
                )
        
        return ValidationResult(valid=True, errors=[], warnings=[])
    
    def _validate_value_range(self, data: Any) -> ValidationResult:
        """Validate value range."""
        field_name = self.config.get('field_name')
        min_val = self.config.get('min')
        max_val = self.config.get('max')
        
        if isinstance(data, dict) and field_name in data:
            value = data[field_name]
            if isinstance(value, (int, float)):
                if min_val is not None and value < min_val:
                    return ValidationResult(
                        valid=False,
                        errors=[f"Field '{field_name}' value {value} is below minimum {min_val}"],
                        warnings=[]
                    )
                if max_val is not None and value > max_val:
                    return ValidationResult(
                        valid=False,
                        errors=[f"Field '{field_name}' value {value} is above maximum {max_val}"],
                        warnings=[]
                    )
        
        return ValidationResult(valid=True, errors=[], warnings=[])
    
    def _validate_string_pattern(self, data: Any) -> ValidationResult:
        """Validate string pattern."""
        field_name = self.config.get('field_name')
        pattern = self.config.get('pattern')
        
        if isinstance(data, dict) and field_name in data:
            value = data[field_name]
            if isinstance(value, str):
                import re
                if not re.match(pattern, value):
                    return ValidationResult(
                        valid=False,
                        errors=[f"Field '{field_name}' does not match pattern {pattern}"],
                        warnings=[]
                    )
        
        return ValidationResult(valid=True, errors=[], warnings=[])
    
    def _validate_custom_function(self, data: Any) -> ValidationResult:
        """Validate using custom function."""
        # This would require dynamic function execution
        # For now, return a placeholder
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=["Custom function validation not implemented"]
        )
