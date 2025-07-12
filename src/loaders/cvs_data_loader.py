#!/usr/bin/env python3
"""
CVS Data Loader

Loads CVS order data from YAML files into the database.
Processes YAML files created by cvs_scraper.py.
"""

import json
import os
from datetime import date, datetime, time

import yaml

from scripts.grocery_db import GroceryDB


def parse_cvs_date(date_str: str) -> date | None:
    """Parse CVS date format like '2024-07-08T15:27:00Z'."""
    try:
        if date_str:
            # Parse ISO format date
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.date()
    except Exception as e:
        print(f"[WARNING] Could not parse date {date_str}: {e}")
    return None


def parse_cvs_time(date_str: str) -> time | None:
    """Parse CVS time format like '2024-07-08T15:27:00Z'."""
    try:
        if date_str:
            # Parse ISO format time
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.time()
    except Exception as e:
        print(f"[WARNING] Could not parse time {date_str}: {e}")
    return None


def parse_decimal(value) -> float | None:
    """Safely parse decimal values."""
    try:
        if value is None or value == "":
            return None
        return float(str(value))
    except (ValueError, TypeError):
        return None


def parse_integer(value) -> int | None:
    """Safely parse integer values."""
    try:
        if value is None or value == "":
            return None
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def load_cvs_order_to_database(db: GroceryDB, order_data: dict) -> int:
    """
    Load a single CVS order into the database.

    Args:
        db: Database connection
        order_data: Parsed order data from YAML

    Returns:
        Number of items successfully loaded
    """
    try:
        conn = db.get_connection()
        cur = conn.cursor()

        # Extract order-level information
        order_number = order_data.get("number")
        order_type = (
            order_data.get("type", [None])[0] if order_data.get("type") else None
        )
        purchase_date = parse_cvs_date(order_data.get("date"))
        purchase_time = parse_cvs_time(order_data.get("date"))

        # Extract order totals
        order_info = order_data.get("order", {})
        cost_info = order_info.get("cost", {})

        subtotal = parse_decimal(cost_info.get("subTotal"))
        tax_total = parse_decimal(cost_info.get("tax"))
        savings_total = parse_decimal(cost_info.get("savings"))
        shipping_total = parse_decimal(cost_info.get("shipping"))
        grand_total = parse_decimal(cost_info.get("total"))

        # Extract store info
        store_id = order_info.get("pickupStoreId")
        ec_card = order_info.get("ecCard")
        transaction_number = order_info.get("txnNo")
        register_number = order_info.get("regNo")

        # Extract payment info (use first payment method)
        payment_methods = order_info.get("paymentMethod", [])
        payment_type = None
        payment_last_four = None
        payment_amount_charged = None
        payment_amount_returned = None

        if payment_methods:
            payment = payment_methods[0]
            payment_type = payment.get("type")
            payment_last_four = payment.get("lastFourDigits")
            payment_amount_charged = parse_decimal(payment.get("amountCharged"))
            payment_amount_returned = parse_decimal(payment.get("amountReturned"))

        # Extract flags
        split_shipment = order_info.get("splitShipment", False)
        split_fulfillment = order_info.get("splitFulfillment", False)
        return_eligible = order_info.get("returnEligible", False)
        return_eligible_final_date = parse_cvs_date(
            order_info.get("returnEligibleFinalDate")
        )

        # Process items from inStore section
        items_loaded = 0
        in_store_orders = order_info.get("inStore", [])

        for store_order in in_store_orders:
            fs_items = store_order.get("fsItems", [])

            for item in fs_items:
                # Prepare item record
                item_record = {
                    "order_number": order_number,
                    "order_type": order_type,
                    "purchase_date": purchase_date,
                    "purchase_time": purchase_time,
                    "subtotal": subtotal,
                    "tax_total": tax_total,
                    "savings_total": savings_total,
                    "shipping_total": shipping_total,
                    "grand_total": grand_total,
                    "store_id": store_id,
                    "ec_card": ec_card,
                    "transaction_number": transaction_number,
                    "register_number": register_number,
                    "item_id": item.get("itemId"),
                    "item_name": item.get("name"),
                    "item_size": item.get("itemSize"),
                    "item_size_uom": item.get("itemSizeUOM"),
                    "item_weight": item.get("itemWeight"),
                    "item_weight_uom": item.get("itemWeightUOM"),
                    "item_quantity": parse_integer(item.get("qty", 1)),
                    "item_price_total": parse_decimal(item.get("priceTotal")),
                    "item_price_final": parse_decimal(item.get("priceFinal")),
                    "item_savings": parse_decimal(item.get("savings")),
                    "item_tax": parse_decimal(item.get("tax")),
                    "item_line_total_without_tax": parse_decimal(
                        item.get("lineTotalWithoutTax")
                    ),
                    "item_status": item.get("status"),
                    "item_image_url": item.get("image"),
                    "item_url": item.get("url"),
                    "ec_rewards_eligible": item.get("ecRewardsEligible") == "true",
                    "in_store_only_item": item.get("inStoreOnlyItem", False),
                    "payment_type": payment_type,
                    "payment_last_four": payment_last_four,
                    "payment_amount_charged": payment_amount_charged,
                    "payment_amount_returned": payment_amount_returned,
                    "split_shipment": split_shipment,
                    "split_fulfillment": split_fulfillment,
                    "return_eligible": return_eligible,
                    "return_eligible_final_date": return_eligible_final_date,
                    "raw_data": json.dumps(order_data),
                }

                # Insert into database
                columns = list(item_record.keys())
                placeholders = ", ".join(["%s"] * len(columns))
                values = [item_record[col] for col in columns]

                insert_sql = f"""
                    INSERT INTO cvs_purchases ({", ".join(columns)})
                    VALUES ({placeholders})
                """

                cur.execute(insert_sql, values)
                items_loaded += 1

        conn.commit()
        return items_loaded

    except Exception as e:
        print(f"[ERROR] Failed to load CVS order to database: {e}")
        if "conn" in locals():
            conn.rollback()
        return 0
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()


