#!/usr/bin/env python3
"""
Publix Data Processor

Processes raw Publix data from JSON files into YAML format and loads into database.
Handles both purchase list data and detailed receipt data.

Usage:
1. Ensure you have raw data in raw/publix/
2. Run: python publix_data_processor.py
"""

import json
import os
import re
from datetime import date, datetime, time

import yaml

from scripts.grocery_db import GroceryDB


class PublixDataProcessor:
    """Processor for Publix raw data to YAML and database."""

    def __init__(self):
        self.raw_dir = "raw/publix"
        self.yaml_dir = "data/publix"

        # Create directories if they don't exist
        os.makedirs(self.yaml_dir, exist_ok=True)

    def parse_publix_date(self, date_str: str) -> date | None:
        """Parse Publix date format like '2025-06-25T21:54:04'."""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.date()
        except Exception as e:
            print(f"[WARNING] Could not parse date {date_str}: {e}")
        return None

    def parse_publix_time(self, date_str: str) -> time | None:
        """Parse Publix time format like '2025-06-25T21:54:04'."""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.time()
        except Exception as e:
            print(f"[WARNING] Could not parse time {date_str}: {e}")
        return None

    def parse_decimal(self, value) -> float | None:
        """Safely parse decimal values."""
        try:
            if value is None or value == "":
                return None
            return float(str(value))
        except (ValueError, TypeError):
            return None

    def parse_integer(self, value) -> int | None:
        """Safely parse integer values."""
        try:
            if value is None or value == "":
                return None
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def parse_receipt_text(self, receipt_text: str) -> dict:
        """Parse receipt text to extract structured data."""
        receipt_info = {
            "store_info": {},
            "items": [],
            "payment_info": {},
            "totals": {},
            "savings": {},
            "fsa_info": {},
            "staff_info": {},
        }

        if not receipt_text:
            return receipt_info

        lines = receipt_text.split("&#10;")

        # Parse store info (first few lines)
        if len(lines) > 0:
            receipt_info["store_info"]["name"] = lines[0].strip()
        if len(lines) > 1:
            receipt_info["store_info"]["address"] = lines[1].strip()
        if len(lines) > 2:
            receipt_info["store_info"]["city_state_zip"] = lines[2].strip()

        # Look for store manager and phone
        for line in lines[:10]:
            if "Store Manager:" in line:
                receipt_info["store_info"]["manager"] = line.replace(
                    "Store Manager:", ""
                ).strip()
            elif re.match(r".*\d{3}-\d{3}-\d{4}.*", line):
                receipt_info["store_info"]["phone"] = re.search(
                    r"\d{3}-\d{3}-\d{4}", line
                ).group()

        # Parse items and totals
        for line in lines:
            line = line.strip()

            # Skip empty lines and headers
            if (
                not line
                or line.startswith("*")
                or line.startswith("=")
                or line.startswith("-")
            ):
                continue

            # Look for item lines (have price at end)
            if re.match(r".*\d+\.\d{2}\s*[THFP]?\s*$", line):
                # Extract item info
                parts = line.rsplit(
                    None, 2
                )  # Split from right to get price and tax flag
                if len(parts) >= 2:
                    item_name = " ".join(parts[:-2]) if len(parts) > 2 else parts[0]
                    price_str = parts[-2] if len(parts) > 2 else parts[-1]
                    tax_flag = (
                        parts[-1]
                        if len(parts) > 2 and not re.match(r"\d+\.\d{2}", parts[-1])
                        else ""
                    )

                    # Handle negative prices (voided items)
                    is_voided = price_str.startswith("-")
                    price = self.parse_decimal(price_str.replace("-", ""))

                    receipt_info["items"].append(
                        {
                            "name": item_name.strip(),
                            "price": price,
                            "tax_flag": tax_flag,
                            "is_voided": is_voided,
                            "line_text": line,
                        }
                    )

            # Look for totals
            elif "Order Total" in line:
                total_match = re.search(r"\d+\.\d{2}", line)
                if total_match:
                    receipt_info["totals"]["order_total"] = self.parse_decimal(
                        total_match.group()
                    )
            elif "Sales Tax" in line:
                tax_match = re.search(r"\d+\.\d{2}", line)
                if tax_match:
                    receipt_info["totals"]["sales_tax"] = self.parse_decimal(
                        tax_match.group()
                    )
            elif "Grand Total" in line:
                grand_match = re.search(r"\d+\.\d{2}", line)
                if grand_match:
                    receipt_info["totals"]["grand_total"] = self.parse_decimal(
                        grand_match.group()
                    )

            # Look for savings
            elif "Digital Coupon" in line:
                savings_match = re.search(r"\d+\.\d{2}", line)
                if savings_match:
                    receipt_info["savings"]["digital_coupon"] = self.parse_decimal(
                        savings_match.group()
                    )
            elif "Your Savings at Publix" in line:
                try:
                    next_line_idx = lines.index(line) + 1
                    if next_line_idx < len(lines):
                        savings_match = re.search(r"\d+\.\d{2}", lines[next_line_idx])
                        if savings_match:
                            receipt_info["savings"]["total_savings"] = (
                                self.parse_decimal(savings_match.group())
                            )
                except (ValueError, IndexError):
                    pass

            # Look for payment info
            elif "PRESTO!" in line or "CREDIT CARD" in line:
                # Payment section - extract details from surrounding lines
                try:
                    line_idx = lines.index(line)
                except ValueError:
                    continue  # Skip if line not found
                for i in range(max(0, line_idx - 5), min(len(lines), line_idx + 10)):
                    payment_line = lines[i].strip()
                    if "Amount:" in payment_line:
                        amount_match = re.search(r"\$(\d+\.\d{2})", payment_line)
                        if amount_match:
                            receipt_info["payment_info"]["amount"] = self.parse_decimal(
                                amount_match.group(1)
                            )
                    elif "Auth #:" in payment_line:
                        receipt_info["payment_info"]["auth_number"] = (
                            payment_line.split("Auth #:")[-1].strip()
                        )
                    elif "Acct #:" in payment_line:
                        receipt_info["payment_info"]["account_number"] = (
                            payment_line.split("Acct #:")[-1].strip()
                        )

            # Look for FSA info
            elif "FSA Total:" in line:
                fsa_match = re.search(r"\$(\d+\.\d{2})", line)
                if fsa_match:
                    receipt_info["fsa_info"]["total"] = self.parse_decimal(
                        fsa_match.group(1)
                    )
            elif "Prescription (P):" in line:
                fsa_match = re.search(r"(\d+\.\d{2})", line)
                if fsa_match:
                    receipt_info["fsa_info"]["prescription"] = self.parse_decimal(
                        fsa_match.group(1)
                    )
            elif "Non-Prescription (H):" in line:
                fsa_match = re.search(r"(\d+\.\d{2})", line)
                if fsa_match:
                    receipt_info["fsa_info"]["non_prescription"] = self.parse_decimal(
                        fsa_match.group(1)
                    )

            # Look for staff info
            elif "Your cashier was" in line:
                receipt_info["staff_info"]["cashier"] = line.replace(
                    "Your cashier was", ""
                ).strip()
            elif "Supervisor #" in line:
                receipt_info["staff_info"]["supervisor"] = line.replace(
                    "Supervisor #", ""
                ).strip()

        return receipt_info

    def process_detail_file(self, filepath: str) -> dict | None:
        """Process a single detail JSON file into structured data."""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            detail = data.get("detail", {})
            original_purchase = data.get("original_purchase", {})

            # Parse receipt text for detailed item info
            receipt_text = detail.get("ReceiptText", "")
            parsed_receipt = self.parse_receipt_text(receipt_text)

            # Extract basic info
            purchase_date = self.parse_publix_date(
                original_purchase.get("PurchaseDate", "")
            )
            purchase_time = self.parse_publix_time(
                original_purchase.get("PurchaseDate", "")
            )

            # Build structured purchase data
            purchase_data = {
                "transaction_number": detail.get("TransactionNumber"),
                "receipt_id": original_purchase.get("Id"),
                "purchase_date": purchase_date.isoformat() if purchase_date else None,
                "purchase_time": purchase_time.isoformat() if purchase_time else None,
                "store_name": original_purchase.get("StoreName"),
                "store_info": parsed_receipt["store_info"],
                "order_total": detail.get("OrderTotal"),
                "tax_amount": detail.get("TaxAmount"),
                "grand_total": detail.get("GrandTotal"),
                "vendor_coupon_amount": detail.get("VendorCouponAmount"),
                "store_coupon_amount": detail.get("StoreCouponAmount"),
                "savings": parsed_receipt["savings"],
                "fsa_info": parsed_receipt["fsa_info"],
                "payment_info": parsed_receipt["payment_info"],
                "staff_info": parsed_receipt["staff_info"],
                "products": detail.get("Products", []),
                "receipt_items": parsed_receipt["items"],
                "receipt_text": receipt_text,
                "barcode_src": detail.get("BarcodeSrc"),
                "raw_data": data,
            }

            return purchase_data

        except Exception as e:
            print(f"[ERROR] Failed to process detail file {filepath}: {e}")
            return None

    def save_yaml_file(self, purchase_data: dict, filename: str) -> bool:
        """Save purchase data as YAML file."""
        try:
            filepath = os.path.join(self.yaml_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(
                    purchase_data, f, default_flow_style=False, allow_unicode=True
                )

            return True

        except Exception as e:
            print(f"[ERROR] Failed to save YAML file {filename}: {e}")
            return False

    def process_raw_to_yaml(self) -> int:
        """Process all raw JSON files to YAML format."""
        print("📁 PROCESSING RAW DATA TO YAML")
        print("=" * 50)

        if not os.path.exists(self.raw_dir):
            print(f"❌ Raw directory {self.raw_dir} does not exist")
            return 0

        # Get all detail JSON files
        detail_files = [
            f
            for f in os.listdir(self.raw_dir)
            if f.startswith("detail-") and f.endswith(".json")
        ]

        if not detail_files:
            print(f"❌ No detail files found in {self.raw_dir}")
            return 0

        print(f"📄 Found {len(detail_files)} detail files to process")

        processed_count = 0

        for filename in sorted(detail_files):
            filepath = os.path.join(self.raw_dir, filename)
            print(f"\n📄 Processing: {filename}")

            # Process the detail file
            purchase_data = self.process_detail_file(filepath)

            if purchase_data:
                # Create YAML filename based on purchase date/time
                purchase_date = purchase_data.get("purchase_date", "unknown-date")
                purchase_time = purchase_data.get("purchase_time", "00:00:00")

                if purchase_date != "unknown-date" and purchase_time != "00:00:00":
                    # Convert to filename format: YYYY-MM-DDTHH-MM-SS.yaml
                    date_part = purchase_date  # Already in YYYY-MM-DD format
                    time_part = purchase_time.replace(
                        ":", "-"
                    )  # Convert HH:MM:SS to HH-MM-SS
                    yaml_filename = f"{date_part}T{time_part}.yaml"
                else:
                    # Fallback to original filename
                    yaml_filename = filename.replace(".json", ".yaml")

                if self.save_yaml_file(purchase_data, yaml_filename):
                    print(f"   ✅ Saved: {yaml_filename}")
                    processed_count += 1
                else:
                    print("   ❌ Failed to save YAML")
            else:
                print("   ❌ Failed to process file")

        print("\n🎉 YAML PROCESSING COMPLETED!")
        print(f"   ✅ Successfully processed: {processed_count}")
        print(f"   📁 YAML files saved to: {self.yaml_dir}")

        return processed_count

    def load_yaml_to_database(self) -> int:
        """Load all YAML files into the database."""
        print("\n🗃️  LOADING YAML DATA TO DATABASE")
        print("=" * 50)

        # Initialize database
        db = GroceryDB()

        # Create tables
        print("🔧 Creating database tables...")
        db.ensure_grocery_tables()

        # Get all YAML files
        if not os.path.exists(self.yaml_dir):
            print(f"❌ YAML directory {self.yaml_dir} does not exist")
            return 0

        yaml_files = [f for f in os.listdir(self.yaml_dir) if f.endswith(".yaml")]

        if not yaml_files:
            print(f"❌ No YAML files found in {self.yaml_dir}")
            return 0

        print(f"📁 Found {len(yaml_files)} YAML files to load")

        total_items = 0
        processed_files = 0
        error_count = 0

        for filename in sorted(yaml_files):
            filepath = os.path.join(self.yaml_dir, filename)
            print(f"\n📄 Processing: {filename}")

            try:
                # Load YAML file
                with open(filepath, encoding="utf-8") as f:
                    purchase_data = yaml.safe_load(f)

                # Load to database
                items_count = self.load_purchase_to_database(db, purchase_data)

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

        print("\n🎉 DATABASE LOADING COMPLETED!")
        print("=" * 50)
        print("📊 SUMMARY:")
        print(f"   ✅ Successfully processed: {processed_files}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📦 Total items loaded: {total_items}")
        print("   🗃️  Data loaded to: publix_purchases table")

        return total_items

    def load_purchase_to_database(self, db: GroceryDB, purchase_data: dict) -> int:
        """Load a single purchase into the database."""
        try:
            conn = db.get_connection()
            cur = conn.cursor()

            # Extract purchase-level information
            transaction_number = purchase_data.get("transaction_number")
            receipt_id = purchase_data.get("receipt_id")
            purchase_date = (
                self.parse_publix_date(purchase_data.get("purchase_date"))
                if purchase_data.get("purchase_date")
                else None
            )
            purchase_time = None
            if purchase_data.get("purchase_time"):
                try:
                    purchase_time = datetime.strptime(
                        purchase_data.get("purchase_time"), "%H:%M:%S"
                    ).time()
                except:
                    pass

            # Store info
            store_name = purchase_data.get("store_name")
            store_info = purchase_data.get("store_info", {})
            store_address = store_info.get("address")
            store_manager = store_info.get("manager")
            store_phone = store_info.get("phone")

            # Totals
            order_total = self.parse_decimal(purchase_data.get("order_total"))
            tax_amount = self.parse_decimal(purchase_data.get("tax_amount"))
            grand_total = self.parse_decimal(purchase_data.get("grand_total"))
            vendor_coupon_amount = self.parse_decimal(
                purchase_data.get("vendor_coupon_amount")
            )
            store_coupon_amount = self.parse_decimal(
                purchase_data.get("store_coupon_amount")
            )

            # Savings info
            savings = purchase_data.get("savings", {})
            digital_coupon_savings = self.parse_decimal(savings.get("digital_coupon"))
            total_savings = self.parse_decimal(savings.get("total_savings"))

            # Payment info
            payment_info = purchase_data.get("payment_info", {})
            payment_amount = self.parse_decimal(payment_info.get("amount"))
            payment_auth_number = payment_info.get("auth_number")
            payment_account_number = payment_info.get("account_number")

            # FSA info
            fsa_info = purchase_data.get("fsa_info", {})
            fsa_total = self.parse_decimal(fsa_info.get("total"))
            fsa_prescription_amount = self.parse_decimal(fsa_info.get("prescription"))
            fsa_non_prescription_amount = self.parse_decimal(
                fsa_info.get("non_prescription")
            )

            # Staff info
            staff_info = purchase_data.get("staff_info", {})
            cashier_name = staff_info.get("cashier")
            supervisor_number = staff_info.get("supervisor")

            items_loaded = 0

            # Process products from API data
            products = purchase_data.get("products", [])
            for product in products:
                item_record = self.build_item_record(
                    transaction_number,
                    receipt_id,
                    purchase_date,
                    purchase_time,
                    store_name,
                    store_address,
                    store_manager,
                    store_phone,
                    order_total,
                    tax_amount,
                    grand_total,
                    vendor_coupon_amount,
                    store_coupon_amount,
                    digital_coupon_savings,
                    total_savings,
                    payment_amount,
                    payment_auth_number,
                    payment_account_number,
                    fsa_total,
                    fsa_prescription_amount,
                    fsa_non_prescription_amount,
                    cashier_name,
                    supervisor_number,
                    product,
                    None,
                    purchase_data,
                )

                if self.insert_item_record(cur, item_record):
                    items_loaded += 1

            # Process receipt items (parsed from receipt text)
            receipt_items = purchase_data.get("receipt_items", [])
            for receipt_item in receipt_items:
                item_record = self.build_item_record(
                    transaction_number,
                    receipt_id,
                    purchase_date,
                    purchase_time,
                    store_name,
                    store_address,
                    store_manager,
                    store_phone,
                    order_total,
                    tax_amount,
                    grand_total,
                    vendor_coupon_amount,
                    store_coupon_amount,
                    digital_coupon_savings,
                    total_savings,
                    payment_amount,
                    payment_auth_number,
                    payment_account_number,
                    fsa_total,
                    fsa_prescription_amount,
                    fsa_non_prescription_amount,
                    cashier_name,
                    supervisor_number,
                    None,
                    receipt_item,
                    purchase_data,
                )

                if self.insert_item_record(cur, item_record):
                    items_loaded += 1

            conn.commit()
            return items_loaded

        except Exception as e:
            print(f"[ERROR] Failed to load purchase to database: {e}")
            if "conn" in locals():
                conn.rollback()
            return 0
        finally:
            if "cur" in locals():
                cur.close()
            if "conn" in locals():
                conn.close()

    def build_item_record(
        self,
        transaction_number,
        receipt_id,
        purchase_date,
        purchase_time,
        store_name,
        store_address,
        store_manager,
        store_phone,
        order_total,
        tax_amount,
        grand_total,
        vendor_coupon_amount,
        store_coupon_amount,
        digital_coupon_savings,
        total_savings,
        payment_amount,
        payment_auth_number,
        payment_account_number,
        fsa_total,
        fsa_prescription_amount,
        fsa_non_prescription_amount,
        cashier_name,
        supervisor_number,
        product,
        receipt_item,
        raw_data,
    ):
        """Build item record for database insertion."""

        # Use product data if available, otherwise use receipt item data
        if product:
            item_id = product.get("ItemId")
            item_name = product.get("ItemName", "")
            item_description = product.get("ItemDescription")
            item_quantity = self.parse_integer(product.get("ItemQuantity", 1))
            item_size_description = product.get("SizeDescription")
            item_image_url = product.get("ItemImageUrl")
            item_detail_url = product.get("ItemDetailUrl")
            upc = product.get("UPC")
            base_product_id = product.get("BaseProductId")
            retail_sub_section_number = product.get("RetailSubSectionNumber")
            activation_status = product.get("ActivationStatus")
            item_price = None  # Not available in product data
            receipt_line_text = None
            is_voided_item = False
            item_tax_flag = None
        else:
            # Use receipt item data
            item_id = None
            item_name = receipt_item.get("name", "") if receipt_item else ""
            item_description = None
            item_quantity = 1  # Receipt items don't have quantity info
            item_price = (
                self.parse_decimal(receipt_item.get("price")) if receipt_item else None
            )
            item_size_description = None
            item_image_url = None
            item_detail_url = None
            upc = None
            base_product_id = None
            retail_sub_section_number = None
            activation_status = None
            receipt_line_text = receipt_item.get("line_text") if receipt_item else None
            is_voided_item = (
                receipt_item.get("is_voided", False) if receipt_item else False
            )
            item_tax_flag = receipt_item.get("tax_flag") if receipt_item else None

        return {
            "transaction_number": transaction_number,
            "receipt_id": receipt_id,
            "purchase_date": purchase_date,
            "purchase_time": purchase_time,
            "store_name": store_name,
            "store_address": store_address,
            "store_manager": store_manager,
            "store_phone": store_phone,
            "order_total": order_total,
            "sales_tax": tax_amount,
            "grand_total": grand_total,
            "vendor_coupon_amount": vendor_coupon_amount,
            "store_coupon_amount": store_coupon_amount,
            "digital_coupon_savings": digital_coupon_savings,
            "total_savings": total_savings,
            "item_id": item_id,
            "item_name": item_name,
            "item_description": item_description,
            "item_quantity": item_quantity,
            "item_price": item_price,
            "item_size_description": item_size_description,
            "item_image_url": item_image_url,
            "item_detail_url": item_detail_url,
            "upc": upc,
            "base_product_id": base_product_id,
            "retail_sub_section_number": retail_sub_section_number,
            "activation_status": activation_status,
            "receipt_line_text": receipt_line_text,
            "is_voided_item": is_voided_item,
            "item_tax_flag": item_tax_flag,
            "payment_method": "Credit Card" if payment_amount else None,
            "payment_amount": payment_amount,
            "payment_account_number": payment_account_number,
            "payment_auth_number": payment_auth_number,
            "fsa_prescription_amount": fsa_prescription_amount,
            "fsa_non_prescription_amount": fsa_non_prescription_amount,
            "fsa_total": fsa_total,
            "cashier_name": cashier_name,
            "supervisor_number": supervisor_number,
            "raw_data": json.dumps(raw_data),
        }

    def insert_item_record(self, cur, item_record):
        """Insert item record into database."""
        try:
            columns = list(item_record.keys())
            placeholders = ", ".join(["%s"] * len(columns))
            values = [item_record[col] for col in columns]

            insert_sql = f"""
                INSERT INTO publix_purchases ({", ".join(columns)})
                VALUES ({placeholders})
            """

            cur.execute(insert_sql, values)
            return True

        except Exception as e:
            print(f"[ERROR] Failed to insert item record: {e}")
            return False


if __name__ == "__main__":
    processor = PublixDataProcessor()

    # Step 1: Process raw data to YAML
    yaml_count = processor.process_raw_to_yaml()

    if yaml_count > 0:
        print(f"\n🚀 Successfully created {yaml_count} YAML files!")

        # Step 2: Load YAML data to database
        db_count = processor.load_yaml_to_database()

        if db_count > 0:
            print("\n🎉 COMPLETE SUCCESS!")
            print(f"   📄 YAML files: {yaml_count}")
            print(f"   📦 Database items: {db_count}")
            print("   🗃️  Publix data collection system ready!")
        else:
            print("\n⚠️  YAML files created but database loading failed")
    else:
        print("\n❌ No YAML files created. Check raw data directory.")
