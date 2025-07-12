#!/usr/bin/env python3
"""
Smoke Tests for Receipt Matcher System

End-to-end smoke tests that validate the complete receipt matcher system
in a production-like environment with real database operations.

Author: AI Agent
Date: 2025-07-11
"""

import os
import sys
import logging
import json
import time
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from receipt_matcher import ReceiptMatcher
from scripts.grocery_db import GroceryDB

# Configure logging with bright colors
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReceiptMatcherSmokeTest:
    """Comprehensive smoke tests for receipt matcher system"""
    
    def __init__(self):
        self.db = GroceryDB()
        self.matcher = ReceiptMatcher(lookback_hours=48)
        self.test_prefix = "SMOKE_TEST_"
        self.api_port = 8081  # Use different port for testing
        self.api_process = None
        
    def setup_smoke_test_data(self):
        """Create comprehensive smoke test data"""
        logger.info("🔧 SETTING UP SMOKE TEST DATA")
        
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        try:
            # Ensure tables exist
            self.matcher.ensure_tables_exist()
            
            # Clean up any existing smoke test data
            self.cleanup_smoke_test_data()
            
            # Create realistic test data
            current_time = datetime.now()
            recent_date = current_time.date()
            recent_time = current_time.time()
            
            # Add items to store lists
            smoke_test_items = {
                'costco_list': [
                    (f'{self.test_prefix}ORGANIC_BANANAS', 3, 'high'),
                    (f'{self.test_prefix}WHOLE_MILK_GALLON', 1, 'high'),
                    (f'{self.test_prefix}CHICKEN_BREAST_5LB', 1, 'medium'),
                    (f'{self.test_prefix}BREAD_LOAF', 2, 'medium'),
                    (f'{self.test_prefix}APPLES_3LB', 1, 'low')
                ],
                'walmart_list': [
                    (f'{self.test_prefix}EGGS_DOZEN', 2, 'high'),
                    (f'{self.test_prefix}CHEESE_SLICES', 1, 'medium'),
                    (f'{self.test_prefix}YOGURT_GREEK', 3, 'medium'),
                    (f'{self.test_prefix}CEREAL_BOX', 1, 'low')
                ],
                'cvs_list': [
                    (f'{self.test_prefix}VITAMINS_MULTI', 1, 'low'),
                    (f'{self.test_prefix}SHAMPOO_BOTTLE', 1, 'medium'),
                    (f'{self.test_prefix}TOOTHPASTE_TUBE', 2, 'high')
                ],
                'publix_list': [
                    (f'{self.test_prefix}ORANGE_JUICE', 1, 'medium'),
                    (f'{self.test_prefix}PASTA_BOX', 2, 'low')
                ]
            }
            
            # Insert list items
            for table_name, items in smoke_test_items.items():
                for item_name, quantity, priority in items:
                    cur.execute(f"""
                        INSERT INTO {table_name} (item_name, quantity_needed, priority)
                        VALUES (%s, %s, %s)
                    """, (item_name, quantity, priority))
            
            # Add recent purchases that should match
            smoke_test_purchases = [
                # Same store matches (should mark as checked)
                ('costco_purchases', f'{self.test_prefix}ORGANIC_BANANAS', 3, 5.99, 'SMOKE_RECEIPT_001'),
                ('costco_purchases', f'{self.test_prefix}WHOLE_MILK_GALLON', 1, 3.49, 'SMOKE_RECEIPT_001'),
                
                # Cross store match (should remove from other lists)
                ('walmart_purchases', f'{self.test_prefix}BREAD_LOAF', 1, 2.99, 'SMOKE_ORDER_002'),
                
                # CVS purchase with exact match
                ('cvs_purchases', f'{self.test_prefix}TOOTHPASTE_TUBE', 1, 4.99, 'SMOKE_CVS_003'),
                
                # Fuzzy match test
                ('publix_purchases', f'{self.test_prefix}ORANGE JUICE', 1, 3.99, 'SMOKE_PUBLIX_004'),
                
                # No match item (should be ignored)
                ('costco_purchases', f'{self.test_prefix}RANDOM_ITEM_NO_MATCH', 1, 1.99, 'SMOKE_RECEIPT_005')
            ]
            
            # Insert purchases with proper column mapping
            for table, item_name, quantity, price, receipt_id in smoke_test_purchases:
                if table == 'costco_purchases':
                    cur.execute("""
                        INSERT INTO costco_purchases (
                            item_name, purchase_date, purchase_time, item_quantity, item_price,
                            store_location, receipt_number
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (item_name, recent_date, recent_time, quantity, price, 'SMOKE_TEST_STORE', receipt_id))
                
                elif table == 'walmart_purchases':
                    cur.execute("""
                        INSERT INTO walmart_purchases (
                            item_name, purchase_date, purchase_time, item_quantity, item_price,
                            order_id, store_name
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (item_name, recent_date, recent_time, quantity, price, receipt_id, 'SMOKE_TEST_WALMART'))
                
                elif table == 'cvs_purchases':
                    cur.execute("""
                        INSERT INTO cvs_purchases (
                            item_name, purchase_date, purchase_time, item_quantity, item_price_final,
                            order_number, order_type
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (item_name, recent_date, recent_time, quantity, price, receipt_id, 'STORE'))
                
                elif table == 'publix_purchases':
                    cur.execute("""
                        INSERT INTO publix_purchases (
                            item_name, purchase_date, purchase_time, item_quantity, item_price,
                            transaction_number, store_name
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (item_name, recent_date, recent_time, quantity, price, receipt_id, 'SMOKE_TEST_PUBLIX'))
            
            conn.commit()
            logger.info("✅ SMOKE TEST DATA SETUP COMPLETED")
            
        except Exception as e:
            logger.error(f"❌ ERROR SETTING UP SMOKE TEST DATA: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    
    def test_core_matching_functionality(self):
        """Test core matching functionality"""
        logger.info("🎯 TESTING CORE MATCHING FUNCTIONALITY")
        
        try:
            # Run the matching process
            stats = self.matcher.run_matching_process()
            
            # Validate results
            expected_stats = {
                'marked_checked': 4,  # ORGANIC_BANANAS, WHOLE_MILK_GALLON, TOOTHPASTE_TUBE, ORANGE_JUICE (fuzzy match)
                'removed_from_lists': 1,  # BREAD_LOAF (cross-store)
                'inventory_added': 5,  # All matched items including fuzzy match
                'no_action': 1,  # RANDOM_ITEM_NO_MATCH
                'errors': 0
            }
            
            # Check stats
            for key, expected_value in expected_stats.items():
                actual_value = stats.get(key, 0)
                if actual_value != expected_value:
                    logger.error(f"❌ STAT MISMATCH: {key} expected {expected_value}, got {actual_value}")
                    return False
                else:
                    logger.info(f"✅ STAT CORRECT: {key} = {actual_value}")
            
            logger.info("✅ CORE MATCHING FUNCTIONALITY TEST PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ CORE MATCHING FUNCTIONALITY TEST FAILED: {e}")
            return False
    
    def test_database_state_validation(self):
        """Validate database state after matching"""
        logger.info("🗃️ TESTING DATABASE STATE VALIDATION")
        
        conn = self.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check that items are marked as checked
            checked_items = [
                f'{self.test_prefix}ORGANIC_BANANAS',
                f'{self.test_prefix}WHOLE_MILK_GALLON',
                f'{self.test_prefix}TOOTHPASTE_TUBE',
                f'{self.test_prefix}ORANGE_JUICE'  # Fuzzy match
            ]
            
            for item_name in checked_items:
                # Find which table this item is in
                for store, table_name in self.matcher.list_tables.items():
                    cur.execute(f"""
                        SELECT is_checked FROM {table_name} 
                        WHERE item_name = %s
                    """, (item_name,))
                    
                    result = cur.fetchone()
                    if result:
                        if result['is_checked']:
                            logger.info(f"✅ ITEM CORRECTLY CHECKED: {item_name}")
                        else:
                            logger.error(f"❌ ITEM NOT CHECKED: {item_name}")
                            return False
                        break
            
            # Check that BREAD_LOAF was removed from lists
            removed_item = f'{self.test_prefix}BREAD_LOAF'
            found_in_lists = False
            
            for store, table_name in self.matcher.list_tables.items():
                cur.execute(f"""
                    SELECT COUNT(*) as count FROM {table_name} 
                    WHERE item_name = %s
                """, (removed_item,))
                
                result = cur.fetchone()
                if result['count'] > 0:
                    found_in_lists = True
                    break
            
            if found_in_lists:
                logger.error(f"❌ ITEM NOT REMOVED: {removed_item}")
                return False
            else:
                logger.info(f"✅ ITEM CORRECTLY REMOVED: {removed_item}")
            
            # Check inventory entries
            cur.execute("""
                SELECT COUNT(*) as count FROM inventory 
                WHERE item_name LIKE %s
            """, (f'{self.test_prefix}%',))
            
            inventory_count = cur.fetchone()['count']
            if inventory_count >= 5:  # Should have at least 5 inventory entries
                logger.info(f"✅ INVENTORY ENTRIES CREATED: {inventory_count}")
            else:
                logger.error(f"❌ INSUFFICIENT INVENTORY ENTRIES: {inventory_count}")
                return False
            
            logger.info("✅ DATABASE STATE VALIDATION TEST PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ DATABASE STATE VALIDATION TEST FAILED: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    
    def test_cron_job_execution(self):
        """Test cron job script execution"""
        logger.info("⏰ TESTING CRON JOB EXECUTION")
        
        try:
            # Run the cron job script
            script_path = Path(__file__).parent / "receipt_matcher_cron.py"
            
            if not script_path.exists():
                logger.error(f"❌ CRON SCRIPT NOT FOUND: {script_path}")
                return False
            
            # Execute cron script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ CRON JOB EXECUTION SUCCESSFUL")
                
                # Check if status file was created
                status_file = Path(__file__).parent / "logs" / "last_run_status.json"
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)
                    
                    if status_data.get('status') == 'success':
                        logger.info("✅ CRON JOB STATUS FILE VALID")
                        return True
                    else:
                        logger.error(f"❌ CRON JOB STATUS INVALID: {status_data}")
                        return False
                else:
                    logger.error("❌ CRON JOB STATUS FILE NOT CREATED")
                    return False
            else:
                logger.error(f"❌ CRON JOB EXECUTION FAILED: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ CRON JOB EXECUTION TEST FAILED: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test HTTP API endpoints"""
        logger.info("🌐 TESTING HTTP API ENDPOINTS")
        
        try:
            # Start API server
            api_script = Path(__file__).parent / "receipt_matcher_api.py"
            
            if not api_script.exists():
                logger.error(f"❌ API SCRIPT NOT FOUND: {api_script}")
                return False
            
            # Start API server in background
            self.api_process = subprocess.Popen(
                [sys.executable, str(api_script), "--port", str(self.api_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(3)
            
            base_url = f"http://localhost:{self.api_port}"
            
            # Test health endpoint
            try:
                response = requests.get(f"{base_url}/health", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ HEALTH ENDPOINT WORKING")
                else:
                    logger.error(f"❌ HEALTH ENDPOINT FAILED: {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"❌ HEALTH ENDPOINT REQUEST FAILED: {e}")
                return False
            
            # Test match endpoint
            try:
                response = requests.post(
                    f"{base_url}/match",
                    json={"lookback_hours": 1},
                    timeout=30
                )
                if response.status_code == 202:
                    logger.info("✅ MATCH ENDPOINT WORKING")
                else:
                    logger.error(f"❌ MATCH ENDPOINT FAILED: {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"❌ MATCH ENDPOINT REQUEST FAILED: {e}")
                return False
            
            # Wait for background processing
            time.sleep(5)
            
            # Test status endpoint
            try:
                response = requests.get(f"{base_url}/status", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ STATUS ENDPOINT WORKING")
                    status_data = response.json()
                    if 'timestamp' in status_data:
                        logger.info("✅ STATUS DATA VALID")
                    else:
                        logger.error("❌ STATUS DATA INVALID")
                        return False
                else:
                    logger.error(f"❌ STATUS ENDPOINT FAILED: {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"❌ STATUS ENDPOINT REQUEST FAILED: {e}")
                return False
            
            logger.info("✅ HTTP API ENDPOINTS TEST PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ HTTP API ENDPOINTS TEST FAILED: {e}")
            return False
        finally:
            # Clean up API server
            if self.api_process:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
    
    def cleanup_smoke_test_data(self):
        """Clean up all smoke test data"""
        logger.info("🧹 CLEANING UP SMOKE TEST DATA")
        
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        try:
            # Clean up from all tables
            tables_to_clean = [
                'costco_list', 'walmart_list', 'cvs_list', 'publix_list',
                'costco_purchases', 'walmart_purchases', 'cvs_purchases', 'publix_purchases',
                'inventory'
            ]
            
            for table in tables_to_clean:
                cur.execute(f"DELETE FROM {table} WHERE item_name LIKE %s", (f'{self.test_prefix}%',))
                if cur.rowcount > 0:
                    logger.info(f"🗑️ Cleaned {cur.rowcount} records from {table}")
            
            # Also clean up by receipt/order IDs
            cur.execute("DELETE FROM costco_purchases WHERE receipt_number LIKE 'SMOKE_%'")
            cur.execute("DELETE FROM walmart_purchases WHERE order_id LIKE 'SMOKE_%'")
            cur.execute("DELETE FROM cvs_purchases WHERE order_number LIKE 'SMOKE_%'")
            cur.execute("DELETE FROM publix_purchases WHERE transaction_number LIKE 'SMOKE_%'")
            
            conn.commit()
            logger.info("✅ SMOKE TEST DATA CLEANUP COMPLETED")
            
        except Exception as e:
            logger.error(f"❌ ERROR CLEANING UP SMOKE TEST DATA: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def run_full_smoke_test_suite(self):
        """Run the complete smoke test suite"""
        logger.info("🔥 STARTING RECEIPT MATCHER SMOKE TEST SUITE")
        logger.info("=" * 70)
        
        test_results = {}
        
        try:
            # Setup test data
            self.setup_smoke_test_data()
            test_results['setup'] = True
            
            # Run core functionality tests
            test_results['core_matching'] = self.test_core_matching_functionality()
            
            # Validate database state
            test_results['database_validation'] = self.test_database_state_validation()
            
            # Test cron job execution
            test_results['cron_job'] = self.test_cron_job_execution()
            
            # Test API endpoints
            test_results['api_endpoints'] = self.test_api_endpoints()
            
        except Exception as e:
            logger.error(f"💥 SMOKE TEST SUITE FAILED: {e}")
            test_results['setup'] = False
        finally:
            # Always cleanup
            self.cleanup_smoke_test_data()
        
        # Print results summary
        logger.info("🔥 SMOKE TEST RESULTS SUMMARY")
        logger.info("=" * 70)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        logger.info("=" * 70)
        logger.info(f"📊 TOTAL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL SMOKE TESTS PASSED - SYSTEM IS PRODUCTION READY!")
            return True
        else:
            logger.error("❌ SOME SMOKE TESTS FAILED - SYSTEM NEEDS ATTENTION!")
            return False

def main():
    """Main entry point for smoke tests"""
    try:
        smoke_tester = ReceiptMatcherSmokeTest()
        success = smoke_tester.run_full_smoke_test_suite()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 SMOKE TEST EXECUTION FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
