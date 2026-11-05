#!/usr/bin/env python3
"""
InvoiceFlow Pro - Complete Test Runner
Runs all tests: unit, integration, API, frontend, and performance tests
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"
        self.results = {
            'backend_unit_tests': None,
            'frontend_tests': None,
            'api_tests': None,
            'integration_tests': None,
            'performance_tests': None
        }
        self.start_time = datetime.now()

    def run_command(self, command, description, cwd=None, capture=True):
        """Run a command and capture results"""
        print(f"\n🔧 {description}...")
        print(f"   Command: {command}")
        
        try:
            if capture:
                result = subprocess.run(
                    command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=300  # 5 minute timeout
                )
                return True, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    check=True,
                    cwd=cwd,
                    timeout=300
                )
                return True, "", ""
        except subprocess.CalledProcessError as e:
            return False, e.stdout if e.stdout else "", e.stderr if e.stderr else str(e)
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 5 minutes"

    def run_backend_unit_tests(self):
        """Run backend unit tests with pytest"""
        print("\n" + "="*50)
        print("🐍 Running Backend Unit Tests")
        print("="*50)
        
        # Check if tests directory exists
        tests_dir = self.backend_path / "tests"
        if not tests_dir.exists():
            print("⚠️  No tests directory found, creating basic test structure...")
            tests_dir.mkdir()
            (tests_dir / "__init__.py").touch()
            
            # Create a basic test file
            basic_test = """
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200
"""
            with open(tests_dir / "test_basic.py", "w") as f:
                f.write(basic_test)
        
        # Run pytest
        venv_python = self.get_python_executable()
        success, stdout, stderr = self.run_command(
            f"{venv_python} -m pytest tests/ -v --tb=short --junitxml=test-results.xml",
            "Running pytest",
            self.backend_path
        )
        
        self.results['backend_unit_tests'] = {
            'success': success,
            'output': stdout,
            'errors': stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            print("✅ Backend unit tests passed")
        else:
            print("❌ Backend unit tests failed")
            print(f"Errors: {stderr}")

    def run_frontend_tests(self):
        """Run frontend tests with Jest"""
        print("\n" + "="*50)
        print("⚛️  Running Frontend Tests")
        print("="*50)
        
        # Check if test files exist
        test_dir = self.frontend_path / "src" / "__tests__"
        if not test_dir.exists():
            print("⚠️  No frontend tests found")
            self.results['frontend_tests'] = {
                'success': False,
                'output': '',
                'errors': 'No test files found',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        success, stdout, stderr = self.run_command(
            "npm test -- --coverage --watchAll=false --passWithNoTests",
            "Running Jest tests",
            self.frontend_path
        )
        
        self.results['frontend_tests'] = {
            'success': success,
            'output': stdout,
            'errors': stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            print("✅ Frontend tests passed")
        else:
            print("❌ Frontend tests failed")
            print(f"Errors: {stderr}")

    def run_api_tests(self):
        """Run comprehensive API tests"""
        print("\n" + "="*50)
        print("🌐 Running API Integration Tests")
        print("="*50)
        
        # Check if backend server is running
        import requests
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            if response.status_code != 200:
                print("❌ Backend server not running at http://localhost:8000")
                print("   Please start the backend server first:")
                print(f"   cd {self.backend_path}")
                print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
                self.results['api_tests'] = {
                    'success': False,
                    'output': '',
                    'errors': 'Backend server not running',
                    'timestamp': datetime.now().isoformat()
                }
                return
        except requests.exceptions.RequestException:
            print("❌ Cannot connect to backend server")
            self.results['api_tests'] = {
                'success': False,
                'output': '',
                'errors': 'Cannot connect to backend server',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        # Run API test script
        venv_python = self.get_python_executable()
        test_script = self.project_root / "scripts" / "test_api.py"
        
        if not test_script.exists():
            print("❌ API test script not found")
            self.results['api_tests'] = {
                'success': False,
                'output': '',
                'errors': 'API test script not found',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        success, stdout, stderr = self.run_command(
            f"{venv_python} scripts/test_api.py",
            "Running API tests",
            self.project_root
        )
        
        self.results['api_tests'] = {
            'success': success,
            'output': stdout,
            'errors': stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            print("✅ API tests completed")
        else:
            print("❌ API tests failed")
            print(f"Errors: {stderr}")

    def run_performance_tests(self):
        """Run basic performance tests"""
        print("\n" + "="*50)
        print("⚡ Running Performance Tests")
        print("="*50)
        
        # Simple performance test using curl
        import requests
        import time
        
        try:
            # Test API response times
            endpoints = [
                "http://localhost:8000/docs",
                "http://localhost:8000/health",
                "http://localhost:8000/api/v1/auth/login"  # This will fail but we just want response time
            ]
            
            response_times = []
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=10)
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    response_times.append({
                        'endpoint': endpoint,
                        'response_time_ms': round(response_time, 2),
                        'status_code': response.status_code
                    })
                except requests.exceptions.RequestException as e:
                    response_times.append({
                        'endpoint': endpoint,
                        'response_time_ms': None,
                        'error': str(e)
                    })
            
            # Calculate average response time for successful requests
            successful_times = [r['response_time_ms'] for r in response_times if r.get('response_time_ms')]
            avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
            
            performance_passed = avg_response_time < 1000  # Less than 1 second average
            
            self.results['performance_tests'] = {
                'success': performance_passed,
                'output': json.dumps(response_times, indent=2),
                'errors': '' if performance_passed else f'Average response time too high: {avg_response_time}ms',
                'timestamp': datetime.now().isoformat(),
                'average_response_time_ms': round(avg_response_time, 2)
            }
            
            if performance_passed:
                print(f"✅ Performance tests passed (avg: {avg_response_time:.2f}ms)")
            else:
                print(f"❌ Performance tests failed (avg: {avg_response_time:.2f}ms)")
            
        except Exception as e:
            self.results['performance_tests'] = {
                'success': False,
                'output': '',
                'errors': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"❌ Performance tests failed: {e}")

    def get_python_executable(self):
        """Get the correct Python executable (with or without venv)"""
        if os.name == 'nt':  # Windows
            venv_python = self.backend_path / "venv" / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            venv_python = self.backend_path / "venv" / "bin" / "python"
        
        if venv_python.exists():
            return str(venv_python)
        else:
            return "python"

    def check_environment(self):
        """Check if the environment is properly set up"""
        print("🔍 Checking Test Environment...")
        
        issues = []
        
        # Check backend dependencies
        venv_python = self.get_python_executable()
        success, stdout, stderr = self.run_command(
            f"{venv_python} -c 'import fastapi, sqlalchemy, pytest'",
            "Check backend dependencies",
            self.backend_path
        )
        if not success:
            issues.append("Backend dependencies missing")
        
        # Check frontend dependencies
        if (self.frontend_path / "node_modules").exists():
            print("✅ Frontend dependencies installed")
        else:
            issues.append("Frontend dependencies missing (run npm install)")
        
        # Check database connection
        success, stdout, stderr = self.run_command(
            f"{venv_python} -c 'from app.core.database import engine; engine.connect()'",
            "Check database connection",
            self.backend_path
        )
        if not success:
            issues.append("Database connection failed")
        
        if issues:
            print("❌ Environment issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Environment check passed")
            return True

    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*60)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        # Summary
        total_tests = len([r for r in self.results.values() if r is not None])
        passed_tests = len([r for r in self.results.values() if r and r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Test Summary:")
        print(f"   Total Test Suites: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   Total Duration: {duration}")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.results.items():
            if result is None:
                print(f"   🚫 {test_name}: Skipped")
            elif result['success']:
                print(f"   ✅ {test_name}: Passed")
            else:
                print(f"   ❌ {test_name}: Failed")
                if result['errors']:
                    # Show first few lines of error
                    error_lines = result['errors'].split('\n')[:3]
                    for line in error_lines:
                        if line.strip():
                            print(f"      {line[:100]}")
        
        # Performance metrics
        if self.results['performance_tests'] and self.results['performance_tests']['success']:
            avg_time = self.results['performance_tests'].get('average_response_time_ms', 0)
            print(f"\n⚡ Performance Metrics:")
            print(f"   Average API Response Time: {avg_time}ms")
        
        # Save detailed report
        report_data = {
            'summary': {
                'total_suites': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests/total_tests)*100 if total_tests > 0 else 0,
                'duration_seconds': duration.total_seconds(),
                'timestamp': end_time.isoformat()
            },
            'results': self.results
        }
        
        report_file = self.project_root / "test_report_comprehensive.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if failed_tests > 0:
            print("   - Fix failing tests before deployment")
            print("   - Check error details in the JSON report")
        
        if self.results['performance_tests'] and not self.results['performance_tests']['success']:
            print("   - Investigate performance issues")
            print("   - Consider optimizing slow endpoints")
        
        print("\n🎯 Next Steps:")
        print("   1. Review failed tests and fix issues")
        print("   2. Ensure all tests pass before deployment")
        print("   3. Run tests regularly during development")
        print("   4. Set up CI/CD pipeline for automated testing")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 InvoiceFlow Pro - Comprehensive Test Suite")
        print("=" * 60)
        print(f"Started at: {self.start_time}")
        
        # Check environment first
        if not self.check_environment():
            print("❌ Environment check failed. Please fix issues before running tests.")
            return
        
        try:
            # Run all test suites
            self.run_backend_unit_tests()
            self.run_frontend_tests()
            self.run_api_tests()
            self.run_performance_tests()
            
        except KeyboardInterrupt:
            print("\n⚡ Tests interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
        finally:
            # Always generate report
            self.generate_report()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='InvoiceFlow Pro Comprehensive Test Runner')
    parser.add_argument('--backend-only', action='store_true', help='Run only backend tests')
    parser.add_argument('--frontend-only', action='store_true', help='Run only frontend tests')
    parser.add_argument('--api-only', action='store_true', help='Run only API tests')
    parser.add_argument('--performance-only', action='store_true', help='Run only performance tests')
    parser.add_argument('--skip-env-check', action='store_true', help='Skip environment check')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.backend_only:
        runner.run_backend_unit_tests()
        runner.generate_report()
    elif args.frontend_only:
        runner.run_frontend_tests()
        runner.generate_report()
    elif args.api_only:
        runner.run_api_tests()
        runner.generate_report()
    elif args.performance_only:
        runner.run_performance_tests()
        runner.generate_report()
    else:
        runner.run_all_tests()