def process_cvs_yaml_files(yaml_dir: str = "data/cvs") -> None:
    """
    Process all CVS YAML files and load them into the database.

    Args:
        yaml_dir: Directory containing CVS YAML files
    """
    print("🏪 CVS DATA LOADER")
    print("=" * 50)

    if not os.path.exists(yaml_dir):
        print(f"❌ Directory {yaml_dir} does not exist")
        return

    # Initialize database
    db = GroceryDB()

    # Create tables
    print("🔧 Creating database tables...")
    db.ensure_grocery_tables()

    # Get all YAML files
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(".yaml")]

    if not yaml_files:
        print(f"❌ No YAML files found in {yaml_dir}")
        return

    print(f"📁 Found {len(yaml_files)} YAML files to process")

    total_items = 0
    processed_files = 0
    error_count = 0

    for filename in sorted(yaml_files):
        filepath = os.path.join(yaml_dir, filename)
        print(f"\n📄 Processing: {filename}")

        try:
            # Load YAML file
            with open(filepath, encoding="utf-8") as f:
                order_data = yaml.safe_load(f)

            # Load to database
            items_count = load_cvs_order_to_database(db, order_data)

            if items_count > 0:
                print(f"   ✅ Loaded {items_count} items to database")
                total_items += items_count
                processed_files += 1
            else:
                print(f"   ⚠️  No items loaded from {filename}")
                error_count += 1

        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            error_count += 1

    print("\n🎉 PROCESSING COMPLETED!")
    print("=" * 50)
    print("📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {processed_files}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📦 Total items loaded: {total_items}")
    print("   🗃️  Data loaded to: cvs_purchases table")


if __name__ == "__main__":
    process_cvs_yaml_files()
