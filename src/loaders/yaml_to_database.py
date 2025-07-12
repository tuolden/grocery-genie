# ruff: noqa: PLR0911
"""
YAML to Database Loader
Loads Costco receipt YAML files into the database.

This script:
1. Scans ./data/costco/ for YAML files
2. Parses each receipt
3. Inserts data into the database
4. Tracks processed files to avoid duplicates
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from src.scripts.grocery_db import GroceryDB


def safe_int(value, default=1):
    """Safely convert a value to integer."""
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.isdigit():
                return int(value)
            if value == "":
                return default
            # Try to extract number from string like "2.0" or "2 items"
            import re

            match = re.search(r"\d+", str(value))
            return int(match.group()) if match else default
        if isinstance(value, float):
            return int(value)
        return default
    except (ValueError, TypeError, AttributeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            if value == "" or value is None:
                return default
            # Remove any non-numeric characters except decimal point and minus
            import re

            cleaned = re.sub(r"[^\d.-]", "", str(value))
            return float(cleaned) if cleaned else default
        return default
    except (ValueError, TypeError):
        return default


def load_yaml_file(filepath):
    """Load and parse a YAML receipt file."""
    try:
        with open(filepath) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def convert_receipt_to_db_format(yaml_data, filename):
    """Convert YAML receipt data to database format."""
    try:
        receipt_info = yaml_data.get("receipt_info", {})
        store_info = yaml_data.get("store_info", {})
        financial = yaml_data.get("financial_summary", {})
        items = yaml_data.get("items", [])
        payments = yaml_data.get("payment_methods", [])

        db_items = []

        # Parse transaction date/time
        transaction_datetime = receipt_info.get("transaction_datetime", "")
        transaction_date = None
        transaction_time = None

        if transaction_datetime:
            try:
                dt = datetime.fromisoformat(transaction_datetime.replace("Z", "+00:00"))
                transaction_date = dt.strftime("%Y-%m-%d")
                transaction_time = dt.strftime("%H:%M:%S")
            except Exception:  # noqa: S110
                # Try to extract from filename if datetime parsing fails
                try:
                    # Filename format: 2025-06-13T18-43-00.yaml
                    date_part = filename.replace(".yaml", "").replace("-", ":")
                    dt = datetime.fromisoformat(date_part)
                    transaction_date = dt.strftime("%Y-%m-%d")
                    transaction_time = dt.strftime("%H:%M:%S")
                except Exception:  # noqa: S110
                    pass

        # Process each item in the receipt
        for item in items:
            # Combine item descriptions
            desc1 = item.get("item_description_01", "")
            desc2 = item.get("item_description_02", "")
            full_description = f"{desc1} {desc2}".strip()

            # Determine if it's a fuel item
            fuel_info = item.get("fuel_info", {})
            is_fuel = bool(
                fuel_info.get("fuel_unit_quantity") or fuel_info.get("fuel_grade_code")
            )

            db_item = {
                "purchase_date": transaction_date,
                "purchase_time": transaction_time,
                "store_location": f"{receipt_info.get('warehouse_name', '')} #{receipt_info.get('warehouse_number', '')}".strip(),
                "receipt_number": receipt_info.get("transaction_barcode", ""),
                "item_code": item.get("item_number", ""),
                "item_name": full_description or "Unknown Item",
                "item_price": safe_float(item.get("amount", 0)),
                "item_quantity": safe_int(item.get("unit", 1)),
                "item_unit_price": safe_float(item.get("item_unit_price_amount", 0)),
                "tax_indicator": item.get("tax_flag", ""),
                "item_type": receipt_info.get("receipt_type", ""),
                "item_department": item.get("item_department_number", ""),
                "discount_reference": None,  # Could be enhanced later
                "discount_amount": None,  # Could be enhanced later
                "subtotal": safe_float(financial.get("subtotal", 0)),
                "tax_total": safe_float(financial.get("taxes", 0)),
                "total_amount": safe_float(financial.get("total", 0)),
                "membership_number": receipt_info.get("membership_number", ""),
                "warehouse_number": receipt_info.get("warehouse_number", ""),
                "transaction_number": receipt_info.get("transaction_number", ""),
                "register_number": receipt_info.get("register_number", ""),
                "operator_number": receipt_info.get("operator_number", ""),
                "instant_savings": safe_float(financial.get("instant_savings", 0)),
                "fuel_quantity": safe_float(fuel_info.get("fuel_unit_quantity", 0))
                if is_fuel
                else None,
                "fuel_grade": fuel_info.get("fuel_grade_description", "")
                if is_fuel
                else None,
                "fuel_unit_price": safe_float(item.get("item_unit_price_amount", 0))
                if is_fuel
                else None,
                "payment_method": ", ".join(
                    [
                        p.get("tender_type_name", p.get("tender_description", ""))
                        for p in payments
                    ]
                ),
                "store_address": f"{store_info.get('warehouse_address1', '')} {store_info.get('warehouse_city', '')} {store_info.get('warehouse_state', '')}".strip(),
                "raw_data": yaml_data,  # Store complete YAML data for reference
            }

            db_items.append(db_item)

        return db_items

    except Exception as e:
        print(f"❌ Error converting receipt data: {e}")
        return []


def get_processed_files():
    """Get list of already processed files from database or tracking file."""
    try:
        # Simple tracking using a text file
        tracking_file = "./data/costco/processed_files.txt"
        if os.path.exists(tracking_file):
            with open(tracking_file) as f:
                return {line.strip() for line in f.readlines()}
        return set()
    except Exception:  # noqa: S110
        return set()


def mark_file_processed(filename):
    """Mark a file as processed."""
    try:
        tracking_file = "./data/costco/processed_files.txt"
        os.makedirs(os.path.dirname(tracking_file), exist_ok=True)
        with open(tracking_file, "a") as f:
            f.write(f"{filename}\n")
    except Exception as e:
        print(f"⚠️ Could not mark file as processed: {e}")


def load_all_yaml_files():
    """Load all YAML files from ./data/costco/ into the database."""

    print("📁 YAML to Database Loader")
    print("=" * 50)

    # Check if data directory exists
    data_dir = "./data/costco"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        print("💡 Run the Costco scraper first to generate YAML files")
        return False

    # Get all YAML files
    yaml_files = list(Path(data_dir).glob("*.yaml"))
    if not yaml_files:
        print(f"❌ No YAML files found in {data_dir}")
        print("💡 Run the Costco scraper first to generate YAML files")
        return False

    print(f"📄 Found {len(yaml_files)} YAML files")

    # Get already processed files
    processed_files = get_processed_files()
    new_files = [f for f in yaml_files if f.name not in processed_files]

    if not new_files:
        print("✅ All files already processed!")
        print(f"📊 Total files: {len(yaml_files)}")
        print(f"📊 Already processed: {len(processed_files)}")
        return True

    print(f"🆕 New files to process: {len(new_files)}")
    print(f"📊 Already processed: {len(processed_files)}")

    # Initialize database
    try:
        db = GroceryDB()
        db.ensure_grocery_tables()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Process each new file
    total_items = 0
    successful_files = 0
    failed_files = 0

    for yaml_file in new_files:
        print(f"\n📄 Processing: {yaml_file.name}")

        try:
            # Load YAML data
            yaml_data = load_yaml_file(yaml_file)
            if not yaml_data:
                failed_files += 1
                continue

            # Convert to database format
            db_items = convert_receipt_to_db_format(yaml_data, yaml_file.name)
            if not db_items:
                print(f"⚠️ No items found in {yaml_file.name}")
                failed_files += 1
                continue

            # Insert into database
            success_count, error_count = db.insert_costco_purchases_batch(db_items)

            if success_count > 0:
                print(f"✅ Inserted {success_count} items from {yaml_file.name}")
                total_items += success_count
                successful_files += 1
                mark_file_processed(yaml_file.name)
            else:
                print(f"❌ Failed to insert items from {yaml_file.name}")
                failed_files += 1

            if error_count > 0:
                print(f"⚠️ {error_count} items had errors")

        except Exception as e:
            print(f"❌ Error processing {yaml_file.name}: {e}")
            failed_files += 1
            continue

    # Final summary
    print("\n🎉 YAML TO DATABASE IMPORT COMPLETED!")
    print("=" * 50)
    print("📊 SUMMARY:")
    print(f"   ✅ Successful files: {successful_files}")
    print(f"   ❌ Failed files: {failed_files}")
    print(f"   📦 Total items imported: {total_items}")
    print(f"   📁 Data location: {data_dir}")

    if successful_files > 0:
        print("\n💡 Your Costco data is now in the database!")
        print("🔍 You can query it using the grocery_db module")

    return successful_files > 0


if __name__ == "__main__":
    load_all_yaml_files()
