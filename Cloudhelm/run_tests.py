#!/usr/bin/env python3
"""
Test runner script for CloudHelm.
Runs both backend and frontend tests.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list, cwd: str = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(command, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return 1


def main():
    """Main test runner."""
    print("🧪 CloudHelm Test Runner")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Track results
    results = {}
    
    # Run backend tests
    print("\n📦 Running Backend Tests (Python/pytest)")
    print("-" * 40)
    
    if backend_dir.exists():
        # Check if pytest is available
        pytest_check = run_command(["python", "-m", "pytest", "--version"], str(backend_dir))
        
        if pytest_check == 0:
            # Run pytest
            backend_result = run_command([
                "python", "-m", "pytest", 
                "tests/", 
                "-v", 
                "--tb=short",
                "--cov=.",
                "--cov-report=term-missing"
            ], str(backend_dir))
            results["backend"] = backend_result
        else:
            print("❌ pytest not found. Install with: pip install pytest")
            results["backend"] = 1
    else:
        print("❌ Backend directory not found")
        results["backend"] = 1
    
    # Run frontend tests
    print("\n🌐 Running Frontend Tests (TypeScript/Vitest)")
    print("-" * 40)
    
    if frontend_dir.exists():
        # Check if npm is available
        npm_check = run_command(["npm", "--version"], str(frontend_dir))
        
        if npm_check == 0:
            # Install dependencies if needed
            if not (frontend_dir / "node_modules").exists():
                print("📦 Installing frontend dependencies...")
                install_result = run_command(["npm", "install"], str(frontend_dir))
                if install_result != 0:
                    print("❌ Failed to install frontend dependencies")
                    results["frontend"] = 1
                    return print_results(results)
            
            # Run tests
            frontend_result = run_command(["npm", "run", "test:run"], str(frontend_dir))
            results["frontend"] = frontend_result
        else:
            print("❌ npm not found. Install Node.js first")
            results["frontend"] = 1
    else:
        print("❌ Frontend directory not found")
        results["frontend"] = 1
    
    # Print results
    print_results(results)
    
    # Exit with error if any tests failed
    if any(code != 0 for code in results.values()):
        sys.exit(1)


def print_results(results: dict):
    """Print test results summary."""
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    for component, exit_code in results.items():
        status = "✅ PASSED" if exit_code == 0 else "❌ FAILED"
        print(f"{component.capitalize()}: {status}")
    
    total_passed = sum(1 for code in results.values() if code == 0)
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
    
    if all(code == 0 for code in results.values()):
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()