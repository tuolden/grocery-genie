#!/usr/bin/env python3
# ruff: noqa: E501
"""
Setup Receipt Matcher System

This script sets up the complete receipt matcher system including:
- Database tables creation
- Cron job installation
- Initial configuration
- Testing validation

Author: AI Agent
Date: 2025-07-11
"""

import logging
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from receipt_matcher import ReceiptMatcher
from test_receipt_matcher import ReceiptMatcherTester

# Configure logging
logging.basicConfig(level=logging.INFO, format="🔧 %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_database_tables():
    """Setup required database tables"""
    logger.info("🗃️ SETTING UP DATABASE TABLES")

    try:
        matcher = ReceiptMatcher()
        matcher.ensure_tables_exist()
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False


def run_tests():
    """Run comprehensive tests"""
    logger.info("🧪 RUNNING COMPREHENSIVE TESTS")

    try:
        tester = ReceiptMatcherTester()
        success = tester.run_full_test_suite()

        if success:
            logger.info("✅ All tests passed successfully")
        else:
            logger.error("❌ Some tests failed")

        return success
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False


def setup_cron_job():
    """Setup cron job for automatic execution"""
    logger.info("⏰ SETTING UP CRON JOB")

    try:
        # Get current script directory
        script_dir = Path(__file__).parent.absolute()
        cron_script = script_dir / "receipt_matcher_cron.py"
        log_dir = script_dir / "logs"

        # Create logs directory
        log_dir.mkdir(exist_ok=True)

        # Create cron job entry
        cron_entry = f"*/30 * * * * /usr/bin/python3 {cron_script} >> {log_dir}/receipt_matcher_cron.log 2>&1"

        logger.info(f"📝 Cron job entry: {cron_entry}")
        logger.info("⚠️  To install the cron job, run:")
        logger.info(f"   echo '{cron_entry}' | crontab -")
        logger.info("   OR manually add to crontab with: crontab -e")

        # Make scripts executable
        os.chmod(cron_script, 0o755)
        os.chmod(script_dir / "receipt_matcher.py", 0o755)

        logger.info("✅ Cron job setup completed (manual installation required)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to setup cron job: {e}")
        return False


def create_sample_list_data():
    """Create sample list data for demonstration"""
    logger.info("📋 CREATING SAMPLE LIST DATA")

    try:
        from scripts.grocery_db import GroceryDB

        db = GroceryDB()
        conn = db.get_connection()
        cur = conn.cursor()

        # Sample items for each store
        sample_data = {
            "costco_list": [
                ("Bananas 3 lb", 2, "high"),
                ("Organic Milk 1 gal", 1, "high"),
                ("Bread Loaf", 1, "medium"),
                ("Chicken Breast 5 lb", 1, "high"),
                ("Apples 3 lb", 2, "medium"),
            ],
            "walmart_list": [
                ("Eggs 12 count", 1, "high"),
                ("Cheese Slices", 1, "medium"),
                ("Greek Yogurt", 2, "medium"),
                ("Cereal Box", 1, "low"),
            ],
            "cvs_list": [
                ("Multivitamins", 1, "low"),
                ("Shampoo", 1, "medium"),
                ("Toothpaste", 1, "high"),
            ],
            "publix_list": [
                ("Orange Juice", 1, "medium"),
                ("Pasta", 2, "low"),
                ("Tomato Sauce", 2, "low"),
            ],
        }

        for table_name, items in sample_data.items():
            # Check if table has any non-test data
            cur.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE item_name NOT LIKE 'TEST_%'"
            )
            count = cur.fetchone()[0]

            if count == 0:
                logger.info(f"📝 Adding sample data to {table_name}")
                for item_name, quantity, priority in items:
                    cur.execute(
                        f"""
                        INSERT INTO {table_name} (item_name, quantity_needed, priority)
                        VALUES (%s, %s, %s)
                    """,
                        (item_name, quantity, priority),
                    )
            else:
                logger.info(
                    f"📊 {table_name} already has {count} items, skipping sample data"
                )

        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Sample list data created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        return False


def show_usage_instructions():
    """Show usage instructions"""
    logger.info("📖 USAGE INSTRUCTIONS")
    logger.info("=" * 60)

    script_dir = Path(__file__).parent.absolute()

    logger.info("🔧 MANUAL EXECUTION:")
    logger.info(f"   python {script_dir}/receipt_matcher.py")
    logger.info(f"   python {script_dir}/receipt_matcher.py --hours 48")
    logger.info(f"   python {script_dir}/receipt_matcher.py --dry-run")

    logger.info("\n⏰ CRON JOB:")
    logger.info("   Runs automatically every 30 minutes")
    logger.info(f"   Logs: {script_dir}/logs/receipt_matcher_cron.log")
    logger.info(f"   Status: {script_dir}/logs/last_run_status.json")

    logger.info("\n🌐 HTTP API:")
    logger.info(f"   python {script_dir}/receipt_matcher_api.py")
    logger.info("   curl http://localhost:8080/health")
    logger.info("   curl -X POST http://localhost:8080/match")
    logger.info("   curl http://localhost:8080/status")

    logger.info("\n🧪 TESTING:")
    logger.info(f"   python {script_dir}/test_receipt_matcher.py")

    logger.info("\n📋 LIST MANAGEMENT:")
    logger.info("   Add items to store lists using database or future web interface")
    logger.info("   Lists: costco_list, walmart_list, cvs_list, publix_list")

    logger.info("\n📦 INVENTORY:")
    logger.info("   View inventory table for purchased items")
    logger.info("   Includes store, quantity, price, purchase date")


def main():
    """Main setup function"""
    logger.info("🚀 STARTING RECEIPT MATCHER SETUP")
    logger.info("=" * 60)

    success_count = 0
    total_steps = 5

    # Step 1: Setup database tables
    if setup_database_tables():
        success_count += 1

    # Step 2: Create sample data
    if create_sample_list_data():
        success_count += 1

    # Step 3: Run tests
    if run_tests():
        success_count += 1

    # Step 4: Setup cron job
    if setup_cron_job():
        success_count += 1

    # Step 5: Show instructions
    show_usage_instructions()
    success_count += 1

    # Final summary
    logger.info("📊 SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Completed steps: {success_count}/{total_steps}")

    if success_count == total_steps:
        logger.info("🎉 RECEIPT MATCHER SETUP COMPLETED SUCCESSFULLY!")
        logger.info("🚀 System is ready for production use")
        return 0
    logger.error("❌ Setup completed with some issues")
    logger.error("🔧 Please check the logs and fix any errors")
    return 1


if __name__ == "__main__":
    exit(main())
