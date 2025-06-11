#!/usr/bin/env python3
"""
Simple test runner for Kaia Kubernetes AI Assistant

This runner works with Python's built-in unittest framework if pytest is not available.

Usage:
    python3 run_tests.py              # Run all tests
    python3 run_tests.py --verbose    # Run with verbose output  
    python3 run_tests.py --help       # Show help
"""

import sys
import os
import argparse
import importlib.util

def run_with_unittest():
    """Run tests using Python's built-in unittest framework."""
    import unittest
    
    # Import the tests module
    import tests
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Load all test classes
    suite = unittest.TestSuite()
    
    # Add all test classes from tests module
    test_classes = [
        tests.TestArgumentParsing,
        tests.TestModelCreation,
        tests.TestEnvironmentVariables,
        tests.TestIntegration,
        tests.TestErrorHandling
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    return suite

def run_with_pytest():
    """Run tests using pytest if available."""
    import subprocess
    
    cmd = ['python3', '-m', 'pytest', 'tests.py', '-v']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='Run tests for Kaia')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--use-unittest', action='store_true',
                       help='Force use of unittest instead of pytest')
    
    args = parser.parse_args()
    
    # Try to use pytest first, fall back to unittest
    use_pytest = True
    if args.use_unittest:
        use_pytest = False
    else:
        try:
            import pytest
        except ImportError:
            print("pytest not found, falling back to unittest framework")
            use_pytest = False
    
    if use_pytest:
        try:
            return run_with_pytest()
        except Exception as e:
            print(f"Error running pytest: {e}")
            print("Falling back to unittest framework")
            use_pytest = False
    
    if not use_pytest:
        # Use unittest
        try:
            suite = run_with_unittest()
            runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
            result = runner.run(suite)
            
            # Return appropriate exit code
            return 0 if result.wasSuccessful() else 1
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 
