"""
BATMAN - API Testing Framework

A standalone, configuration-driven testing solution that automatically generates
and executes BATS (Bash Automated Testing System) integration tests for any API
based on its OpenAPI specification.
"""

__version__ = "1.0.0"
__author__ = "BATMAN Team"
__email__ = "team@batman-testing.com"

from .cli import main

__all__ = ["main"]
