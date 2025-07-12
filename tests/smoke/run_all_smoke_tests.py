#!/usr/bin/env python3
"""
Master Smoke Test Runner for Grocery Genie

Runs all smoke tests in the proper order and provides comprehensive reporting.
Supports both local development and CI/CD environments.

Author: AI Agent
Date: 2025-07-12
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

# Configure logging with bright colors
logging.basicConfig(
    level=logging.INFO,
    format='🚀 %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SmokeTestRunner:
    """Master smoke test runner"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent
        self.results = {}
        self.start_time = datetime.now()
        
        # Define smoke tests in execution order
        self.smoke_tests = [
            {
                'name': 'Receipt Matcher',
                'file': 'test_receipt_matcher_smoke.py',
                'description': 'Tests receipt matching system end-to-end',
                'required_env': None
            },
            {
                'name': 'Other Purchases Loader',
                'file': 'test_other_purchases_smoke.py',
                'description': 'Tests other purchases data loading and validation',
                'required_env': None
            }
        ]
    
    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("🧪 GROCERY GENIE SMOKE TEST SUITE")
        print("=" * 80)
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 Environment: {os.getenv('ENV', 'development')}")
        print(f"📁 Test Directory: {self.test_dir}")
        print(f"📁 Project Root: {self.project_root}")
        print("=" * 80)
    
    def check_environment(self, test_config):
        """Check if environment requirements are met"""
        required_env = test_config.get('required_env')
        if required_env:
            current_env = os.getenv('ENV', '').lower()
            if current_env != required_env:
                logger.warning(f"⚠️  Test {test_config['name']} requires ENV={required_env}, current: {current_env}")
                return False
        return True
    
    def run_single_test(self, test_config):
        """Run a single smoke test"""
        test_name = test_config['name']
        test_file = test_config['file']
        test_path = self.test_dir / test_file
        
        logger.info(f"🔍 Starting: {test_name}")
        logger.info(f"📄 Description: {test_config['description']}")
        
        # Check if test file exists
        if not test_path.exists():
            logger.error(f"❌ Test file not found: {test_path}")
            return False
        
        # Check environment requirements
        if not self.check_environment(test_config):
            logger.warning(f"⏭️  Skipping {test_name} due to environment requirements")
            return None  # None indicates skipped
        
        try:
            # Run the test
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()
            duration = end_time - start_time
            
            # Store results
            self.results[test_name] = {
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {test_name} PASSED ({duration:.1f}s)")
                return True
            else:
                logger.error(f"❌ {test_name} FAILED ({duration:.1f}s)")
                logger.error(f"Return code: {result.returncode}")
                if result.stderr:
                    logger.error(f"STDERR:\n{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {test_name} TIMED OUT (>300s)")
            self.results[test_name] = {
                'success': False,
                'duration': 300,
                'stdout': '',
                'stderr': 'Test timed out after 300 seconds',
                'returncode': -1
            }
            return False
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
            self.results[test_name] = {
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e),
                'returncode': -2
            }
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 SMOKE TEST SUMMARY")
        print("=" * 80)
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, result in self.results.items():
            if result['success']:
                status = "✅ PASSED"
                passed += 1
            else:
                status = "❌ FAILED"
                failed += 1
            
            print(f"{status:12} {test_name:25} ({result['duration']:.1f}s)")
        
        # Count skipped tests
        skipped = len(self.smoke_tests) - len(self.results)
        
        print("-" * 80)
        print(f"📈 Results: {passed} passed, {failed} failed, {skipped} skipped")
        print(f"⏱️  Total Duration: {total_duration:.1f}s")
        print(f"🏁 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print detailed failure information
        if failed > 0:
            print("\n" + "🔍 FAILURE DETAILS:")
            print("-" * 80)
            for test_name, result in self.results.items():
                if not result['success']:
                    print(f"\n❌ {test_name}:")
                    print(f"   Return Code: {result['returncode']}")
                    if result['stderr']:
                        print(f"   Error Output:\n{result['stderr']}")
                    if result['stdout']:
                        print(f"   Standard Output:\n{result['stdout']}")
        
        print("=" * 80)
        
        return failed == 0
    
    def run_all_tests(self):
        """Run all smoke tests"""
        self.print_header()
        
        overall_success = True
        
        for test_config in self.smoke_tests:
            print("\n" + "-" * 50)
            result = self.run_single_test(test_config)
            
            if result is False:  # Failed
                overall_success = False
            # result is None means skipped, which doesn't affect overall success
        
        success = self.print_summary()
        return success and overall_success

def main():
    """Main entry point"""
    runner = SmokeTestRunner()
    
    try:
        success = runner.run_all_tests()
        
        if success:
            logger.info("🎉 All smoke tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Some smoke tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️  Smoke tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Smoke test runner crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
