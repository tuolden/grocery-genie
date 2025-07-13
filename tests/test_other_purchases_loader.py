#!/usr/bin/env python3
"""
Unit and Integration Tests for Other Purchases Loader

Comprehensive test suite for the other_purchases_loader.py module
including unit tests, integration tests, and edge case validation.

Author: AI Agent
Date: 2025-07-11
"""

import unittest
import os
import sys
import tempfile
import yaml
import json
from datetime import datetime, date, time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.loaders.other_purchases_loader import OtherPurchasesLoader


class TestOtherPurchasesLoader(unittest.TestCase):
    """Unit tests for OtherPurchasesLoader class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.loader = OtherPurchasesLoader(data_dir=self.test_dir)

        # Sample valid YAML data
        self.valid_yaml_data = {
            "store_name": "Test Store",
            "items": [
                {"item_name": "Test Item 1", "variant": "large", "quantity": 2, "price": 5.99},
                {"item_name": "Test Item 2", "quantity": 1, "price": 3.49},
            ],
        }

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """Test OtherPurchasesLoader initialization"""
        loader = OtherPurchasesLoader(data_dir="./test_data")

        self.assertEqual(str(loader.data_dir), "test_data")
        self.assertIsNotNone(loader.db)
        self.assertIsInstance(loader.processed_files, set)
        self.assertIsNotNone(loader.file_pattern)

    def test_validate_filename_valid(self):
        """Test filename validation with valid filenames"""
        valid_filenames = [
            "2025-07-10T14-30-00.yaml",
            "2023-01-01T00-00-00.yaml",
            "2024-12-31T23-59-59.yaml",
        ]

        for filename in valid_filenames:
            with self.subTest(filename=filename):
                self.assertTrue(self.loader._validate_filename(filename))

    def test_validate_filename_invalid(self):
        """Test filename validation with invalid filenames"""
        invalid_filenames = [
            "2025-07-10.yaml",  # Missing time
            "2025-7-10T14-30-00.yaml",  # Single digit month
            "2025-07-10T14:30:00.yaml",  # Colons instead of dashes
            "receipt.yaml",  # No datetime
            "2025-07-10T14-30-00.txt",  # Wrong extension
            "2025-13-10T14-30-00.yaml",  # Invalid month
            "2025-07-32T14-30-00.yaml",  # Invalid day
            "2025-07-10T25-30-00.yaml",  # Invalid hour
        ]

        for filename in invalid_filenames:
            with self.subTest(filename=filename):
                self.assertFalse(self.loader._validate_filename(filename))

    def test_parse_datetime_from_filename(self):
        """Test datetime parsing from filename"""
        filename = "2025-07-10T14-30-00.yaml"

        parsed_date, parsed_time = self.loader._parse_datetime_from_filename(filename)

        self.assertEqual(parsed_date, date(2025, 7, 10))
        self.assertEqual(parsed_time, time(14, 30, 0))

    def test_parse_datetime_from_filename_invalid(self):
        """Test datetime parsing with invalid filename"""
        invalid_filename = "invalid-format.yaml"

        with self.assertRaises(ValueError):
            self.loader._parse_datetime_from_filename(invalid_filename)

    def test_validate_yaml_data_valid(self):
        """Test YAML data validation with valid data"""
        self.assertTrue(self.loader._validate_yaml_data(self.valid_yaml_data, "test.yaml"))

    def test_validate_yaml_data_missing_store_name(self):
        """Test YAML data validation with missing store_name"""
        invalid_data = {"items": [{"item_name": "Test Item"}]}

        self.assertFalse(self.loader._validate_yaml_data(invalid_data, "test.yaml"))

    def test_validate_yaml_data_missing_items(self):
        """Test YAML data validation with missing items"""
        invalid_data = {"store_name": "Test Store"}

        self.assertFalse(self.loader._validate_yaml_data(invalid_data, "test.yaml"))

    def test_validate_yaml_data_empty_items(self):
        """Test YAML data validation with empty items list"""
        invalid_data = {"store_name": "Test Store", "items": []}

        self.assertFalse(self.loader._validate_yaml_data(invalid_data, "test.yaml"))

    def test_validate_yaml_data_invalid_item_structure(self):
        """Test YAML data validation with invalid item structure"""
        invalid_data = {
            "store_name": "Test Store",
            "items": [
                "invalid_item_string",  # Should be dict
                {"item_name": "Valid Item"},
            ],
        }

        self.assertFalse(self.loader._validate_yaml_data(invalid_data, "test.yaml"))

    def test_validate_yaml_data_missing_item_name(self):
        """Test YAML data validation with missing item_name"""
        invalid_data = {
            "store_name": "Test Store",
            "items": [
                {"quantity": 1, "price": 5.99}  # Missing item_name
            ],
        }

        self.assertFalse(self.loader._validate_yaml_data(invalid_data, "test.yaml"))

    def test_load_yaml_file_valid(self):
        """Test loading valid YAML file"""
        # Create test YAML file
        test_file = Path(self.test_dir) / "test.yaml"
        with open(test_file, "w") as f:
            yaml.dump(self.valid_yaml_data, f)

        loaded_data = self.loader._load_yaml_file(test_file)

        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["store_name"], "Test Store")
        self.assertEqual(len(loaded_data["items"]), 2)

    def test_load_yaml_file_invalid_yaml(self):
        """Test loading invalid YAML file"""
        # Create invalid YAML file
        test_file = Path(self.test_dir) / "invalid.yaml"
        with open(test_file, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        loaded_data = self.loader._load_yaml_file(test_file)

        self.assertIsNone(loaded_data)

    def test_load_yaml_file_empty(self):
        """Test loading empty YAML file"""
        # Create empty YAML file
        test_file = Path(self.test_dir) / "empty.yaml"
        test_file.touch()

        loaded_data = self.loader._load_yaml_file(test_file)

        self.assertIsNone(loaded_data)

    def test_load_yaml_file_nonexistent(self):
        """Test loading non-existent YAML file"""
        test_file = Path(self.test_dir) / "nonexistent.yaml"

        loaded_data = self.loader._load_yaml_file(test_file)

        self.assertIsNone(loaded_data)

    def test_get_yaml_files_empty_directory(self):
        """Test getting YAML files from empty directory"""
        yaml_files = self.loader.get_yaml_files()

        self.assertEqual(len(yaml_files), 0)

    def test_get_yaml_files_with_valid_files(self):
        """Test getting YAML files with valid files in directory"""
        # Create test files
        valid_files = ["2025-07-10T14-30-00.yaml", "2025-07-11T09-15-30.yaml"]

        invalid_files = ["invalid.yaml", "2025-07-10.yaml", "not-yaml.txt"]

        # Create valid files
        for filename in valid_files:
            test_file = Path(self.test_dir) / filename
            with open(test_file, "w") as f:
                yaml.dump(self.valid_yaml_data, f)

        # Create invalid files
        for filename in invalid_files:
            test_file = Path(self.test_dir) / filename
            test_file.touch()

        yaml_files = self.loader.get_yaml_files()

        # Should only return valid files
        self.assertEqual(len(yaml_files), 2)

        # Check filenames
        returned_filenames = [f.name for f in yaml_files]
        for filename in valid_files:
            self.assertIn(filename, returned_filenames)


class TestOtherPurchasesLoaderIntegration(unittest.TestCase):
    """Integration tests that require database connection"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.loader = OtherPurchasesLoader(data_dir=self.test_dir)

        # Sample test data
        self.test_yaml_data = {
            "store_name": "Integration Test Store",
            "receipt_source": "test",
            "items": [
                {
                    "item_name": "Integration Test Item",
                    "variant": "test variant",
                    "quantity": 1,
                    "quantity_unit": "piece",
                    "price": 9.99,
                    "original_text": "TEST ITEM",
                }
            ],
        }

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up test data from database
        try:
            conn = self.loader.db.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM other_purchases WHERE store_name LIKE '%Test%'")
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass

        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_table_creation(self):
        """Test that database tables are created properly"""
        try:
            conn = self.loader.db.get_connection()
            cur = conn.cursor()

            # Check if other_purchases table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'other_purchases'
                )
            """)

            table_exists = cur.fetchone()[0]
            self.assertTrue(table_exists)

            cur.close()
            conn.close()

        except Exception as e:
            self.fail(f"Database table creation test failed: {e}")

    def test_process_yaml_file_integration(self):
        """Test processing a complete YAML file with database integration"""
        # Create test YAML file
        test_file = Path(self.test_dir) / "2025-07-10T14-30-00.yaml"
        with open(test_file, "w") as f:
            yaml.dump(self.test_yaml_data, f)

        # Process the file
        success = self.loader.process_yaml_file(test_file)

        self.assertTrue(success)

        # Verify data was inserted into database
        conn = self.loader.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute(
                """
                SELECT * FROM other_purchases 
                WHERE store_name = %s AND item_name = %s
            """,
                ("Integration Test Store", "Integration Test Item"),
            )

            records = cur.fetchall()
            self.assertEqual(len(records), 1)

            record = records[0]
            self.assertEqual(record["store_name"], "Integration Test Store")
            self.assertEqual(record["item_name"], "Integration Test Item")
            self.assertEqual(record["variant"], "test variant")
            self.assertEqual(record["quantity"], 1)
            self.assertEqual(float(record["price"]), 9.99)

        finally:
            cur.close()
            conn.close()


def run_other_purchases_tests():
    """Run all other purchases loader tests"""
    print("🧪 STARTING OTHER PURCHASES LOADER TESTS")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOtherPurchasesLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestOtherPurchasesLoaderIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("🧪 OTHER PURCHASES LOADER TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n⚠️  ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n🎉 ALL OTHER PURCHASES LOADER TESTS PASSED!")
    else:
        print("\n❌ SOME OTHER PURCHASES LOADER TESTS FAILED!")

    return success


if __name__ == "__main__":
    success = run_other_purchases_tests()
    exit(0 if success else 1)
