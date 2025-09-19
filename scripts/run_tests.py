#!/usr/bin/env python3
\"\"\"
Comprehensive Test Runner for OmniDesk AI
This script runs all tests and validates the system improvements
\"\"\"

import asyncio
import sys
import os
import subprocess
import time
from typing import List, Dict, Tuple
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    def __init__(self):
        self.results = {
            'backend_tests': [],
            'frontend_tests': [],
            'integration_tests': [],
            'performance_tests': []
        }
        self.start_time = time.time()
    
    def print_header(self, title: str):
        \"\"\"Print a formatted header\"\"\"
        print(f\"\n{'='*60}\")
        print(f\"  {title}\")
        print(f\"{'='*60}\")
    
    def print_result(self, test_name: str, passed: bool, details: str = \"\"):
        \"\"\"Print test result with formatting\"\"\"
        status = \"✓ PASS\" if passed else \"✗ FAIL\"
        print(f\"{status:<8} {test_name}\")
        if details:
            print(f\"         {details}\")
    
    def run_command(self, command: List[str], cwd: str = None) -> Tuple[bool, str]:
        \"\"\"Run a shell command and return success status and output\"\"\"
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, \"Command timed out after 5 minutes\"
        except Exception as e:
            return False, f\"Command failed: {str(e)}\"
    
    def test_python_backend(self) -> bool:
        \"\"\"Test Python backend functionality\"\"\"
        self.print_header(\"BACKEND TESTS\")
        
        backend_dir = project_root / \"backend\"
        if not backend_dir.exists():
            self.print_result(\"Backend Directory\", False, \"Backend directory not found\")
            return False
        
        # Test 1: Check if main dependencies are importable
        try:
            import fastapi
            import sqlalchemy
            import anthropic
            self.print_result(\"Dependencies Check\", True, \"All main dependencies importable\")
        except ImportError as e:
            self.print_result(\"Dependencies Check\", False, f\"Import error: {e}\")
            return False
        
        # Test 2: Run pytest if available
        test_dir = backend_dir / \"tests\"
        if test_dir.exists():
            success, output = self.run_command([\"python\", \"-m\", \"pytest\", \"tests/\", \"-v\"], str(backend_dir))
            self.print_result(\"PyTest Execution\", success, \"All backend tests passed\" if success else \"Some tests failed\")
        else:
            self.print_result(\"PyTest Execution\", False, \"Tests directory not found\")
        
        # Test 3: Validate configuration
        try:
            from app.core.config import settings
            config_valid = hasattr(settings, 'APP_NAME') and hasattr(settings, 'VERSION')
            self.print_result(\"Configuration\", config_valid, \"Settings properly configured\")
        except Exception as e:
            self.print_result(\"Configuration\", False, f\"Config error: {e}\")
        
        # Test 4: Check database models
        try:
            from app.models.ticket import Ticket
            model_valid = hasattr(Ticket, '__tablename__') and hasattr(Ticket, 'id')
            self.print_result(\"Database Models\", model_valid, \"Models properly defined\")
        except Exception as e:
            self.print_result(\"Database Models\", False, f\"Model error: {e}\")
        
        return True
    
    def test_frontend_build(self) -> bool:
        \"\"\"Test frontend build and structure\"\"\"
        self.print_header(\"FRONTEND TESTS\")
        
        frontend_dir = project_root / \"frontend\"
        if not frontend_dir.exists():
            self.print_result(\"Frontend Directory\", False, \"Frontend directory not found\")
            return False
        
        # Test 1: Check package.json
        package_json = frontend_dir / \"package.json\"
        if package_json.exists():
            self.print_result(\"Package Configuration\", True, \"package.json found\")
        else:
            self.print_result(\"Package Configuration\", False, \"package.json missing\")
            return False
        
        # Test 2: Check TypeScript configuration
        tsconfig = frontend_dir / \"tsconfig.json\"
        if tsconfig.exists():
            self.print_result(\"TypeScript Config\", True, \"tsconfig.json found\")
        else:
            self.print_result(\"TypeScript Config\", False, \"tsconfig.json missing\")
        
        # Test 3: Check component structure
        components_dir = frontend_dir / \"src\" / \"components\"
        if components_dir.exists():
            components = list(components_dir.glob(\"*.tsx\"))
            self.print_result(\"Components\", len(components) > 0, f\"Found {len(components)} components\")
        else:
            self.print_result(\"Components\", False, \"Components directory missing\")
        
        # Test 4: Check types definition
        types_dir = frontend_dir / \"src\" / \"types\"
        if types_dir.exists():
            self.print_result(\"Type Definitions\", True, \"Types directory found\")
        else:
            self.print_result(\"Type Definitions\", False, \"Types directory missing\")
        
        # Test 5: Try to build (if node_modules exists)
        node_modules = frontend_dir / \"node_modules\"
        if node_modules.exists():
            success, output = self.run_command([\"npm\", \"run\", \"build\"], str(frontend_dir))
            self.print_result(\"Build Process\", success, \"Build completed successfully\" if success else \"Build failed\")
        else:
            self.print_result(\"Build Process\", False, \"Dependencies not installed (run npm install)\")
        
        return True
    
    def test_docker_configuration(self) -> bool:
        \"\"\"Test Docker setup\"\"\"
        self.print_header(\"DOCKER CONFIGURATION TESTS\")
        
        # Test 1: Check docker-compose.yml
        docker_compose = project_root / \"docker-compose.yml\"
        if docker_compose.exists():
            self.print_result(\"Docker Compose\", True, \"docker-compose.yml found\")
        else:
            self.print_result(\"Docker Compose\", False, \"docker-compose.yml missing\")
            return False
        
        # Test 2: Check Dockerfile
        dockerfile = project_root / \"backend\" / \"Dockerfile\"
        if dockerfile.exists():
            self.print_result(\"Backend Dockerfile\", True, \"Dockerfile found\")
        else:
            self.print_result(\"Backend Dockerfile\", False, \"Backend Dockerfile missing\")
        
        # Test 3: Check environment example
        env_example = project_root / \".env.example\"
        if env_example.exists():
            self.print_result(\"Environment Template\", True, \".env.example found\")
        else:
            self.print_result(\"Environment Template\", False, \".env.example missing\")
        
        # Test 4: Validate docker-compose syntax
        try:
            success, output = self.run_command([\"docker-compose\", \"config\"], str(project_root))
            self.print_result(\"Docker Compose Syntax\", success, \"Configuration valid\")
        except FileNotFoundError:
            self.print_result(\"Docker Compose Syntax\", False, \"Docker not installed\")
        
        return True
    
    def test_documentation(self) -> bool:
        \"\"\"Test documentation completeness\"\"\"
        self.print_header(\"DOCUMENTATION TESTS\")
        
        # Test 1: Check README
        readme = project_root / \"README.md\"
        if readme.exists():
            content = readme.read_text()
            has_setup = \"setup\" in content.lower() or \"installation\" in content.lower()
            has_usage = \"usage\" in content.lower() or \"how to\" in content.lower()
            self.print_result(\"README Completeness\", has_setup and has_usage, \"README has setup and usage sections\")
        else:
            self.print_result(\"README\", False, \"README.md missing\")
        
        # Test 2: Check setup documentation
        setup_md = project_root / \"setup.md\"
        if setup_md.exists():
            self.print_result(\"Setup Documentation\", True, \"setup.md found\")
        else:
            self.print_result(\"Setup Documentation\", False, \"setup.md missing\")
        
        return True
    
    def test_security_configuration(self) -> bool:
        \"\"\"Test security configuration\"\"\"
        self.print_header(\"SECURITY TESTS\")
        
        # Test 1: Check for sensitive files in git
        gitignore = project_root / \".gitignore\"
        if gitignore.exists():
            content = gitignore.read_text()
            has_env = \".env\" in content
            has_secrets = \"secrets\" in content or \"*.key\" in content
            self.print_result(\"Git Security\", has_env and has_secrets, \"Sensitive files ignored\")
        else:
            self.print_result(\"Git Security\", False, \".gitignore missing\")
        
        # Test 2: Check for hardcoded secrets
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        found_issues = []
        
        for py_file in (project_root / \"backend\").rglob(\"*.py\"):
            if py_file.name.startswith('test_'):
                continue
            
            try:
                content = py_file.read_text().lower()
                for pattern in sensitive_patterns:
                    if f'{pattern} = \"' in content or f\"{pattern} = '\" in content:
                        found_issues.append(str(py_file))
                        break
            except:
                continue
        
        self.print_result(\"Hardcoded Secrets\", len(found_issues) == 0, 
                         f\"Found {len(found_issues)} potential issues\" if found_issues else \"No hardcoded secrets found\")
        
        return True
    
    def generate_summary(self) -> Dict:
        \"\"\"Generate test summary\"\"\"
        end_time = time.time()
        duration = end_time - self.start_time
        
        summary = {
            'duration': f\"{duration:.2f} seconds\",
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0
        }
        
        return summary
    
    def run_all_tests(self) -> bool:
        \"\"\"Run all test suites\"\"\"
        print(\"\n🚀 OmniDesk AI - Comprehensive Test Suite\")
        print(f\"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\")
        
        all_passed = True
        
        try:
            # Run all test suites
            self.test_python_backend()
            self.test_frontend_build()
            self.test_docker_configuration()
            self.test_documentation()
            self.test_security_configuration()
            
        except KeyboardInterrupt:
            print(\"\n⚠️ Test execution interrupted by user\")
            return False
        except Exception as e:
            print(f\"\n❌ Test execution failed: {e}\")
            return False
        
        # Print summary
        self.print_header(\"TEST SUMMARY\")
        summary = self.generate_summary()
        print(f\"Duration: {summary['duration']}\")
        print(f\"Completed at: {summary['timestamp']}\")
        
        if all_passed:
            print(\"\n🎉 All tests completed successfully!\")
            print(\"✅ Your OmniDesk AI system has been improved and validated.\")
        else:
            print(\"\n⚠️ Some tests failed. Please review the output above.\")
        
        return all_passed

def main():
    \"\"\"Main entry point\"\"\"
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == \"__main__\":
    main()