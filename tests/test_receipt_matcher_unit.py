#!/usr/bin/env python3
"""
Unit Tests for Receipt Matcher System

Comprehensive unit tests covering all components of the receipt matcher
system with isolated testing of individual functions and methods.

Author: AI Agent
Date: 2025-07-11
"""

import unittest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.services.receipt_matcher import ReceiptMatcher, PurchaseItem, ListItem, MatchResult

class TestReceiptMatcherUnit(unittest.TestCase):
    """Unit tests for ReceiptMatcher class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.matcher = ReceiptMatcher(lookback_hours=24)
        
        # Sample test data
        self.sample_purchase = PurchaseItem(
            item_name="Test Bananas",
            store="costco",
            purchase_date=datetime.now(),
            quantity=2,
            price=3.99,
            table_source="costco_purchases",
            raw_data={"test": "data"}
        )
        
        self.sample_list_item = ListItem(
            id=1,
            item_name="Test Bananas",
            store="costco",
            is_checked=False,
            table_source="costco_list"
        )
    
    def test_initialization(self):
        """Test ReceiptMatcher initialization"""
        matcher = ReceiptMatcher(lookback_hours=48)
        
        self.assertEqual(matcher.lookback_hours, 48)
        self.assertEqual(matcher.match_threshold, 0.8)
        self.assertIsNotNone(matcher.db)
        
        # Test table mappings
        self.assertIn('costco', matcher.purchase_tables)
        self.assertIn('walmart', matcher.purchase_tables)
        self.assertIn('cvs', matcher.purchase_tables)
        self.assertIn('publix', matcher.purchase_tables)
        
        self.assertIn('costco', matcher.list_tables)
        self.assertIn('walmart', matcher.list_tables)
        self.assertIn('cvs', matcher.list_tables)
        self.assertIn('publix', matcher.list_tables)
    
    def test_calculate_similarity_exact_match(self):
        """Test exact string matching"""
        similarity = self.matcher.calculate_similarity("bananas", "bananas")
        self.assertEqual(similarity, 1.0)
        
        # Case insensitive
        similarity = self.matcher.calculate_similarity("BANANAS", "bananas")
        self.assertEqual(similarity, 1.0)
        
        # With whitespace
        similarity = self.matcher.calculate_similarity("  bananas  ", "bananas")
        self.assertEqual(similarity, 1.0)
    
    def test_calculate_similarity_fuzzy_match(self):
        """Test fuzzy string matching"""
        # Similar strings
        similarity = self.matcher.calculate_similarity("bananas", "banana")
        self.assertGreater(similarity, 0.8)
        
        # Partial match
        similarity = self.matcher.calculate_similarity("organic bananas", "bananas")
        self.assertGreater(similarity, 0.5)
        
        # No match
        similarity = self.matcher.calculate_similarity("bananas", "apples")
        self.assertLess(similarity, 0.5)
    
    def test_calculate_similarity_edge_cases(self):
        """Test edge cases for similarity calculation"""
        # Empty strings
        similarity = self.matcher.calculate_similarity("", "")
        self.assertEqual(similarity, 1.0)
        
        # One empty string
        similarity = self.matcher.calculate_similarity("bananas", "")
        self.assertEqual(similarity, 0.0)
        
        # Very different strings
        similarity = self.matcher.calculate_similarity("a", "xyz")
        self.assertLess(similarity, 0.5)
    
    @patch('src.services.receipt_matcher.GroceryDB')
    def test_get_recent_purchases_mock(self, mock_db_class):
        """Test get_recent_purchases with mocked database"""
        # Mock database connection and cursor
        mock_db = Mock()
        mock_conn = Mock()
        mock_cur = Mock()
        
        mock_db_class.return_value = mock_db
        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock query results
        mock_cur.fetchall.return_value = [
            {
                'item_name': 'Test Item',
                'purchase_date': datetime.now().date(),
                'purchase_time': datetime.now().time(),
                'item_quantity': 1,
                'item_price': 5.99,
                'raw_data': {'test': 'data'}
            }
        ]
        
        matcher = ReceiptMatcher(lookback_hours=24)
        purchases = matcher.get_recent_purchases()
        
        # Verify database calls
        mock_db.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    def test_find_matches_same_store(self):
        """Test finding matches for same store purchases"""
        purchases = [self.sample_purchase]
        list_items = [self.sample_list_item]
        
        matches = self.matcher.find_matches(purchases, list_items)
        
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.action, 'mark_checked')
        self.assertEqual(match.match_score, 1.0)
        self.assertEqual(match.purchase_item, self.sample_purchase)
        self.assertEqual(match.list_item, self.sample_list_item)
    
    def test_find_matches_cross_store(self):
        """Test finding matches for cross-store purchases"""
        # Purchase from walmart, item in costco list
        walmart_purchase = PurchaseItem(
            item_name="Test Bananas",
            store="walmart",
            purchase_date=datetime.now(),
            quantity=1,
            price=2.99,
            table_source="walmart_purchases",
            raw_data={}
        )
        
        purchases = [walmart_purchase]
        list_items = [self.sample_list_item]  # costco list item
        
        matches = self.matcher.find_matches(purchases, list_items)
        
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.action, 'remove_from_other_lists')
        self.assertEqual(match.match_score, 1.0)
    
    def test_find_matches_no_match(self):
        """Test finding matches when no matches exist"""
        no_match_purchase = PurchaseItem(
            item_name="Random Item",
            store="costco",
            purchase_date=datetime.now(),
            quantity=1,
            price=1.99,
            table_source="costco_purchases",
            raw_data={}
        )
        
        purchases = [no_match_purchase]
        list_items = [self.sample_list_item]
        
        matches = self.matcher.find_matches(purchases, list_items)
        
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.action, 'no_action')
        self.assertEqual(match.match_score, 0.0)
        self.assertIsNone(match.list_item)
    
    def test_find_matches_already_checked(self):
        """Test that already checked items are skipped"""
        checked_list_item = ListItem(
            id=1,
            item_name="Test Bananas",
            store="costco",
            is_checked=True,  # Already checked
            table_source="costco_list"
        )
        
        purchases = [self.sample_purchase]
        list_items = [checked_list_item]
        
        matches = self.matcher.find_matches(purchases, list_items)
        
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.action, 'no_action')
        self.assertIsNone(match.list_item)
    
    def test_find_matches_threshold(self):
        """Test matching threshold behavior"""
        # Item below threshold
        low_similarity_purchase = PurchaseItem(
            item_name="Completely Different Item",
            store="costco",
            purchase_date=datetime.now(),
            quantity=1,
            price=1.99,
            table_source="costco_purchases",
            raw_data={}
        )
        
        purchases = [low_similarity_purchase]
        list_items = [self.sample_list_item]
        
        matches = self.matcher.find_matches(purchases, list_items)
        
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.action, 'no_action')
        self.assertIsNone(match.list_item)
    
    def test_match_result_dataclass(self):
        """Test MatchResult dataclass"""
        match = MatchResult(
            purchase_item=self.sample_purchase,
            list_item=self.sample_list_item,
            match_score=0.95,
            action='mark_checked'
        )
        
        self.assertEqual(match.purchase_item, self.sample_purchase)
        self.assertEqual(match.list_item, self.sample_list_item)
        self.assertEqual(match.match_score, 0.95)
        self.assertEqual(match.action, 'mark_checked')
    
    def test_purchase_item_dataclass(self):
        """Test PurchaseItem dataclass"""
        purchase = PurchaseItem(
            item_name="Test Item",
            store="costco",
            purchase_date=datetime.now(),
            quantity=2,
            price=5.99,
            table_source="costco_purchases",
            raw_data={"key": "value"}
        )
        
        self.assertEqual(purchase.item_name, "Test Item")
        self.assertEqual(purchase.store, "costco")
        self.assertEqual(purchase.quantity, 2)
        self.assertEqual(purchase.price, 5.99)
        self.assertEqual(purchase.table_source, "costco_purchases")
        self.assertIsInstance(purchase.raw_data, dict)
    
    def test_list_item_dataclass(self):
        """Test ListItem dataclass"""
        list_item = ListItem(
            id=123,
            item_name="Test Item",
            store="walmart",
            is_checked=False,
            table_source="walmart_list"
        )
        
        self.assertEqual(list_item.id, 123)
        self.assertEqual(list_item.item_name, "Test Item")
        self.assertEqual(list_item.store, "walmart")
        self.assertFalse(list_item.is_checked)
        self.assertEqual(list_item.table_source, "walmart_list")

class TestReceiptMatcherIntegration(unittest.TestCase):
    """Integration tests that require database connection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.matcher = ReceiptMatcher(lookback_hours=1)
    
    def test_table_creation(self):
        """Test that ensure_tables_exist works"""
        try:
            self.matcher.ensure_tables_exist()
            # If no exception is raised, test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Table creation failed: {e}")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            conn = self.matcher.db.get_connection()
            self.assertIsNotNone(conn)
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

class TestReceiptMatcherEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.matcher = ReceiptMatcher(lookback_hours=24)
    
    def test_empty_purchases_list(self):
        """Test behavior with empty purchases list"""
        purchases = []
        list_items = [ListItem(1, "Test", "costco", False, "costco_list")]
        
        matches = self.matcher.find_matches(purchases, list_items)
        self.assertEqual(len(matches), 0)
    
    def test_empty_list_items(self):
        """Test behavior with empty list items"""
        purchases = [PurchaseItem("Test", "costco", datetime.now(), 1, 1.99, "costco_purchases", {})]
        list_items = []
        
        matches = self.matcher.find_matches(purchases, list_items)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].action, 'no_action')
    
    def test_both_empty_lists(self):
        """Test behavior with both empty lists"""
        purchases = []
        list_items = []
        
        matches = self.matcher.find_matches(purchases, list_items)
        self.assertEqual(len(matches), 0)
    
    def test_special_characters_in_names(self):
        """Test handling of special characters in item names"""
        special_name = "Test Item (2 lb) - Organic & Fresh!"
        
        similarity = self.matcher.calculate_similarity(special_name, special_name)
        self.assertEqual(similarity, 1.0)
        
        # Test with similar but different special chars
        similar_name = "Test Item 2 lb Organic Fresh"
        similarity = self.matcher.calculate_similarity(special_name, similar_name)
        self.assertGreater(similarity, 0.5)
    
    def test_very_long_item_names(self):
        """Test handling of very long item names"""
        long_name = "A" * 500  # Very long name
        short_name = "A" * 10
        
        similarity = self.matcher.calculate_similarity(long_name, short_name)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        unicode_name1 = "Café Latté"
        unicode_name2 = "Cafe Latte"
        
        similarity = self.matcher.calculate_similarity(unicode_name1, unicode_name2)
        self.assertIsInstance(similarity, float)
        self.assertGreater(similarity, 0.5)

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 STARTING RECEIPT MATCHER UNIT TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestReceiptMatcherUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestReceiptMatcherIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestReceiptMatcherEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🧪 UNIT TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
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
        print("\n🎉 ALL UNIT TESTS PASSED!")
    else:
        print("\n❌ SOME UNIT TESTS FAILED!")
    
    return success

if __name__ == "__main__":
    success = run_unit_tests()
    exit(0 if success else 1)
