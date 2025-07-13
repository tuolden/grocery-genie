#!/usr/bin/env python3
"""
Manual Data Loaders Test Runner

This script manually runs all data loaders to test the CRON job functionality
without waiting for the scheduled time. It simulates the exact same process
that would run at 11:30-11:50 PM EST daily.

Usage:
    python scripts/run_manual_data_loaders.py [options]

Options:
    --loader LOADER    Run specific loader only (cvs, costco, walmart, publix, other)
    --verify-only      Only verify data, don't run loaders
    --staging          Use staging environment configuration
    --production       Use production environment configuration
    --verbose          Enable verbose logging

Examples:
    # Run all loaders
    python scripts/run_manual_data_loaders.py

    # Run only CVS loader
    python scripts/run_manual_data_loaders.py --loader cvs

    # Verify data only
    python scripts/run_manual_data_loaders.py --verify-only

    # Run with staging environment
    python scripts/run_manual_data_loaders.py --staging
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.grocery_db import GroceryDB


class ManualDataLoaderRunner:
    """Runs all data loaders manually for testing CRON job functionality."""

    def __init__(self, environment="local", verbose=False):
        self.environment = environment
        self.verbose = verbose
        self.start_time = datetime.now()
        
        # Set environment variables if specified
        if environment == "staging":
            os.environ["ENV"] = "staging"
        elif environment == "production":
            os.environ["ENV"] = "production"
        
        print("🚀 MANUAL DATA LOADERS TEST RUNNER")
        print("=" * 60)
        print(f"🌍 Environment: {environment}")
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def run_cvs_loader(self):
        """Run CVS data loader."""
        print("🏪 RUNNING CVS DATA LOADER")
        print("-" * 40)
        
        try:
            from loaders.cvs_data_loader import process_cvs_yaml_files
            
            # Check if data directory exists
            if not os.path.exists("data/cvs"):
                print("❌ CVS data directory not found: data/cvs")
                return False
                
            # Run the loader
            process_cvs_yaml_files("data/cvs")
            print("✅ CVS loader completed")
            return True
            
        except Exception as e:
            print(f"❌ CVS loader failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def run_costco_loader(self):
        """Run Costco data loader."""
        print("🏪 RUNNING COSTCO DATA LOADER")
        print("-" * 40)
        
        try:
            from loaders.yaml_to_database import load_all_yaml_files
            
            # Check if data directory exists
            if not os.path.exists("data/costco"):
                print("❌ Costco data directory not found: data/costco")
                return False
                
            # Run the loader
            success = load_all_yaml_files()
            if success:
                print("✅ Costco loader completed")
                return True
            else:
                print("❌ Costco loader failed")
                return False
                
        except Exception as e:
            print(f"❌ Costco loader failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def run_walmart_loader(self):
        """Run Walmart data loader."""
        print("🛒 RUNNING WALMART DATA LOADER")
        print("-" * 40)
        
        try:
            from loaders.walmart_data_loader import process_walmart_files
            
            # Check if raw directory exists
            if not os.path.exists("raw/walmart"):
                print("❌ Walmart raw directory not found: raw/walmart")
                return False
                
            # Run the loader
            process_walmart_files()
            print("✅ Walmart loader completed")
            return True
            
        except Exception as e:
            print(f"❌ Walmart loader failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def run_publix_loader(self):
        """Run Publix data loader."""
        print("🛍️ RUNNING PUBLIX DATA LOADER")
        print("-" * 40)
        
        try:
            from loaders.publix_data_processor import PublixDataProcessor
            
            # Check if raw directory exists
            if not os.path.exists("raw/publix"):
                print("❌ Publix raw directory not found: raw/publix")
                return False
                
            # Run the processor
            processor = PublixDataProcessor()
            
            # Step 1: Process raw to YAML
            yaml_count = processor.process_raw_to_yaml()
            
            if yaml_count > 0:
                # Step 2: Load YAML to database
                db_count = processor.load_yaml_to_database()
                
                if db_count > 0:
                    print("✅ Publix loader completed")
                    return True
                else:
                    print("❌ Publix database loading failed")
                    return False
            else:
                print("❌ Publix YAML processing failed")
                return False
                
        except Exception as e:
            print(f"❌ Publix loader failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def run_other_purchases_loader(self):
        """Run Other Purchases data loader."""
        print("📦 RUNNING OTHER PURCHASES LOADER")
        print("-" * 40)
        
        try:
            from loaders.other_purchases_loader import OtherPurchasesLoader
            
            # Check if data directory exists
            if not os.path.exists("data/other"):
                print("❌ Other purchases data directory not found: data/other")
                return False
                
            # Run the loader
            loader = OtherPurchasesLoader(data_dir="data/other")
            stats = loader.process_all_files()
            
            if stats["failed"] == 0:
                print("✅ Other purchases loader completed")
                return True
            else:
                print(f"❌ Other purchases loader failed: {stats['failed']} files failed")
                return False
                
        except Exception as e:
            print(f"❌ Other purchases loader failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def verify_data_loaded(self):
        """Verify that data has been loaded into all tables."""
        print("🔍 VERIFYING DATA LOADED")
        print("-" * 40)
        
        try:
            db = GroceryDB()
            
            # Check each table
            tables = [
                ("cvs_purchases", "CVS"),
                ("costco_purchases", "Costco"),
                ("walmart_purchases", "Walmart"),
                ("publix_purchases", "Publix"),
                ("other_purchases", "Other")
            ]
            
            total_records = 0
            verification_results = {}
            
            for table_name, retailer in tables:
                try:
                    count = db.get_table_count(table_name)
                    total_records += count
                    verification_results[retailer] = count
                    
                    if count > 0:
                        print(f"✅ {retailer:8}: {count:6,} records")
                    else:
                        print(f"⚠️  {retailer:8}: {count:6,} records (empty)")
                        
                except Exception as e:
                    print(f"❌ {retailer:8}: Error checking table - {e}")
                    verification_results[retailer] = -1
            
            print("-" * 40)
            print(f"📊 TOTAL RECORDS: {total_records:,}")
            
            return verification_results, total_records
            
        except Exception as e:
            print(f"❌ Data verification failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {}, 0

    def run_all_loaders(self):
        """Run all data loaders in sequence."""
        print("🔄 RUNNING ALL DATA LOADERS")
        print("=" * 60)
        
        loaders = [
            ("CVS", self.run_cvs_loader),
            ("Costco", self.run_costco_loader),
            ("Walmart", self.run_walmart_loader),
            ("Publix", self.run_publix_loader),
            ("Other", self.run_other_purchases_loader)
        ]
        
        results = {}
        
        for name, loader_func in loaders:
            print(f"\n⏰ Starting {name} loader...")
            start_time = time.time()
            
            success = loader_func()
            
            end_time = time.time()
            duration = end_time - start_time
            
            results[name] = {
                "success": success,
                "duration": duration
            }
            
            print(f"⏱️  {name} loader took {duration:.2f} seconds")
            print()
        
        return results

    def print_summary(self, loader_results, verification_results, total_records):
        """Print final summary of all operations."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("🎉 MANUAL DATA LOADERS TEST SUMMARY")
        print("=" * 60)
        print(f"🌍 Environment: {self.environment}")
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print()
        
        # Loader results
        print("📊 LOADER RESULTS:")
        successful_loaders = 0
        for name, result in loader_results.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            duration = result["duration"]
            print(f"   {name:8}: {status} ({duration:.2f}s)")
            if result["success"]:
                successful_loaders += 1
        
        print()
        
        # Data verification results
        print("🔍 DATA VERIFICATION:")
        for retailer, count in verification_results.items():
            if count > 0:
                print(f"   {retailer:8}: ✅ {count:,} records")
            elif count == 0:
                print(f"   {retailer:8}: ⚠️  0 records (no data)")
            else:
                print(f"   {retailer:8}: ❌ Error checking")
        
        print()
        print(f"📈 OVERALL RESULTS:")
        print(f"   ✅ Successful loaders: {successful_loaders}/{len(loader_results)}")
        print(f"   📊 Total records: {total_records:,}")
        
        # Final status
        if successful_loaders == len(loader_results) and total_records > 0:
            print("\n🎉 ALL TESTS PASSED! Data loading system is working correctly.")
        elif successful_loaders > 0:
            print("\n⚠️  PARTIAL SUCCESS: Some loaders worked, check failed ones.")
        else:
            print("\n❌ ALL TESTS FAILED: Data loading system needs attention.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manual Data Loaders Test Runner")
    parser.add_argument(
        "--loader",
        choices=["cvs", "costco", "walmart", "publix", "other"],
        help="Run specific loader only"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify data, don't run loaders"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Use staging environment configuration"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production environment configuration"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Determine environment
    environment = "local"
    if args.staging:
        environment = "staging"
    elif args.production:
        environment = "production"
    
    # Create runner
    runner = ManualDataLoaderRunner(environment=environment, verbose=args.verbose)
    
    # Run specific loader or all loaders
    if args.verify_only:
        # Only verify data
        verification_results, total_records = runner.verify_data_loaded()
        runner.print_summary({}, verification_results, total_records)
        
    elif args.loader:
        # Run specific loader
        loader_map = {
            "cvs": runner.run_cvs_loader,
            "costco": runner.run_costco_loader,
            "walmart": runner.run_walmart_loader,
            "publix": runner.run_publix_loader,
            "other": runner.run_other_purchases_loader
        }
        
        print(f"🎯 Running {args.loader.upper()} loader only...")
        success = loader_map[args.loader]()
        
        # Verify data
        verification_results, total_records = runner.verify_data_loaded()
        
        # Print summary
        loader_results = {args.loader.capitalize(): {"success": success, "duration": 0}}
        runner.print_summary(loader_results, verification_results, total_records)
        
    else:
        # Run all loaders
        loader_results = runner.run_all_loaders()
        
        # Verify data
        verification_results, total_records = runner.verify_data_loaded()
        
        # Print summary
        runner.print_summary(loader_results, verification_results, total_records)


if __name__ == "__main__":
    main()
