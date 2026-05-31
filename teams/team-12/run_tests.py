# -*- coding: utf-8 -*-
"""
Test Runner Script for DataCleanAgent.
Discovers and executes all unit tests in the 'tests' directory.
Exits with code 0 on success, or code 1 on failure.
"""

import sys
import unittest

def run_all_tests():
    print("======================================================================")
    print("       DataCleanAgent Automated Test Suite Execution")
    print("======================================================================")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n======================================================================")
    print("                      Test execution summary")
    print("======================================================================")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("======================================================================")
    
    if not result.wasSuccessful():
        print(" verdict: FAIL")
        sys.exit(1)
    else:
        print(" verdict: SUCCESS")
        sys.exit(0)

if __name__ == '__main__':
    run_all_tests()
