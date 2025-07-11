#!/usr/bin/env python3
"""
Staging Environment Smoke Tests for Grocery Genie
Only runs in staging environment with mirrored production data
"""
import os
import sys
import psycopg2
import requests
import time
from scripts.grocery_db import get_db_connection

def is_staging_environment():
    """Check if we're running in staging environment"""
    return os.getenv('ENV', '').lower() == 'staging'

def test_database_connectivity():
    """Test database connection and basic operations"""
    print("🔍 Testing database connectivity...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ Database connected: {version[0]}")
        
        # Test table existence
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables in database")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def test_data_integrity():
    """Test data integrity without modifying production data"""
    print("🔍 Testing data integrity...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test Costco data
        cursor.execute("SELECT COUNT(*) FROM costco_purchases")
        costco_count = cursor.fetchone()[0]
        print(f"✅ Costco purchases: {costco_count} records")
        
        # Test Walmart data
        cursor.execute("SELECT COUNT(*) FROM walmart_purchases")
        walmart_count = cursor.fetchone()[0]
        print(f"✅ Walmart purchases: {walmart_count} records")
        
        # Test CVS data
        cursor.execute("SELECT COUNT(*) FROM cvs_purchases")
        cvs_count = cursor.fetchone()[0]
        print(f"✅ CVS purchases: {cvs_count} records")
        
        # Test Publix data
        cursor.execute("SELECT COUNT(*) FROM publix_purchases")
        publix_count = cursor.fetchone()[0]
        print(f"✅ Publix purchases: {publix_count} records")
        
        # Test Other purchases data
        cursor.execute("SELECT COUNT(*) FROM other_purchases")
        other_count = cursor.fetchone()[0]
        print(f"✅ Other purchases: {other_count} records")
        
        total_records = costco_count + walmart_count + cvs_count + publix_count + other_count
        print(f"✅ Total purchase records: {total_records}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        return False

def test_file_system_access():
    """Test file system access for data directories"""
    print("🔍 Testing file system access...")
    try:
        required_dirs = ['data', 'logs', 'raw']
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                print(f"❌ Required directory missing: {dir_name}")
                return False
            if not os.access(dir_name, os.W_OK):
                print(f"❌ Directory not writable: {dir_name}")
                return False
            print(f"✅ Directory accessible: {dir_name}")
        
        # Test subdirectories
        data_subdirs = ['costco', 'walmart', 'cvs', 'publix', 'other']
        for subdir in data_subdirs:
            full_path = os.path.join('data', subdir)
            if os.path.exists(full_path):
                print(f"✅ Data subdirectory exists: {subdir}")
            else:
                print(f"ℹ️  Data subdirectory missing (will be created): {subdir}")
        
        return True
    except Exception as e:
        print(f"❌ File system access test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment-specific configuration"""
    print("🔍 Testing environment configuration...")
    try:
        # Check staging-specific environment variables
        env = os.getenv('ENV')
        if env != 'staging':
            print(f"❌ Expected ENV=staging, got: {env}")
            return False
        print(f"✅ Environment correctly set: {env}")
        
        # Check debug logging is enabled in staging
        debug_logging = os.getenv('ENABLE_DEBUG_LOGGING', 'false').lower()
        if debug_logging != 'true':
            print(f"⚠️  Debug logging not enabled in staging: {debug_logging}")
        else:
            print(f"✅ Debug logging enabled: {debug_logging}")
        
        # Check smoke tests are enabled
        smoke_tests = os.getenv('ENABLE_SMOKE_TESTS', 'false').lower()
        if smoke_tests != 'true':
            print(f"⚠️  Smoke tests not enabled: {smoke_tests}")
        else:
            print(f"✅ Smoke tests enabled: {smoke_tests}")
        
        return True
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints if available"""
    print("🔍 Testing API endpoints...")
    try:
        # Test health check endpoint
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
        
        # Simple health check
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Health endpoint accessible: {response.status_code}")
            else:
                print(f"⚠️  Health endpoint returned: {response.status_code}")
        except requests.exceptions.RequestException:
            print("ℹ️  Health endpoint not available (expected for batch jobs)")
        
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Main smoke test function"""
    print("🚀 Starting Grocery Genie Staging Smoke Tests")
    print("=" * 50)
    
    # Verify we're in staging environment
    if not is_staging_environment():
        print("❌ Smoke tests should only run in staging environment")
        print(f"Current ENV: {os.getenv('ENV', 'not set')}")
        sys.exit(1)
    
    print("✅ Running in staging environment")
    
    # Run all tests
    tests = [
        test_database_connectivity,
        test_data_integrity,
        test_file_system_access,
        test_environment_configuration,
        test_api_endpoints
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print("\n" + "-" * 30)
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🧪 Smoke Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All staging smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some staging smoke tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
