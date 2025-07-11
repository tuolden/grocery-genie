#!/usr/bin/env python3
"""
Health check script for Grocery Genie Docker container
"""
import os
import sys
import psycopg2
from scripts.grocery_db import get_db_connection

def check_database_connection():
    """Check if database connection is working"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def check_file_system():
    """Check if required directories exist and are writable"""
    required_dirs = ['data', 'logs', 'raw']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"Required directory missing: {dir_name}")
            return False
        if not os.access(dir_name, os.W_OK):
            print(f"Directory not writable: {dir_name}")
            return False
    return True

def main():
    """Main health check function"""
    print("Running Grocery Genie health check...")
    
    # Check file system
    if not check_file_system():
        print("❌ File system health check failed")
        sys.exit(1)
    
    # Check database connection (only if DB credentials are available)
    if os.getenv('DB_HOST'):
        if not check_database_connection():
            print("❌ Database health check failed")
            sys.exit(1)
        print("✅ Database connection healthy")
    else:
        print("ℹ️  Database credentials not configured, skipping DB check")
    
    print("✅ All health checks passed")
    sys.exit(0)

if __name__ == "__main__":
    main()
