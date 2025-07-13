#!/usr/bin/env python3
"""
Comprehensive Test Runner for Receipt Matcher System

Runs all tests (unit tests, integration tests, smoke tests) and provides
a comprehensive report of the system's health and readiness.

Author: AI Agent
Date: 2025-07-11
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path

# Configure logging with bright colors
logging.basicConfig(level=logging.INFO, format="🧪 %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """Runs all tests for the receipt matcher system"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.test_results = {}

    def run_unit_tests(self):
        """Run unit tests"""
        logger.info("🔬 RUNNING UNIT TESTS")
        logger.info("=" * 50)

        try:
            unit_test_script = self.script_dir / "test_receipt_matcher_unit.py"

            if not unit_test_script.exists():
                logger.error(f"❌ UNIT TEST SCRIPT NOT FOUND: {unit_test_script}")
                return False

            # Run unit tests
            result = subprocess.run(
                [sys.executable, str(unit_test_script)], capture_output=True, text=True, timeout=120
            )

            # Log output
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        logger.info(f"📝 {line}")

            if result.stderr:
                for line in result.stderr.split("\n"):
                    if line.strip():
                        logger.error(f"⚠️  {line}")

            if result.returncode == 0:
                logger.info("✅ UNIT TESTS PASSED")
                return True
            else:
                logger.error(f"❌ UNIT TESTS FAILED (exit code: {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ UNIT TESTS TIMED OUT")
            return False
        except Exception as e:
            logger.error(f"❌ UNIT TESTS ERROR: {e}")
            return False

    def run_integration_tests(self):
        """Run integration tests (existing test_receipt_matcher.py)"""
        logger.info("🔗 RUNNING INTEGRATION TESTS")
        logger.info("=" * 50)

        try:
            integration_test_script = self.script_dir / "test_receipt_matcher.py"

            if not integration_test_script.exists():
                logger.error(f"❌ INTEGRATION TEST SCRIPT NOT FOUND: {integration_test_script}")
                return False

            # Run integration tests
            result = subprocess.run(
                [sys.executable, str(integration_test_script)],
                capture_output=True,
                text=True,
                timeout=180,
            )

            # Log key output lines
            if result.stdout:
                lines = result.stdout.split("\n")
                for line in lines:
                    if any(
                        keyword in line for keyword in ["✅", "❌", "PASSED", "FAILED", "SUMMARY"]
                    ):
                        logger.info(f"📝 {line}")

            if result.stderr:
                for line in result.stderr.split("\n"):
                    if line.strip():
                        logger.error(f"⚠️  {line}")

            if result.returncode == 0:
                logger.info("✅ INTEGRATION TESTS PASSED")
                return True
            else:
                logger.error(f"❌ INTEGRATION TESTS FAILED (exit code: {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ INTEGRATION TESTS TIMED OUT")
            return False
        except Exception as e:
            logger.error(f"❌ INTEGRATION TESTS ERROR: {e}")
            return False

    def run_smoke_tests(self):
        """Run smoke tests"""
        logger.info("🔥 RUNNING SMOKE TESTS")
        logger.info("=" * 50)

        try:
            smoke_test_script = (
                self.script_dir / "tests" / "smoke" / "test_receipt_matcher_smoke.py"
            )

            if not smoke_test_script.exists():
                logger.error(f"❌ SMOKE TEST SCRIPT NOT FOUND: {smoke_test_script}")
                return False

            # Run smoke tests
            result = subprocess.run(
                [sys.executable, str(smoke_test_script)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for smoke tests
            )

            # Log key output lines
            if result.stdout:
                lines = result.stdout.split("\n")
                for line in lines:
                    if any(
                        keyword in line
                        for keyword in ["✅", "❌", "PASSED", "FAILED", "SUMMARY", "TOTAL:"]
                    ):
                        logger.info(f"📝 {line}")

            if result.stderr:
                for line in result.stderr.split("\n"):
                    if line.strip():
                        logger.error(f"⚠️  {line}")

            if result.returncode == 0:
                logger.info("✅ SMOKE TESTS PASSED")
                return True
            else:
                logger.error(f"❌ SMOKE TESTS FAILED (exit code: {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ SMOKE TESTS TIMED OUT")
            return False
        except Exception as e:
            logger.error(f"❌ SMOKE TESTS ERROR: {e}")
            return False

    def check_system_prerequisites(self):
        """Check system prerequisites"""
        logger.info("🔧 CHECKING SYSTEM PREREQUISITES")
        logger.info("=" * 50)

        prerequisites_passed = True

        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 7:
            logger.info(
                f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
            )
        else:
            logger.error(
                f"❌ Python version too old: {python_version.major}.{python_version.minor}.{python_version.micro}"
            )
            prerequisites_passed = False

        # Check required files exist
        required_files = [
            "receipt_matcher.py",
            "test_receipt_matcher_unit.py",
            "test_receipt_matcher.py",
            "receipt_matcher_cron.py",
            "receipt_matcher_api.py",
            "setup_receipt_matcher.py",
        ]

        for file_name in required_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                logger.info(f"✅ Required file exists: {file_name}")
            else:
                logger.error(f"❌ Required file missing: {file_name}")
                prerequisites_passed = False

        # Check database connectivity
        try:
            sys.path.append(str(self.script_dir))
            from scripts.grocery_db import GroceryDB

            db = GroceryDB()
            conn = db.get_connection()
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            prerequisites_passed = False

        return prerequisites_passed

    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 70)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        # Test results summary
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name.upper().replace('_', ' ')}: {status}")

        logger.info("=" * 70)
        logger.info(f"📈 OVERALL RESULTS: {passed_tests}/{total_tests} test suites passed")

        # System status
        if passed_tests == total_tests:
            logger.info("🎉 SYSTEM STATUS: PRODUCTION READY")
            logger.info("🚀 All tests passed - Receipt Matcher is ready for deployment!")
        else:
            logger.error("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
            logger.error("🔧 Some tests failed - Please review and fix issues before deployment")

        # Next steps
        logger.info("\n📋 NEXT STEPS:")
        if passed_tests == total_tests:
            logger.info("1. ✅ Install cron job: python setup_receipt_matcher.py")
            logger.info("2. ✅ Add grocery items to store lists")
            logger.info("3. ✅ Monitor logs: tail -f logs/receipt_matcher_cron.log")
            logger.info("4. ✅ Check status: curl http://localhost:8080/status")
        else:
            logger.info("1. 🔧 Fix failing tests")
            logger.info("2. 🔧 Re-run test suite")
            logger.info("3. 🔧 Check logs for detailed error information")

        return passed_tests == total_tests

    def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 STARTING COMPREHENSIVE TEST SUITE")
        logger.info("🕐 Start time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("=" * 70)

        start_time = time.time()

        # Check prerequisites
        self.test_results["prerequisites"] = self.check_system_prerequisites()

        # Run unit tests
        self.test_results["unit_tests"] = self.run_unit_tests()

        # Run integration tests
        self.test_results["integration_tests"] = self.run_integration_tests()

        # Run smoke tests
        self.test_results["smoke_tests"] = self.run_smoke_tests()

        # Calculate execution time
        execution_time = time.time() - start_time

        # Generate report
        success = self.generate_test_report()

        logger.info("=" * 70)
        logger.info(f"⏱️  Total execution time: {execution_time:.2f} seconds")
        logger.info("🕐 End time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return success


def main():
    """Main entry point"""
    try:
        runner = ComprehensiveTestRunner()
        success = runner.run_all_tests()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("🛑 Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
