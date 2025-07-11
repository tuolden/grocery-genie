#!/usr/bin/env python3
"""
Comprehensive Smoke Test for Other Purchases Loader

Creates diverse test data with various field combinations, processes through
the loader, and validates database integrity with detailed reporting.

Tests 30-50 items across multiple scenarios:
- Complete data with all fields
- Minimal data with only required fields
- Missing optional fields
- Different data types and edge cases
- Multiple stores and receipt sources
- Various price formats and quantities

Author: AI Agent
Date: 2025-07-11
"""

import os
import sys
import yaml
import json
import tempfile
import shutil
import logging
from datetime import datetime, date, time
from pathlib import Path
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from other_purchases_loader import OtherPurchasesLoader

# Configure logging with bright colors
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class OtherPurchasesSmokeTest:
    """Comprehensive smoke test for other purchases loader"""
    
    def __init__(self):
        """Initialize smoke test"""
        self.test_dir = None
        self.loader = None
        self.test_files_created = []
        self.expected_items = []
        self.test_results = {
            'files_created': 0,
            'items_expected': 0,
            'items_loaded': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'errors': []
        }
        
        logger.info("🔥 INITIALIZING OTHER PURCHASES SMOKE TEST")
    
    def setup_test_environment(self):
        """Set up temporary test environment"""
        logger.info("🔧 SETTING UP TEST ENVIRONMENT")
        
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="other_purchases_smoke_")
        logger.info(f"📁 Test directory: {self.test_dir}")
        
        # Initialize loader with test directory
        self.loader = OtherPurchasesLoader(data_dir=self.test_dir)
        
        # Clean any existing test data from database
        self._cleanup_test_data()
        
        logger.info("✅ TEST ENVIRONMENT READY")
    
    def _cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            conn = self.loader.db.get_connection()
            cur = conn.cursor()
            
            # Remove any test data
            cur.execute("DELETE FROM other_purchases WHERE store_name LIKE 'SMOKE_TEST_%'")
            deleted_count = cur.rowcount
            
            conn.commit()
            cur.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned {deleted_count} existing test records")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not clean test data: {e}")
    
    def create_test_data_files(self):
        """Create diverse test YAML files with various field combinations"""
        logger.info("📝 CREATING DIVERSE TEST DATA FILES")
        
        test_scenarios = [
            # Scenario 1: Complete data with all fields
            {
                'filename': '2025-07-11T10-00-00.yaml',
                'store_name': 'SMOKE_TEST_COMPLETE_STORE',
                'receipt_source': 'manual',
                'purchase_notes': 'Complete test data',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_COMPLETE_ITEM_1',
                        'variant': 'large size',
                        'quantity': 2,
                        'quantity_unit': 'pieces',
                        'price': 15.99,
                        'original_text': 'COMPLETE ITEM LG'
                    },
                    {
                        'item_name': 'SMOKE_TEST_COMPLETE_ITEM_2',
                        'variant': 'organic',
                        'quantity': 1,
                        'quantity_unit': 'bag',
                        'price': 8.50,
                        'original_text': 'ORG ITEM BAG'
                    }
                ],
                'receipt_metadata': {
                    'total_amount': 24.49,
                    'tax_amount': 2.00,
                    'subtotal': 22.49,
                    'payment_method': 'Credit Card'
                }
            },
            
            # Scenario 2: Minimal data with only required fields
            {
                'filename': '2025-07-11T10-15-00.yaml',
                'store_name': 'SMOKE_TEST_MINIMAL_STORE',
                'items': [
                    {'item_name': 'SMOKE_TEST_MINIMAL_ITEM_1'},
                    {'item_name': 'SMOKE_TEST_MINIMAL_ITEM_2'},
                    {'item_name': 'SMOKE_TEST_MINIMAL_ITEM_3'}
                ]
            },
            
            # Scenario 3: Mixed field combinations
            {
                'filename': '2025-07-11T10-30-00.yaml',
                'store_name': 'SMOKE_TEST_MIXED_STORE',
                'receipt_source': 'image',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_MIXED_ITEM_1',
                        'quantity': 5,
                        'price': 12.75
                    },
                    {
                        'item_name': 'SMOKE_TEST_MIXED_ITEM_2',
                        'variant': 'extra large',
                        'original_text': 'XL ITEM'
                    },
                    {
                        'item_name': 'SMOKE_TEST_MIXED_ITEM_3',
                        'quantity': 3,
                        'quantity_unit': 'bottles',
                        'price': 9.99
                    }
                ]
            },
            
            # Scenario 4: Different price formats and edge cases
            {
                'filename': '2025-07-11T10-45-00.yaml',
                'store_name': 'SMOKE_TEST_EDGE_CASES_STORE',
                'receipt_source': 'text',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_ZERO_PRICE',
                        'price': 0.00,
                        'quantity': 1
                    },
                    {
                        'item_name': 'SMOKE_TEST_HIGH_PRICE',
                        'price': 999.99,
                        'quantity': 1
                    },
                    {
                        'item_name': 'SMOKE_TEST_DECIMAL_PRICE',
                        'price': 3.333,
                        'quantity': 2
                    },
                    {
                        'item_name': 'SMOKE_TEST_NO_PRICE',
                        'quantity': 10,
                        'quantity_unit': 'units'
                    }
                ]
            },
            
            # Scenario 5: Large quantity test
            {
                'filename': '2025-07-11T11-00-00.yaml',
                'store_name': 'SMOKE_TEST_BULK_STORE',
                'items': [
                    {
                        'item_name': f'SMOKE_TEST_BULK_ITEM_{i:02d}',
                        'variant': f'variant_{i}',
                        'quantity': i,
                        'quantity_unit': 'pieces',
                        'price': round(i * 1.25, 2),
                        'original_text': f'BULK ITEM {i:02d}'
                    } for i in range(1, 16)  # 15 items
                ]
            },
            
            # Scenario 6: Special characters and unicode
            {
                'filename': '2025-07-11T11-15-00.yaml',
                'store_name': 'SMOKE_TEST_UNICODE_STORE',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_SPECIAL_CHARS_!@#$%',
                        'variant': 'with & symbols',
                        'price': 5.99
                    },
                    {
                        'item_name': 'SMOKE_TEST_UNICODE_CAFÉ',
                        'variant': 'français',
                        'price': 7.50
                    },
                    {
                        'item_name': 'SMOKE_TEST_NUMBERS_123',
                        'variant': '50% off',
                        'price': 2.50
                    }
                ]
            },
            
            # Scenario 7: Different stores same time
            {
                'filename': '2025-07-11T11-30-00.yaml',
                'store_name': 'SMOKE_TEST_PHARMACY',
                'receipt_source': 'manual',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_MEDICINE_A',
                        'variant': '30 tablets',
                        'quantity': 1,
                        'price': 25.99
                    },
                    {
                        'item_name': 'SMOKE_TEST_VITAMINS_B',
                        'variant': '60 capsules',
                        'quantity': 2,
                        'price': 18.50
                    }
                ]
            },
            
            # Scenario 8: Grocery store with produce
            {
                'filename': '2025-07-11T11-45-00.yaml',
                'store_name': 'SMOKE_TEST_GROCERY',
                'items': [
                    {
                        'item_name': 'SMOKE_TEST_ORGANIC_APPLES',
                        'variant': '3 lb bag',
                        'quantity': 2,
                        'quantity_unit': 'bags',
                        'price': 8.98
                    },
                    {
                        'item_name': 'SMOKE_TEST_WHOLE_MILK',
                        'variant': '1 gallon',
                        'quantity': 1,
                        'quantity_unit': 'gallon',
                        'price': 4.29
                    },
                    {
                        'item_name': 'SMOKE_TEST_BREAD_LOAF',
                        'variant': 'whole wheat',
                        'quantity': 1,
                        'quantity_unit': 'loaf',
                        'price': 3.49
                    }
                ]
            }
        ]
        
        # Create YAML files
        for scenario in test_scenarios:
            file_path = Path(self.test_dir) / scenario['filename']
            
            # Create YAML content
            yaml_content = {
                'store_name': scenario['store_name'],
                'items': scenario['items']
            }
            
            # Add optional fields if present
            for optional_field in ['receipt_source', 'purchase_notes', 'receipt_metadata']:
                if optional_field in scenario:
                    yaml_content[optional_field] = scenario[optional_field]
            
            # Write YAML file
            with open(file_path, 'w') as f:
                yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True)
            
            self.test_files_created.append(file_path)
            
            # Track expected items
            for item in scenario['items']:
                expected_item = {
                    'store_name': scenario['store_name'],
                    'item_name': item['item_name'],
                    'filename': scenario['filename']
                }
                expected_item.update(item)
                self.expected_items.append(expected_item)
            
            logger.info(f"📄 Created {scenario['filename']} with {len(scenario['items'])} items")
        
        self.test_results['files_created'] = len(self.test_files_created)
        self.test_results['items_expected'] = len(self.expected_items)
        
        logger.info(f"✅ CREATED {len(self.test_files_created)} TEST FILES WITH {len(self.expected_items)} TOTAL ITEMS")
    
    def run_loader(self):
        """Run the other purchases loader on test data"""
        logger.info("🔄 RUNNING OTHER PURCHASES LOADER")
        
        try:
            # Process all files
            stats = self.loader.process_all_files()
            
            logger.info(f"📊 LOADER STATS: {stats}")
            
            if stats['failed'] > 0:
                self.test_results['errors'].append(f"Loader failed to process {stats['failed']} files")
            
            return stats['processed'] > 0
            
        except Exception as e:
            error_msg = f"Loader execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def validate_database_data(self):
        """Validate that all expected data made it to the database"""
        logger.info("🔍 VALIDATING DATABASE DATA")
        
        try:
            conn = self.loader.db.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all test records from database
            cur.execute("""
                SELECT * FROM other_purchases 
                WHERE store_name LIKE 'SMOKE_TEST_%'
                ORDER BY store_name, item_name
            """)
            
            db_records = cur.fetchall()
            self.test_results['items_loaded'] = len(db_records)
            
            logger.info(f"📊 Found {len(db_records)} records in database")
            
            # Validate each expected item
            for expected_item in self.expected_items:
                validation_result = self._validate_single_item(expected_item, db_records)
                
                if validation_result['valid']:
                    self.test_results['validation_passed'] += 1
                    logger.info(f"✅ VALID: {expected_item['item_name']}")
                else:
                    self.test_results['validation_failed'] += 1
                    error_msg = f"INVALID: {expected_item['item_name']} - {validation_result['error']}"
                    logger.error(f"❌ {error_msg}")
                    self.test_results['errors'].append(error_msg)
            
            cur.close()
            conn.close()
            
            return self.test_results['validation_failed'] == 0
            
        except Exception as e:
            error_msg = f"Database validation failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def _validate_single_item(self, expected_item, db_records):
        """Validate a single expected item against database records"""
        # Find matching record
        matching_record = None
        for record in db_records:
            if (record['store_name'] == expected_item['store_name'] and 
                record['item_name'] == expected_item['item_name']):
                matching_record = record
                break
        
        if not matching_record:
            return {'valid': False, 'error': 'Record not found in database'}
        
        # Validate fields
        validations = []
        
        # Check required fields
        if matching_record['store_name'] != expected_item['store_name']:
            validations.append(f"store_name mismatch: expected {expected_item['store_name']}, got {matching_record['store_name']}")
        
        if matching_record['item_name'] != expected_item['item_name']:
            validations.append(f"item_name mismatch: expected {expected_item['item_name']}, got {matching_record['item_name']}")
        
        # Check optional fields if present in expected
        optional_fields = ['variant', 'quantity', 'quantity_unit', 'price', 'original_text']
        
        for field in optional_fields:
            if field in expected_item:
                expected_value = expected_item[field]
                actual_value = matching_record[field]
                
                # Special handling for price (convert to float for comparison)
                if field == 'price' and expected_value is not None:
                    try:
                        expected_float = float(expected_value)
                        actual_float = float(actual_value) if actual_value else 0.0
                        if abs(expected_float - actual_float) > 0.01:  # Allow small floating point differences
                            validations.append(f"{field} mismatch: expected {expected_float}, got {actual_float}")
                    except (ValueError, TypeError):
                        validations.append(f"{field} type error: expected {expected_value}, got {actual_value}")
                elif expected_value != actual_value:
                    validations.append(f"{field} mismatch: expected {expected_value}, got {actual_value}")
        
        if validations:
            return {'valid': False, 'error': '; '.join(validations)}
        
        return {'valid': True, 'error': None}

    def generate_detailed_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 GENERATING DETAILED SMOKE TEST REPORT")

        report = []
        report.append("🔥 OTHER PURCHASES LOADER SMOKE TEST REPORT")
        report.append("=" * 70)
        report.append(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📁 Test Directory: {self.test_dir}")
        report.append("")

        # Test Summary
        report.append("📊 TEST SUMMARY")
        report.append("-" * 50)
        report.append(f"📄 Files Created: {self.test_results['files_created']}")
        report.append(f"📦 Items Expected: {self.test_results['items_expected']}")
        report.append(f"💾 Items Loaded: {self.test_results['items_loaded']}")
        report.append(f"✅ Validations Passed: {self.test_results['validation_passed']}")
        report.append(f"❌ Validations Failed: {self.test_results['validation_failed']}")
        report.append(f"⚠️  Errors: {len(self.test_results['errors'])}")
        report.append("")

        # Success Rate
        if self.test_results['items_expected'] > 0:
            success_rate = (self.test_results['validation_passed'] / self.test_results['items_expected']) * 100
            report.append(f"🎯 SUCCESS RATE: {success_rate:.1f}%")
        else:
            report.append("🎯 SUCCESS RATE: N/A (no items expected)")
        report.append("")

        # Test Scenarios Breakdown
        report.append("🧪 TEST SCENARIOS BREAKDOWN")
        report.append("-" * 50)

        scenario_stats = {}
        for item in self.expected_items:
            store = item['store_name']
            if store not in scenario_stats:
                scenario_stats[store] = {'total': 0, 'passed': 0}
            scenario_stats[store]['total'] += 1

        # Count passed validations by store
        try:
            conn = self.loader.db.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            for store in scenario_stats.keys():
                cur.execute("""
                    SELECT COUNT(*) as count FROM other_purchases
                    WHERE store_name = %s
                """, (store,))
                result = cur.fetchone()
                scenario_stats[store]['passed'] = result['count'] if result else 0

            cur.close()
            conn.close()

        except Exception as e:
            report.append(f"⚠️  Could not get detailed scenario stats: {e}")

        for store, stats in scenario_stats.items():
            scenario_name = store.replace('SMOKE_TEST_', '').replace('_STORE', '').title()
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report.append(f"  {scenario_name}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")

        report.append("")

        # Field Coverage Analysis
        report.append("📋 FIELD COVERAGE ANALYSIS")
        report.append("-" * 50)

        field_coverage = {
            'required_fields': ['store_name', 'item_name'],
            'optional_fields': ['variant', 'quantity', 'quantity_unit', 'price', 'original_text', 'receipt_source']
        }

        for field_type, fields in field_coverage.items():
            report.append(f"{field_type.replace('_', ' ').title()}:")
            for field in fields:
                items_with_field = sum(1 for item in self.expected_items if field in item and item[field] is not None)
                coverage_pct = (items_with_field / len(self.expected_items)) * 100 if self.expected_items else 0
                report.append(f"  {field}: {items_with_field}/{len(self.expected_items)} ({coverage_pct:.1f}%)")
            report.append("")

        # Data Type Testing
        report.append("🔢 DATA TYPE TESTING")
        report.append("-" * 50)

        data_types_tested = {
            'Price Formats': ['Zero price (0.00)', 'High price (999.99)', 'Decimal price (3.333)', 'No price (NULL)'],
            'Quantity Variations': ['Single items (1)', 'Multiple items (2-15)', 'Bulk quantities (10+)'],
            'Text Formats': ['Special characters (!@#$%)', 'Unicode (café, français)', 'Numbers in text (123)'],
            'Store Types': ['Complete Store', 'Minimal Store', 'Pharmacy', 'Grocery', 'Mixed Store']
        }

        for category, types in data_types_tested.items():
            report.append(f"{category}:")
            for data_type in types:
                report.append(f"  ✅ {data_type}")
            report.append("")

        # Error Details
        if self.test_results['errors']:
            report.append("❌ ERROR DETAILS")
            report.append("-" * 50)
            for i, error in enumerate(self.test_results['errors'], 1):
                report.append(f"{i}. {error}")
            report.append("")

        # Database Statistics
        try:
            db_stats = self.loader.get_database_stats()
            if db_stats:
                report.append("💾 DATABASE STATISTICS")
                report.append("-" * 50)
                report.append(f"Total Records: {db_stats.get('total_records', 'N/A')}")
                report.append(f"Recent Records (30 days): {db_stats.get('recent_records', 'N/A')}")

                if 'stores' in db_stats and db_stats['stores']:
                    report.append("Records by Store:")
                    for store, count in db_stats['stores'].items():
                        if store.startswith('SMOKE_TEST_'):
                            store_display = store.replace('SMOKE_TEST_', '').replace('_STORE', '').title()
                            report.append(f"  {store_display}: {count} items")
                report.append("")
        except Exception as e:
            report.append(f"⚠️  Could not get database statistics: {e}")
            report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 50)

        if self.test_results['validation_failed'] == 0:
            report.append("✅ All validations passed! System is working correctly.")
            report.append("✅ Data integrity maintained across all test scenarios.")
            report.append("✅ Ready for production use with diverse data formats.")
        else:
            report.append("⚠️  Some validations failed. Review error details above.")
            report.append("🔧 Check data processing logic for failed scenarios.")
            report.append("🔧 Verify database schema matches expected data types.")

        report.append("")
        report.append("🎯 NEXT STEPS")
        report.append("-" * 50)
        report.append("1. Review any failed validations and fix issues")
        report.append("2. Add more test scenarios if needed")
        report.append("3. Run integration tests with receipt matcher")
        report.append("4. Deploy to production environment")
        report.append("")
        report.append("=" * 70)
        report.append("🔥 END OF SMOKE TEST REPORT")

        return "\n".join(report)

    def cleanup_test_environment(self):
        """Clean up test environment"""
        logger.info("🧹 CLEANING UP TEST ENVIRONMENT")

        try:
            # Clean database test data
            self._cleanup_test_data()

            # Remove test directory
            if self.test_dir and Path(self.test_dir).exists():
                shutil.rmtree(self.test_dir)
                logger.info(f"🗑️  Removed test directory: {self.test_dir}")

            logger.info("✅ TEST ENVIRONMENT CLEANED UP")

        except Exception as e:
            logger.warning(f"⚠️  Cleanup warning: {e}")

    def run_complete_smoke_test(self):
        """Run the complete smoke test suite"""
        logger.info("🔥 STARTING COMPREHENSIVE OTHER PURCHASES SMOKE TEST")
        logger.info("=" * 70)

        success = True

        try:
            # Setup
            self.setup_test_environment()

            # Create test data
            self.create_test_data_files()

            # Run loader
            if not self.run_loader():
                success = False

            # Validate results
            if not self.validate_database_data():
                success = False

            # Generate report
            report = self.generate_detailed_report()

            # Print report
            print("\n" + report)

            # Final status
            if success:
                logger.info("🎉 SMOKE TEST COMPLETED SUCCESSFULLY!")
                return True
            else:
                logger.error("❌ SMOKE TEST FAILED - SEE REPORT FOR DETAILS")
                return False

        except Exception as e:
            logger.error(f"💥 SMOKE TEST EXECUTION FAILED: {e}")
            return False
        finally:
            # Always cleanup
            self.cleanup_test_environment()

def main():
    """Main entry point for smoke test"""
    print("🔥 OTHER PURCHASES LOADER COMPREHENSIVE SMOKE TEST")
    print("=" * 70)
    print("Testing 30-50 items across diverse scenarios:")
    print("• Complete data with all fields")
    print("• Minimal data with only required fields")
    print("• Mixed field combinations")
    print("• Edge cases and special characters")
    print("• Multiple stores and receipt sources")
    print("• Various price formats and quantities")
    print("=" * 70)

    smoke_test = OtherPurchasesSmokeTest()
    success = smoke_test.run_complete_smoke_test()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
