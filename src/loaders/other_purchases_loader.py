#!/usr/bin/env python3
"""
Other Purchases Loader

Loads YAML files from ./data/other/ directory into the other_purchases database table.
Follows the established pattern of other data loaders in the grocery-genie system.

File Format: YYYY-MM-DDTHH-MM-SS.yaml
Directory: ./data/other/

Features:
- Upsert logic to prevent duplicates
- Batch processing of all YAML files
- Individual file processing capability
- Comprehensive logging and error handling
- Tracks processed files

Author: AI Agent
Date: 2025-07-11
"""

import json
import logging
import os
import re
import sys
from datetime import date, datetime, time
from pathlib import Path

import yaml
from psycopg2.extras import RealDictCursor

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from src.scripts.grocery_db import GroceryDB

# Configure logging with bright colors for visibility
logging.basicConfig(
    level=logging.INFO,
    format="🔄 %(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("other_purchases_loader.log"),
    ],
)
logger = logging.getLogger(__name__)


class OtherPurchasesLoader:
    """Loader for other purchases YAML files"""

    def __init__(self, data_dir: str = "./data/other"):
        """
        Initialize the loader

        Args:
            data_dir: Directory containing YAML files (default: ./data/other)
        """
        self.data_dir = Path(data_dir)
        self.db = GroceryDB()
        self.processed_files = set()
        self.file_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.yaml$")

        logger.info("🚀 OTHER PURCHASES LOADER INITIALIZED")
        logger.info(f"📁 Data directory: {self.data_dir}")

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Ensure database tables exist
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Ensure the other_purchases table exists"""
        try:
            self.db.ensure_grocery_tables()
            logger.info("✅ Database tables ensured")
        except Exception as e:
            logger.error(f"❌ Failed to ensure database tables: {e}")
            raise

    def _validate_filename(self, filename: str) -> bool:
        """
        Validate filename matches YYYY-MM-DDTHH-MM-SS.yaml pattern and contains valid
        datetime

        Args:
            filename: Name of the file to validate

        Returns:
            bool: True if filename is valid
        """
        # First check regex pattern
        if not self.file_pattern.match(filename):
            return False

        # Then validate the actual datetime values
        try:
            self._parse_datetime_from_filename(filename)
            return True
        except (ValueError, TypeError):
            return False

    def _parse_datetime_from_filename(self, filename: str) -> tuple[date, time]:
        """
        Parse date and time from filename

        Args:
            filename: YAML filename in format YYYY-MM-DDTHH-MM-SS.yaml

        Returns:
            Tuple of (date, time) objects
        """
        # Remove .yaml extension
        datetime_str = filename.replace(".yaml", "")

        # Parse datetime
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H-%M-%S")  # noqa: DTZ007
        return dt.date(), dt.time()

    def _validate_yaml_data(self, data: dict, filename: str) -> bool:
        """
        Validate YAML data structure

        Args:
            data: Parsed YAML data
            filename: Source filename for error reporting

        Returns:
            bool: True if data is valid
        """
        required_fields = ["store_name", "items"]

        # Check required top-level fields
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing required field '{field}' in {filename}")
                return False

        # Validate items structure
        if not isinstance(data["items"], list):
            logger.error(f"❌ 'items' must be a list in {filename}")
            return False

        if not data["items"]:
            logger.error(f"❌ 'items' list is empty in {filename}")
            return False

        # Validate each item
        for i, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                logger.error(f"❌ Item {i} must be a dictionary in {filename}")
                return False

            if "item_name" not in item:
                logger.error(f"❌ Item {i} missing 'item_name' in {filename}")
                return False

        logger.info(f"✅ YAML data validation passed for {filename}")
        return True

    def _load_yaml_file(self, file_path: Path) -> dict | None:
        """
        Load and parse YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data or None if failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.error(f"❌ Empty YAML file: {file_path}")
                return None

            logger.info(f"📄 Loaded YAML file: {file_path}")
            return data

        except yaml.YAMLError as e:
            logger.error(f"❌ YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return None

    def _upsert_purchase_item(
        self,
        cur,
        item_data: dict,
        store_name: str,
        purchase_date: date,
        purchase_time: time,
        raw_data: dict,
    ) -> bool:
        """
        Upsert a single purchase item

        Args:
            cur: Database cursor
            item_data: Item data from YAML
            store_name: Store name
            purchase_date: Purchase date
            purchase_time: Purchase time
            raw_data: Complete raw YAML data

        Returns:
            bool: True if successful
        """
        try:
            # Prepare item data with defaults
            item_name = item_data["item_name"]
            variant = item_data.get("variant")
            quantity = item_data.get("quantity", 1)
            quantity_unit = item_data.get("quantity_unit")
            price = item_data.get("price")
            receipt_source = item_data.get("receipt_source", "manual")
            original_text = item_data.get("original_text")

            # Convert price to decimal if provided
            if price is not None:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    logger.warning(
                        f"⚠️  Invalid price '{price}' for item '{item_name}', "
                        f"setting to NULL"
                    )
                    price = None

            # Upsert query
            upsert_query = """
                INSERT INTO other_purchases (
                    store_name, item_name, variant, quantity, quantity_unit, price,
                    purchase_date, purchase_time, receipt_source, original_text,
                    raw_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (store_name, item_name, purchase_date, variant)
                DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    quantity_unit = EXCLUDED.quantity_unit,
                    price = EXCLUDED.price,
                    purchase_time = EXCLUDED.purchase_time,
                    receipt_source = EXCLUDED.receipt_source,
                    original_text = EXCLUDED.original_text,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
            """

            # Execute upsert
            cur.execute(
                upsert_query,
                (
                    store_name,
                    item_name,
                    variant,
                    quantity,
                    quantity_unit,
                    price,
                    purchase_date,
                    purchase_time,
                    receipt_source,
                    original_text,
                    json.dumps(raw_data),
                ),
            )

            logger.info(f"✅ Upserted item: {item_name} from {store_name}")
            return True

        except Exception as e:
            logger.error(
                f"❌ Error upserting item '{item_data.get('item_name', 'unknown')}': {e}"
            )
            return False

    def process_yaml_file(self, file_path: Path) -> bool:
        """
        Process a single YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            bool: True if successful
        """
        logger.info(f"🔄 Processing file: {file_path}")

        # Validate filename
        if not self._validate_filename(file_path.name):
            logger.error(f"❌ Invalid filename format: {file_path.name}")
            logger.error("   Expected format: YYYY-MM-DDTHH-MM-SS.yaml")
            return False

        # Parse datetime from filename
        try:
            purchase_date, purchase_time = self._parse_datetime_from_filename(
                file_path.name
            )
            logger.info(f"📅 Purchase date/time: {purchase_date} {purchase_time}")
        except Exception as e:
            logger.error(
                f"❌ Error parsing datetime from filename {file_path.name}: {e}"
            )
            return False

        # Load YAML data
        yaml_data = self._load_yaml_file(file_path)
        if not yaml_data:
            return False

        # Validate YAML structure
        if not self._validate_yaml_data(yaml_data, file_path.name):
            return False

        # Extract store name and items
        store_name = yaml_data["store_name"]
        items = yaml_data["items"]

        logger.info(f"🏪 Store: {store_name}")
        logger.info(f"📦 Items to process: {len(items)}")

        # Process items
        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            success_count = 0

            for item in items:
                if self._upsert_purchase_item(
                    cur, item, store_name, purchase_date, purchase_time, yaml_data
                ):
                    success_count += 1

            conn.commit()

            logger.info(
                f"✅ Successfully processed {success_count}/{len(items)} items from {file_path.name}"
            )

            # Mark file as processed
            self.processed_files.add(str(file_path))

            return success_count == len(items)

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error processing {file_path.name}: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    def get_yaml_files(self) -> list[Path]:
        """
        Get all YAML files in the data directory

        Returns:
            List of Path objects for valid YAML files
        """
        yaml_files = []

        if not self.data_dir.exists():
            logger.warning(f"⚠️  Data directory does not exist: {self.data_dir}")
            return yaml_files

        for file_path in self.data_dir.glob("*.yaml"):
            if self._validate_filename(file_path.name):
                yaml_files.append(file_path)
            else:
                logger.warning(f"⚠️  Skipping invalid filename: {file_path.name}")

        # Sort by filename (chronological order)
        yaml_files.sort()

        logger.info(f"📁 Found {len(yaml_files)} valid YAML files")
        return yaml_files

    def process_all_files(self) -> dict[str, int]:
        """
        Process all YAML files in the data directory

        Returns:
            Dict with processing statistics
        """
        logger.info("🚀 STARTING BATCH PROCESSING OF ALL YAML FILES")
        logger.info("=" * 60)

        yaml_files = self.get_yaml_files()

        if not yaml_files:
            logger.info("ℹ️  No YAML files found to process")
            return {"total_files": 0, "processed": 0, "failed": 0, "skipped": 0}

        stats = {
            "total_files": len(yaml_files),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
        }

        for file_path in yaml_files:
            # Skip if already processed (in current session)
            if str(file_path) in self.processed_files:
                logger.info(f"⏭️  Skipping already processed file: {file_path.name}")
                stats["skipped"] += 1
                continue

            # Process file
            if self.process_yaml_file(file_path):
                stats["processed"] += 1
            else:
                stats["failed"] += 1

        # Log summary
        logger.info("📊 BATCH PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📁 Total files found: {stats['total_files']}")
        logger.info(f"✅ Successfully processed: {stats['processed']}")
        logger.info(f"❌ Failed to process: {stats['failed']}")
        logger.info(f"⏭️  Skipped (already processed): {stats['skipped']}")
        logger.info("=" * 60)

        return stats

    def get_database_stats(self) -> dict[str, int]:
        """
        Get statistics from the other_purchases table

        Returns:
            Dict with database statistics
        """
        conn = self.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Total records
            cur.execute("SELECT COUNT(*) as total FROM other_purchases")
            total_records = cur.fetchone()["total"]

            # Records by store
            cur.execute("""
                SELECT store_name, COUNT(*) as count
                FROM other_purchases
                GROUP BY store_name
                ORDER BY count DESC
            """)
            stores = cur.fetchall()

            # Recent records (last 30 days)
            cur.execute("""
                SELECT COUNT(*) as recent
                FROM other_purchases
                WHERE purchase_date >= CURRENT_DATE - INTERVAL '30 days'
            """)
            recent_records = cur.fetchone()["recent"]

            return {
                "total_records": total_records,
                "recent_records": recent_records,
                "stores": {store["store_name"]: store["count"] for store in stores},
            }

        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {}
        finally:
            cur.close()
            conn.close()

    def show_database_summary(self):
        """Show summary of data in the database"""
        logger.info("📊 DATABASE SUMMARY")
        logger.info("=" * 50)

        stats = self.get_database_stats()

        if not stats:
            logger.error("❌ Could not retrieve database statistics")
            return

        logger.info(f"📦 Total records: {stats['total_records']}")
        logger.info(f"📅 Recent records (30 days): {stats['recent_records']}")

        if stats["stores"]:
            logger.info("🏪 Records by store:")
            for store_name, count in stats["stores"].items():
                logger.info(f"   {store_name}: {count} items")
        else:
            logger.info("🏪 No store data found")

        logger.info("=" * 50)


def main():  # noqa: PLR0911
    """Main entry point for the loader"""
    import argparse

    parser = argparse.ArgumentParser(description="Other Purchases YAML Loader")
    parser.add_argument("--file", type=str, help="Process a specific YAML file")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data/other",
        help="Data directory (default: ./data/other)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show database statistics only"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        loader = OtherPurchasesLoader(data_dir=args.data_dir)

        if args.stats:
            # Show database stats only
            loader.show_database_summary()
            return 0

        if args.file:
            # Process specific file
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                return 1

            if loader.process_yaml_file(file_path):
                logger.info("🎉 File processed successfully")
                return 0
            logger.error("❌ File processing failed")
            return 1
        # Process all files
        stats = loader.process_all_files()

        # Show database summary
        loader.show_database_summary()

        if stats["failed"] == 0:
            logger.info("🎉 All files processed successfully")
            return 0
        logger.error(f"⚠️  {stats['failed']} files failed to process")
        return 1

    except Exception as e:
        logger.error(f"💥 Loader execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
