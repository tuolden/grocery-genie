#!/usr/bin/env python3
"""
Data Verification Script

Verifies that data has been properly loaded into all grocery database tables.
This script provides detailed analysis of the data loading results and can be
used to validate that the CRON jobs are working correctly.

Usage:
    python scripts/verify_data_loaded.py [options]

Options:
    --detailed         Show detailed statistics for each table
    --recent           Show only recent data (last 30 days)
    --export           Export verification results to JSON
    --staging          Use staging database
    --production       Use production database

Examples:
    # Basic verification
    python scripts/verify_data_loaded.py

    # Detailed analysis
    python scripts/verify_data_loaded.py --detailed

    # Recent data only
    python scripts/verify_data_loaded.py --recent

    # Export results
    python scripts/verify_data_loaded.py --export
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.grocery_db import GroceryDB


class DataVerifier:
    """Verifies data loading across all grocery database tables."""

    def __init__(self, environment="local", detailed=False, recent_only=False):
        self.environment = environment
        self.detailed = detailed
        self.recent_only = recent_only
        self.verification_time = datetime.now()
        
        # Set environment variables if specified
        if environment == "staging":
            os.environ["ENV"] = "staging"
        elif environment == "production":
            os.environ["ENV"] = "production"
        
        print("🔍 DATA VERIFICATION SCRIPT")
        print("=" * 50)
        print(f"🌍 Environment: {environment}")
        print(f"📅 Verification Time: {self.verification_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if recent_only:
            print("📅 Scope: Recent data (last 30 days)")
        else:
            print("📅 Scope: All data")
        print()

    def get_table_statistics(self, table_name, retailer_name):
        """Get detailed statistics for a specific table."""
        try:
            db = GroceryDB()
            
            # Basic count
            total_count = db.get_table_count(table_name)
            
            stats = {
                "retailer": retailer_name,
                "table": table_name,
                "total_records": total_count,
                "status": "success" if total_count >= 0 else "error"
            }
            
            if total_count == 0:
                stats["status"] = "empty"
                return stats
            
            if self.detailed:
                # Get date range
                try:
                    date_query = f"""
                    SELECT 
                        MIN(purchase_date) as earliest_date,
                        MAX(purchase_date) as latest_date,
                        COUNT(DISTINCT purchase_date) as unique_dates
                    FROM {table_name}
                    WHERE purchase_date IS NOT NULL
                    """
                    
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute(date_query)
                    date_result = cur.fetchone()
                    
                    if date_result and date_result[0]:
                        stats["earliest_date"] = str(date_result[0])
                        stats["latest_date"] = str(date_result[1])
                        stats["unique_dates"] = date_result[2]
                    
                    # Get recent data count (last 30 days)
                    recent_date = (datetime.now() - timedelta(days=30)).date()
                    recent_query = f"""
                    SELECT COUNT(*) 
                    FROM {table_name} 
                    WHERE purchase_date >= %s
                    """
                    cur.execute(recent_query, (recent_date,))
                    recent_count = cur.fetchone()[0]
                    stats["recent_records"] = recent_count
                    
                    # Get item count
                    item_query = f"""
                    SELECT 
                        COUNT(DISTINCT item_name) as unique_items,
                        AVG(CAST(quantity AS FLOAT)) as avg_quantity,
                        AVG(CAST(price AS FLOAT)) as avg_price
                    FROM {table_name}
                    WHERE item_name IS NOT NULL
                    """
                    cur.execute(item_query)
                    item_result = cur.fetchone()
                    
                    if item_result:
                        stats["unique_items"] = item_result[0] or 0
                        stats["avg_quantity"] = round(float(item_result[1] or 0), 2)
                        stats["avg_price"] = round(float(item_result[2] or 0), 2)
                    
                    cur.close()
                    conn.close()
                    
                except Exception as e:
                    stats["detail_error"] = str(e)
            
            return stats
            
        except Exception as e:
            return {
                "retailer": retailer_name,
                "table": table_name,
                "total_records": -1,
                "status": "error",
                "error": str(e)
            }

    def verify_all_tables(self):
        """Verify all grocery database tables."""
        print("📊 VERIFYING ALL TABLES")
        print("-" * 50)
        
        tables = [
            ("cvs_purchases", "CVS"),
            ("costco_purchases", "Costco"),
            ("walmart_purchases", "Walmart"),
            ("publix_purchases", "Publix"),
            ("other_purchases", "Other Purchases")
        ]
        
        verification_results = []
        total_records = 0
        successful_tables = 0
        
        for table_name, retailer_name in tables:
            print(f"🔍 Checking {retailer_name}...")
            
            stats = self.get_table_statistics(table_name, retailer_name)
            verification_results.append(stats)
            
            if stats["status"] == "success":
                successful_tables += 1
                total_records += stats["total_records"]
                
                if self.detailed:
                    print(f"   ✅ {stats['total_records']:,} total records")
                    if "recent_records" in stats:
                        print(f"   📅 {stats['recent_records']:,} recent records (30 days)")
                    if "unique_items" in stats:
                        print(f"   🛒 {stats['unique_items']:,} unique items")
                    if "earliest_date" in stats and stats["earliest_date"]:
                        print(f"   📅 Date range: {stats['earliest_date']} to {stats['latest_date']}")
                else:
                    print(f"   ✅ {stats['total_records']:,} records")
                    
            elif stats["status"] == "empty":
                print(f"   ⚠️  0 records (table exists but empty)")
                
            elif stats["status"] == "error":
                print(f"   ❌ Error: {stats.get('error', 'Unknown error')}")
            
            print()
        
        return verification_results, total_records, successful_tables

    def check_data_freshness(self):
        """Check how fresh the data is across all tables."""
        print("🕐 CHECKING DATA FRESHNESS")
        print("-" * 50)
        
        tables = [
            ("cvs_purchases", "CVS"),
            ("costco_purchases", "Costco"),
            ("walmart_purchases", "Walmart"),
            ("publix_purchases", "Publix"),
            ("other_purchases", "Other Purchases")
        ]
        
        freshness_results = []
        
        try:
            db = GroceryDB()
            
            for table_name, retailer_name in tables:
                try:
                    # Get most recent record
                    query = f"""
                    SELECT MAX(purchase_date) as latest_date
                    FROM {table_name}
                    WHERE purchase_date IS NOT NULL
                    """
                    
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute(query)
                    result = cur.fetchone()
                    
                    if result and result[0]:
                        latest_date = result[0]
                        days_ago = (datetime.now().date() - latest_date).days
                        
                        freshness_results.append({
                            "retailer": retailer_name,
                            "latest_date": str(latest_date),
                            "days_ago": days_ago
                        })
                        
                        if days_ago == 0:
                            status = "🟢 Today"
                        elif days_ago <= 7:
                            status = f"🟡 {days_ago} days ago"
                        elif days_ago <= 30:
                            status = f"🟠 {days_ago} days ago"
                        else:
                            status = f"🔴 {days_ago} days ago"
                        
                        print(f"   {retailer_name:15}: {latest_date} ({status})")
                    else:
                        print(f"   {retailer_name:15}: No data with dates")
                        freshness_results.append({
                            "retailer": retailer_name,
                            "latest_date": None,
                            "days_ago": None
                        })
                    
                    cur.close()
                    conn.close()
                    
                except Exception as e:
                    print(f"   {retailer_name:15}: Error checking - {e}")
                    freshness_results.append({
                        "retailer": retailer_name,
                        "error": str(e)
                    })
        
        except Exception as e:
            print(f"❌ Database connection error: {e}")
        
        print()
        return freshness_results

    def export_results(self, verification_results, freshness_results, total_records):
        """Export verification results to JSON file."""
        export_data = {
            "verification_time": self.verification_time.isoformat(),
            "environment": self.environment,
            "summary": {
                "total_records": total_records,
                "tables_checked": len(verification_results),
                "successful_tables": len([r for r in verification_results if r["status"] == "success"])
            },
            "table_statistics": verification_results,
            "data_freshness": freshness_results
        }
        
        filename = f"data_verification_{self.environment}_{self.verification_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📄 Results exported to: {filename}")
        return filename

    def print_summary(self, verification_results, freshness_results, total_records, successful_tables):
        """Print final verification summary."""
        print("🎯 VERIFICATION SUMMARY")
        print("=" * 50)
        print(f"🌍 Environment: {self.environment}")
        print(f"📅 Verification Time: {self.verification_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("📊 OVERALL RESULTS:")
        print(f"   ✅ Successful tables: {successful_tables}/{len(verification_results)}")
        print(f"   📦 Total records: {total_records:,}")
        
        # Status breakdown
        status_counts = {}
        for result in verification_results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"   🟢 Working tables: {status_counts.get('success', 0)}")
        print(f"   🟡 Empty tables: {status_counts.get('empty', 0)}")
        print(f"   🔴 Error tables: {status_counts.get('error', 0)}")
        print()
        
        # Data freshness summary
        recent_data_count = 0
        for result in freshness_results:
            if result.get("days_ago") is not None and result["days_ago"] <= 7:
                recent_data_count += 1
        
        print("🕐 DATA FRESHNESS:")
        print(f"   📅 Tables with recent data (≤7 days): {recent_data_count}/{len(freshness_results)}")
        
        # Final assessment
        if successful_tables == len(verification_results) and total_records > 0:
            print("\n🎉 VERIFICATION PASSED: All tables have data!")
        elif successful_tables > 0:
            print("\n⚠️  PARTIAL SUCCESS: Some tables working, others need attention.")
        else:
            print("\n❌ VERIFICATION FAILED: No tables have data or all have errors.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Data Verification Script")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed statistics for each table"
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        help="Show only recent data (last 30 days)"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export verification results to JSON"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Use staging database"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production database"
    )
    
    args = parser.parse_args()
    
    # Determine environment
    environment = "local"
    if args.staging:
        environment = "staging"
    elif args.production:
        environment = "production"
    
    # Create verifier
    verifier = DataVerifier(
        environment=environment,
        detailed=args.detailed,
        recent_only=args.recent
    )
    
    # Run verification
    verification_results, total_records, successful_tables = verifier.verify_all_tables()
    
    # Check data freshness
    freshness_results = verifier.check_data_freshness()
    
    # Export if requested
    if args.export:
        verifier.export_results(verification_results, freshness_results, total_records)
        print()
    
    # Print summary
    verifier.print_summary(verification_results, freshness_results, total_records, successful_tables)


if __name__ == "__main__":
    main()
