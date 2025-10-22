"""
Test execution engine for BATMAN API Testing Framework.
"""

import os
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


@dataclass
class TestResult:
    """Represents the result of a test execution."""
    test_file: str
    success: bool
    output: str
    duration: float
    exit_code: int
    error_message: Optional[str] = None


@dataclass
class ExecutionResults:
    """Aggregated test execution results."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    results: List[TestResult]
    success: bool


class TestExecutor:
    """Executes BATS tests with support for parallel execution."""
    
    def __init__(self):
        self.results = []
        self.start_time = None
    
    def run_tests(self, config: Dict[str, Any], docker: bool = False, 
                  parallel: bool = False, verbose: bool = False) -> ExecutionResults:
        """Run BATS tests based on configuration."""
        self.start_time = time.time()
        
        # Get execution configuration
        execution_config = config.get('execution', {})
        test_config = config.get('test_generation', {})
        
        output_dir = Path(test_config.get('output_dir', 'generated/tests'))
        max_parallel = execution_config.get('max_parallel', 4)
        timeout = execution_config.get('timeout', 300)
        
        # Find test files
        test_files = self._find_test_files(output_dir)
        
        if not test_files:
            raise ValueError(f"No test files found in {output_dir}")
        
        # Setup environment
        self._setup_environment(config)
        
        # Execute tests
        if docker:
            results = self._run_docker_tests(config, test_files, verbose)
        elif parallel:
            results = self._run_parallel_tests(test_files, max_parallel, timeout, verbose)
        else:
            results = self._run_sequential_tests(test_files, timeout, verbose)
        
        # Calculate summary
        total_duration = time.time() - self.start_time
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = len(results) - passed_tests
        
        return ExecutionResults(
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_duration=total_duration,
            results=results,
            success=failed_tests == 0
        )
    
    def _find_test_files(self, output_dir: Path) -> List[Path]:
        """Find all BATS test files in the output directory."""
        test_files = []
        
        if output_dir.exists():
            # Find .bats files
            for pattern in ['*.bats', '**/*.bats']:
                test_files.extend(output_dir.glob(pattern))
        
        return sorted(test_files)
    
    def _setup_environment(self, config: Dict[str, Any]) -> None:
        """Setup environment variables for test execution."""
        target_api = config.get('target_api', {})
        
        # Set API base URL
        os.environ['API_BASE_URL'] = target_api.get('base_url', '')
        
        # Set authentication
        auth = target_api.get('auth')
        if auth:
            if auth.get('type') == 'bearer' and auth.get('token'):
                os.environ['AUTH_TOKEN'] = auth['token']
            elif auth.get('type') == 'basic':
                if auth.get('username'):
                    os.environ['AUTH_USERNAME'] = auth['username']
                if auth.get('password'):
                    os.environ['AUTH_PASSWORD'] = auth['password']
            elif auth.get('type') == 'api_key':
                if auth.get('api_key'):
                    os.environ['API_KEY'] = auth['api_key']
                if auth.get('api_key_header'):
                    os.environ['API_KEY_HEADER'] = auth['api_key_header']
        
        # Set timeout
        os.environ['TIMEOUT'] = str(target_api.get('timeout', 30))
        
        # Set retries
        os.environ['MAX_RETRIES'] = str(target_api.get('retries', 3))
    
    def _run_sequential_tests(self, test_files: List[Path], timeout: int, verbose: bool) -> List[TestResult]:
        """Run tests sequentially."""
        results = []
        
        for test_file in test_files:
            result = self._run_single_test(test_file, timeout, verbose)
            results.append(result)
            
            if verbose:
                self._print_test_result(result)
        
        return results
    
    def _run_parallel_tests(self, test_files: List[Path], max_parallel: int, 
                           timeout: int, verbose: bool) -> List[TestResult]:
        """Run tests in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self._run_single_test, test_file, timeout, verbose): test_file
                for test_file in test_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_test):
                test_file = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if verbose:
                        self._print_test_result(result)
                except Exception as e:
                    # Handle unexpected errors
                    error_result = TestResult(
                        test_file=str(test_file),
                        success=False,
                        output="",
                        duration=0.0,
                        exit_code=1,
                        error_message=str(e)
                    )
                    results.append(error_result)
        
        return results
    
    def _run_docker_tests(self, config: Dict[str, Any], test_files: List[Path], verbose: bool) -> List[TestResult]:
        """Run tests using Docker."""
        docker_config = config.get('docker', {})
        
        if not docker_config.get('enabled', False):
            raise ValueError("Docker is not enabled in configuration")
        
        # Generate Docker Compose file if needed
        compose_file = docker_config.get('compose_file', 'docker-compose.yml')
        if not Path(compose_file).exists():
            from .generator import TestGenerator
            generator = TestGenerator()
            generator.generate_docker_compose(config)
        
        # Run Docker Compose
        try:
            cmd = ['docker-compose', '-f', compose_file, 'up', '--build', '--abort-on-container-exit']
            
            if verbose:
                print(f"Running Docker command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.get('execution', {}).get('timeout', 300)
            )
            
            # Parse Docker output
            docker_result = TestResult(
                test_file="docker-compose",
                success=result.returncode == 0,
                output=result.stdout,
                duration=0.0,  # Duration not easily extractable from Docker
                exit_code=result.returncode,
                error_message=result.stderr if result.returncode != 0 else None
            )
            
            return [docker_result]
            
        except subprocess.TimeoutExpired:
            return [TestResult(
                test_file="docker-compose",
                success=False,
                output="",
                duration=0.0,
                exit_code=1,
                error_message="Docker execution timed out"
            )]
        except Exception as e:
            return [TestResult(
                test_file="docker-compose",
                success=False,
                output="",
                duration=0.0,
                exit_code=1,
                error_message=str(e)
            )]
    
    def _run_single_test(self, test_file: Path, timeout: int, verbose: bool) -> TestResult:
        """Run a single BATS test file."""
        start_time = time.time()
        
        try:
            # Check if BATS is available
            if not self._check_bats_available():
                raise RuntimeError("BATS is not installed or not available in PATH")
            
            # Run the test
            cmd = ['bats', str(test_file)]
            
            if verbose:
                print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=test_file.parent
            )
            
            duration = time.time() - start_time
            
            return TestResult(
                test_file=str(test_file),
                success=result.returncode == 0,
                output=result.stdout,
                duration=duration,
                exit_code=result.returncode,
                error_message=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                test_file=str(test_file),
                success=False,
                output="",
                duration=duration,
                exit_code=1,
                error_message=f"Test timed out after {timeout} seconds"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_file=str(test_file),
                success=False,
                output="",
                duration=duration,
                exit_code=1,
                error_message=str(e)
            )
    
    def _check_bats_available(self) -> bool:
        """Check if BATS is available in the system."""
        try:
            result = subprocess.run(['bats', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _print_test_result(self, result: TestResult) -> None:
        """Print test result to console."""
        status = "✓ PASS" if result.success else "✗ FAIL"
        print(f"{status} {result.test_file} ({result.duration:.2f}s)")
        
        if not result.success and result.error_message:
            print(f"  Error: {result.error_message}")
    
    def generate_report(self, results: ExecutionResults, config: Dict[str, Any]) -> None:
        """Generate test reports in various formats."""
        reporting_config = config.get('reporting', {})
        formats = reporting_config.get('format', ['console'])
        output_dir = Path(reporting_config.get('output_dir', 'reports'))
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for format_type in formats:
            if format_type == 'json':
                self._generate_json_report(results, output_dir)
            elif format_type == 'junit':
                self._generate_junit_report(results, output_dir)
            elif format_type == 'html':
                self._generate_html_report(results, output_dir)
            elif format_type == 'console':
                self._print_console_report(results)
    
    def _generate_json_report(self, results: ExecutionResults, output_dir: Path) -> None:
        """Generate JSON report."""
        report_data = {
            'summary': {
                'total_tests': results.total_tests,
                'passed_tests': results.passed_tests,
                'failed_tests': results.failed_tests,
                'total_duration': results.total_duration,
                'success': results.success
            },
            'results': [
                {
                    'test_file': r.test_file,
                    'success': r.success,
                    'duration': r.duration,
                    'exit_code': r.exit_code,
                    'error_message': r.error_message
                }
                for r in results.results
            ]
        }
        
        report_file = output_dir / 'test-report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def _generate_junit_report(self, results: ExecutionResults, output_dir: Path) -> None:
        """Generate JUnit XML report."""
        # Simplified JUnit XML generation
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="BATMAN API Tests" tests="{results.total_tests}" failures="{results.failed_tests}" time="{results.total_duration:.2f}">
'''
        
        for result in results.results:
            test_name = Path(result.test_file).stem
            xml_content += f'  <testcase name="{test_name}" time="{result.duration:.2f}">\n'
            
            if not result.success:
                xml_content += f'    <failure message="{result.error_message or "Test failed"}"/>\n'
            
            xml_content += '  </testcase>\n'
        
        xml_content += '</testsuite>'
        
        report_file = output_dir / 'test-report.xml'
        with open(report_file, 'w') as f:
            f.write(xml_content)
    
    def _generate_html_report(self, results: ExecutionResults, output_dir: Path) -> None:
        """Generate HTML report."""
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>BATMAN API Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .test-result.pass {{ border-left-color: green; }}
        .test-result.fail {{ border-left-color: red; }}
    </style>
</head>
<body>
    <h1>BATMAN API Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {results.total_tests}</p>
        <p class="pass">Passed: {results.passed_tests}</p>
        <p class="fail">Failed: {results.failed_tests}</p>
        <p>Duration: {results.total_duration:.2f}s</p>
    </div>
    <h2>Test Results</h2>
'''
        
        for result in results.results:
            status_class = "pass" if result.success else "fail"
            html_content += f'''
    <div class="test-result {status_class}">
        <h3>{Path(result.test_file).name}</h3>
        <p>Duration: {result.duration:.2f}s</p>
        <p>Status: {"PASS" if result.success else "FAIL"}</p>
'''
            
            if not result.success and result.error_message:
                html_content += f'        <p>Error: {result.error_message}</p>\n'
            
            html_content += '    </div>\n'
        
        html_content += '''
</body>
</html>
'''
        
        report_file = output_dir / 'test-report.html'
        with open(report_file, 'w') as f:
            f.write(html_content)
    
    def _print_console_report(self, results: ExecutionResults) -> None:
        """Print console report."""
        print("\n" + "="*50)
        print("BATMAN API Test Report")
        print("="*50)
        print(f"Total Tests: {results.total_tests}")
        print(f"Passed: {results.passed_tests}")
        print(f"Failed: {results.failed_tests}")
        print(f"Duration: {results.total_duration:.2f}s")
        print("="*50)
        
        if results.failed_tests > 0:
            print("\nFailed Tests:")
            for result in results.results:
                if not result.success:
                    print(f"  ✗ {Path(result.test_file).name}")
                    if result.error_message:
                        print(f"    Error: {result.error_message}")
        
        print(f"\nOverall Result: {'PASS' if results.success else 'FAIL'}")
