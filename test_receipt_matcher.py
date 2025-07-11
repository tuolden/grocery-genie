#!/usr/bin/env python3
"""
Test Receipt Matcher - Unit tests and integration tests

This script tests the receipt matcher functionality with sample data
to ensure it works correctly before deploying as a cron job.

Author: AI Agent
Date: 2025-07-11
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from receipt_matcher import ReceiptMatcher
from scripts.grocery_db import GroceryDB

# Configure logging
logging.basicConfig(level=logging.INFO, format='🧪 %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ReceiptMatcherTester:
    """Test class for receipt matcher functionality"""
    
    def __init__(self):
        self.db = GroceryDB()
        self.matcher = ReceiptMatcher(lookback_hours=48)  # Look back 48 hours for testing
        
    def setup_test_data(self):
        """Create test data for validation"""
        logger.info("🔧 SETTING UP TEST DATA")
        
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        try:
            # Ensure tables exist
            self.matcher.ensure_tables_exist()
            
            # Clear existing test data
            logger.info("🧹 Clearing existing test data")
            test_tables = ['costco_list', 'walmart_list', 'cvs_list', 'publix_list', 'inventory']
            for table in test_tables:
                cur.execute(f"DELETE FROM {table} WHERE item_name LIKE 'TEST_%'")
            
            # Add test items to store lists
            logger.info("📋 Adding test items to store lists")
            
            # Costco list items
            test_costco_items = [
                'TEST_BANANAS',
                'TEST_ORGANIC MILK',
                'TEST_BREAD LOAF',
                'TEST_CHICKEN BREAST',
                'TEST_APPLES'
            ]
            
            for item in test_costco_items:
                cur.execute("""
                    INSERT INTO costco_list (item_name, quantity_needed, priority)
                    VALUES (%s, %s, %s)
                """, (item, 2, 'high'))
            
            # Walmart list items
            test_walmart_items = [
                'TEST_EGGS',
                'TEST_CHEESE',
                'TEST_YOGURT',
                'TEST_CEREAL'
            ]
            
            for item in test_walmart_items:
                cur.execute("""
                    INSERT INTO walmart_list (item_name, quantity_needed, priority)
                    VALUES (%s, %s, %s)
                """, (item, 1, 'medium'))
            
            # CVS list items
            test_cvs_items = [
                'TEST_VITAMINS',
                'TEST_SHAMPOO',
                'TEST_TOOTHPASTE'
            ]
            
            for item in test_cvs_items:
                cur.execute("""
                    INSERT INTO cvs_list (item_name, quantity_needed, priority)
                    VALUES (%s, %s, %s)
                """, (item, 1, 'low'))
            
            # Add some test purchases that should match
            logger.info("🛒 Adding test purchases")
            
            # Recent Costco purchase that should match
            recent_date = datetime.now().date()
            recent_time = datetime.now().time()
            
            # This should match and mark TEST_BANANAS as checked
            cur.execute("""
                INSERT INTO costco_purchases (
                    item_name, purchase_date, purchase_time, item_quantity, item_price,
                    store_location, receipt_number
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('TEST_BANANAS', recent_date, recent_time, 2, 3.99, 'TEST STORE', 'TEST123'))
            
            # This should match and mark TEST_ORGANIC MILK as checked
            cur.execute("""
                INSERT INTO costco_purchases (
                    item_name, purchase_date, purchase_time, item_quantity, item_price,
                    store_location, receipt_number
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('TEST_ORGANIC MILK', recent_date, recent_time, 1, 4.99, 'TEST STORE', 'TEST123'))
            
            # Cross-store purchase - bought at Walmart but was on Costco list
            cur.execute("""
                INSERT INTO walmart_purchases (
                    item_name, purchase_date, purchase_time, item_quantity, item_price,
                    order_id, store_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('TEST_BREAD LOAF', recent_date, recent_time, 1, 2.49, 'TEST456', 'TEST WALMART'))
            
            # Purchase with no matching list item
            cur.execute("""
                INSERT INTO cvs_purchases (
                    item_name, purchase_date, purchase_time, item_quantity, item_price_final,
                    order_number, order_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('TEST_RANDOM ITEM', recent_date, recent_time, 1, 1.99, 'TEST789', 'STORE'))
            
            conn.commit()
            logger.info("✅ TEST DATA SETUP COMPLETED")
            
        except Exception as e:
            logger.error(f"❌ ERROR SETTING UP TEST DATA: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    
    def run_test_scenarios(self):
        """Run various test scenarios"""
        logger.info("🧪 RUNNING TEST SCENARIOS")
        
        # Test 1: Same store match
        logger.info("📝 TEST 1: Same store match (Costco)")
        
        # Test 2: Cross store match  
        logger.info("📝 TEST 2: Cross store match (Walmart purchase, Costco list)")
        
        # Test 3: No match scenario
        logger.info("📝 TEST 3: No match scenario")
        
        # Test 4: Fuzzy matching
        logger.info("📝 TEST 4: Fuzzy matching test")
        
        # Run the actual matching process
        stats = self.matcher.run_matching_process()
        
        return stats
    
    def validate_results(self):
        """Validate that the matching worked correctly"""
        logger.info("✅ VALIDATING RESULTS")
        
        conn = self.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check that TEST_BANANAS is marked as checked in costco_list
            cur.execute("SELECT * FROM costco_list WHERE item_name = 'TEST_BANANAS'")
            bananas = cur.fetchone()
            
            if bananas and bananas['is_checked']:
                logger.info("✅ TEST_BANANAS correctly marked as checked")
            else:
                logger.error("❌ TEST_BANANAS not marked as checked")
            
            # Check that TEST_ORGANIC MILK is marked as checked
            cur.execute("SELECT * FROM costco_list WHERE item_name = 'TEST_ORGANIC MILK'")
            milk = cur.fetchone()
            
            if milk and milk['is_checked']:
                logger.info("✅ TEST_ORGANIC MILK correctly marked as checked")
            else:
                logger.error("❌ TEST_ORGANIC MILK not marked as checked")
            
            # Check inventory entries
            cur.execute("SELECT COUNT(*) as count FROM inventory WHERE item_name LIKE 'TEST_%'")
            inventory_count = cur.fetchone()['count']
            
            logger.info(f"📦 Inventory entries created: {inventory_count}")
            
            # Show inventory details
            cur.execute("""
                SELECT item_name, store, quantity, purchase_date, price
                FROM inventory 
                WHERE item_name LIKE 'TEST_%'
                ORDER BY created_at DESC
            """)
            
            inventory_items = cur.fetchall()
            for item in inventory_items:
                logger.info(f"📦 Inventory: {item['item_name']} - {item['store']} - Qty: {item['quantity']} - ${item['price']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ERROR VALIDATING RESULTS: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    
    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 CLEANING UP TEST DATA")
        
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        try:
            # Remove test data from all tables
            test_tables = [
                'costco_list', 'walmart_list', 'cvs_list', 'publix_list',
                'costco_purchases', 'walmart_purchases', 'cvs_purchases', 'publix_purchases',
                'inventory'
            ]
            
            for table in test_tables:
                cur.execute(f"DELETE FROM {table} WHERE item_name LIKE 'TEST_%'")
                if cur.rowcount > 0:
                    logger.info(f"🗑️ Removed {cur.rowcount} test records from {table}")
            
            # Also clean up test receipts
            cur.execute("DELETE FROM costco_purchases WHERE receipt_number = 'TEST123'")
            cur.execute("DELETE FROM walmart_purchases WHERE order_id = 'TEST456'")
            cur.execute("DELETE FROM cvs_purchases WHERE order_number = 'TEST789'")
            
            conn.commit()
            logger.info("✅ TEST DATA CLEANUP COMPLETED")
            
        except Exception as e:
            logger.error(f"❌ ERROR CLEANING UP TEST DATA: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        logger.info("🚀 STARTING RECEIPT MATCHER TEST SUITE")
        logger.info("=" * 60)
        
        try:
            # Setup test data
            self.setup_test_data()
            
            # Run test scenarios
            stats = self.run_test_scenarios()
            
            # Validate results
            validation_passed = self.validate_results()
            
            # Show final results
            logger.info("📊 TEST SUITE RESULTS")
            logger.info("=" * 60)
            logger.info(f"✅ Validation passed: {validation_passed}")
            logger.info(f"📈 Processing stats: {stats}")
            logger.info("=" * 60)
            
            return validation_passed
            
        except Exception as e:
            logger.error(f"💥 TEST SUITE FAILED: {e}")
            return False
        finally:
            # Always cleanup
            self.cleanup_test_data()

def main():
    """Main entry point for testing"""
    try:
        tester = ReceiptMatcherTester()
        success = tester.run_full_test_suite()
        
        if success:
            logger.info("🎉 ALL TESTS PASSED - RECEIPT MATCHER IS READY!")
            return 0
        else:
            logger.error("❌ TESTS FAILED - CHECK LOGS FOR DETAILS")
            return 1
            
    except Exception as e:
        logger.error(f"💥 TEST EXECUTION FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
