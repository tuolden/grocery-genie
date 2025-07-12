"""
Database operations for grocery purchase data.
Handles insertion, updates, and queries for grocery store purchases.
"""

import json
import os

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GroceryDB:
    """Database handler for grocery purchase data."""

    def __init__(self):
        # Get database configuration from environment variables
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "grocery_genie"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
        }

        # Alternative: use DATABASE_URL if provided
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self.database_url = database_url
        else:
            self.database_url = None

    def get_connection(self):
        """Get database connection."""
        try:
            if self.database_url:
                # Use DATABASE_URL if provided
                return psycopg2.connect(self.database_url)
            # Use individual config parameters
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            print("[ERROR] Check your .env file and database configuration")
            raise

    def ensure_grocery_tables(self):
        """Ensure grocery tables exist and create indexes."""
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Create grocery_stores table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS grocery_stores (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    location VARCHAR(200),
                    store_number VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create enhanced costco_purchases table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS costco_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Receipt header info
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,
                    store_location VARCHAR(200),
                    receipt_number VARCHAR(50),

                    -- Item details (one row per item)
                    item_code VARCHAR(20),
                    item_name VARCHAR(300) NOT NULL,
                    item_price DECIMAL(10,2) NOT NULL,
                    item_quantity INTEGER DEFAULT 1,
                    item_unit_price DECIMAL(10,2),
                    tax_indicator VARCHAR(10),
                    item_type VARCHAR(50),
                    item_department VARCHAR(20),
                    discount_reference VARCHAR(20),
                    discount_amount DECIMAL(10,2),

                    -- Receipt totals
                    subtotal DECIMAL(10,2),
                    tax_total DECIMAL(10,2),
                    total_amount DECIMAL(10,2),

                    -- Enhanced Costco fields
                    membership_number VARCHAR(20),
                    warehouse_number VARCHAR(10),
                    transaction_number VARCHAR(20),
                    register_number VARCHAR(10),
                    operator_number VARCHAR(10),
                    instant_savings DECIMAL(10,2),

                    -- Fuel-specific fields
                    fuel_quantity DECIMAL(10,3),
                    fuel_grade VARCHAR(50),
                    fuel_unit_price DECIMAL(10,3),

                    -- Payment and store info
                    payment_method VARCHAR(100),
                    store_address VARCHAR(300),

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create Walmart purchases table (single table design matching Costco)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS walmart_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Order header info (repeated for each item)
                    order_id VARCHAR(50) NOT NULL,
                    group_id VARCHAR(50),
                    purchase_order_id VARCHAR(50),
                    display_id VARCHAR(50),
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,

                    -- Order details (repeated for each item)
                    order_type VARCHAR(50),
                    fulfillment_type VARCHAR(50),
                    status_type VARCHAR(50),
                    delivery_message VARCHAR(200),

                    -- Item details (one row per item)
                    item_id VARCHAR(50),
                    item_name VARCHAR(300) NOT NULL,
                    item_price DECIMAL(10,2),
                    line_price DECIMAL(10,2),
                    item_quantity INTEGER DEFAULT 1,
                    item_unit_price DECIMAL(10,2),
                    item_brand VARCHAR(200),
                    item_category VARCHAR(100),
                    item_subcategory VARCHAR(100),
                    item_sku VARCHAR(50),
                    item_upc VARCHAR(50),
                    item_image_url VARCHAR(500),
                    sales_unit_type VARCHAR(50),

                    -- Store info (repeated for each item)
                    store_id VARCHAR(20),
                    store_name VARCHAR(200),
                    store_address VARCHAR(300),
                    store_city VARCHAR(100),
                    store_state VARCHAR(10),
                    store_zip VARCHAR(20),

                    -- Order totals (repeated for each item)
                    subtotal DECIMAL(10,2),
                    tax_total DECIMAL(10,2),
                    shipping_total DECIMAL(10,2),
                    grand_total DECIMAL(10,2),

                    -- Payment info (repeated for each item)
                    payment_method VARCHAR(100),

                    -- Fulfillment details (repeated for each item)
                    tracking_number VARCHAR(100),
                    carrier VARCHAR(50),
                    delivery_date DATE,
                    pickup_date DATE,

                    -- Flags (repeated for each item)
                    is_pet_rx BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_shipped_by_walmart BOOLEAN DEFAULT FALSE,

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS walmart_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Order header info
                    order_id VARCHAR(50) NOT NULL,
                    group_id VARCHAR(50),
                    purchase_order_id VARCHAR(50),
                    display_id VARCHAR(50),
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,

                    -- Order details
                    order_type VARCHAR(50),
                    fulfillment_type VARCHAR(50),
                    status_type VARCHAR(50),
                    delivery_message VARCHAR(200),

                    -- Item details
                    item_id VARCHAR(50),
                    item_name VARCHAR(300) NOT NULL,
                    item_price DECIMAL(10,2),
                    item_quantity INTEGER DEFAULT 1,
                    item_unit_price DECIMAL(10,2),
                    item_brand VARCHAR(200),
                    item_category VARCHAR(100),
                    item_subcategory VARCHAR(100),
                    item_sku VARCHAR(50),
                    item_upc VARCHAR(50),
                    item_image_url VARCHAR(500),

                    -- Store info
                    store_id VARCHAR(20),
                    store_name VARCHAR(200),
                    store_address VARCHAR(300),
                    store_city VARCHAR(100),
                    store_state VARCHAR(10),
                    store_zip VARCHAR(20),

                    -- Pricing and totals
                    subtotal DECIMAL(10,2),
                    tax_total DECIMAL(10,2),
                    shipping_total DECIMAL(10,2),
                    total_amount DECIMAL(10,2),

                    -- Payment info
                    payment_method VARCHAR(100),

                    -- Fulfillment details
                    tracking_number VARCHAR(100),
                    carrier VARCHAR(50),
                    delivery_date DATE,
                    pickup_date DATE,

                    -- Flags
                    is_pet_rx BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_shipped_by_walmart BOOLEAN DEFAULT FALSE,

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create CVS purchases table (single table design matching Costco/Walmart)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cvs_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Order header info (repeated for each item)
                    order_number VARCHAR(50) NOT NULL,
                    order_type VARCHAR(50),
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,

                    -- Order totals
                    subtotal DECIMAL(10,2),
                    tax_total DECIMAL(10,2),
                    savings_total DECIMAL(10,2),
                    shipping_total DECIMAL(10,2),
                    grand_total DECIMAL(10,2),

                    -- Store info
                    store_id VARCHAR(20),
                    ec_card VARCHAR(20),
                    transaction_number VARCHAR(20),
                    register_number VARCHAR(20),

                    -- Item details
                    item_id VARCHAR(50),
                    item_name VARCHAR(300) NOT NULL,
                    item_size VARCHAR(50),
                    item_size_uom VARCHAR(20),
                    item_weight VARCHAR(50),
                    item_weight_uom VARCHAR(20),
                    item_quantity INTEGER DEFAULT 1,
                    item_price_total DECIMAL(10,2),
                    item_price_final DECIMAL(10,2),
                    item_savings DECIMAL(10,2),
                    item_tax DECIMAL(10,2),
                    item_line_total_without_tax DECIMAL(10,2),
                    item_status VARCHAR(50),
                    item_image_url VARCHAR(500),
                    item_url VARCHAR(500),
                    ec_rewards_eligible BOOLEAN DEFAULT FALSE,
                    in_store_only_item BOOLEAN DEFAULT FALSE,

                    -- Payment info
                    payment_type VARCHAR(50),
                    payment_last_four VARCHAR(10),
                    payment_amount_charged DECIMAL(10,2),
                    payment_amount_returned DECIMAL(10,2),

                    -- Flags
                    split_shipment BOOLEAN DEFAULT FALSE,
                    split_fulfillment BOOLEAN DEFAULT FALSE,
                    return_eligible BOOLEAN DEFAULT FALSE,
                    return_eligible_final_date DATE,

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create Publix purchases table (single table design matching other retailers)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS publix_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Order header info (repeated for each item)
                    transaction_number VARCHAR(100) NOT NULL,
                    receipt_id VARCHAR(200),
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,

                    -- Store info
                    store_name VARCHAR(100),
                    store_address VARCHAR(200),
                    store_manager VARCHAR(100),
                    store_phone VARCHAR(20),

                    -- Order totals
                    order_total DECIMAL(10,2),
                    sales_tax DECIMAL(10,2),
                    grand_total DECIMAL(10,2),
                    vendor_coupon_amount DECIMAL(10,2),
                    store_coupon_amount DECIMAL(10,2),
                    digital_coupon_savings DECIMAL(10,2),
                    total_savings DECIMAL(10,2),

                    -- Item details
                    item_id VARCHAR(100),
                    item_name VARCHAR(300) NOT NULL,
                    item_description VARCHAR(500),
                    item_quantity INTEGER DEFAULT 1,
                    item_price DECIMAL(10,2),
                    item_size_description VARCHAR(100),
                    item_image_url VARCHAR(500),
                    item_detail_url VARCHAR(500),
                    upc VARCHAR(100),
                    base_product_id VARCHAR(200),
                    retail_sub_section_number VARCHAR(50),
                    activation_status VARCHAR(10),

                    -- Receipt line item info
                    receipt_line_text VARCHAR(500),
                    is_voided_item BOOLEAN DEFAULT FALSE,
                    item_tax_flag VARCHAR(10),  -- T, H, F, etc.

                    -- Payment info
                    payment_method VARCHAR(100),
                    payment_amount DECIMAL(10,2),
                    payment_account_number VARCHAR(100),
                    payment_auth_number VARCHAR(100),
                    payment_trace_number VARCHAR(100),
                    payment_reference_number VARCHAR(100),

                    -- FSA info
                    fsa_prescription_amount DECIMAL(10,2),
                    fsa_non_prescription_amount DECIMAL(10,2),
                    fsa_total DECIMAL(10,2),

                    -- Staff info
                    cashier_name VARCHAR(100),
                    supervisor_number VARCHAR(20),

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create other_purchases table (generic table for non-main retailers)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS other_purchases (
                    id SERIAL PRIMARY KEY,

                    -- Store and item identification
                    store_name VARCHAR(200) NOT NULL,
                    item_name VARCHAR(300) NOT NULL,
                    variant VARCHAR(200),

                    -- Quantity and pricing
                    quantity INTEGER DEFAULT 1,
                    quantity_unit VARCHAR(50),
                    price DECIMAL(10,2),

                    -- Purchase details
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,

                    -- Receipt source tracking
                    receipt_source VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'image', 'text'
                    original_text TEXT,

                    -- Metadata
                    raw_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),

                    -- Composite unique constraint for upsert logic
                    UNIQUE(store_name, item_name, purchase_date, variant)
                );
            """)

            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_costco_purchase_date
                ON costco_purchases(purchase_date);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_costco_store_location
                ON costco_purchases(store_location);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_costco_item_name
                ON costco_purchases(item_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_costco_receipt_number
                ON costco_purchases(receipt_number);
            """)

            # Create unique constraint to prevent duplicates
            # Drop the problematic unique constraint if it exists
            cur.execute("""
                DROP INDEX IF EXISTS idx_costco_unique_item;
            """)

            # Note: No unique constraint needed - customers can buy:
            # - Multiple quantities of same item in one receipt
            # - Same item on different dates
            # - Same item multiple times in same receipt (separate line items)

            # Create Walmart indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_walmart_purchase_date
                ON walmart_purchases(purchase_date);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_walmart_order_id
                ON walmart_purchases(order_id);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_walmart_item_name
                ON walmart_purchases(item_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_walmart_store_name
                ON walmart_purchases(store_name);
            """)

            # Create CVS indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_cvs_purchase_date
                ON cvs_purchases(purchase_date);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_cvs_order_number
                ON cvs_purchases(order_number);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_cvs_item_name
                ON cvs_purchases(item_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_cvs_store_id
                ON cvs_purchases(store_id);
            """)

            # Create Publix indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_publix_purchase_date
                ON publix_purchases(purchase_date);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_publix_transaction_number
                ON publix_purchases(transaction_number);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_publix_item_name
                ON publix_purchases(item_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_publix_store_name
                ON publix_purchases(store_name);
            """)

            # Create other_purchases indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_other_purchase_date
                ON other_purchases(purchase_date);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_other_store_name
                ON other_purchases(store_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_other_item_name
                ON other_purchases(item_name);
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_other_composite_key
                ON other_purchases(store_name, item_name, purchase_date);
            """)

            conn.commit()
            print("[✓] Grocery database tables and indexes ensured")

        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to ensure grocery tables: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    def insert_costco_purchase(self, purchase_data):
        """
        Insert a single Costco purchase record.

        Args:
            purchase_data (dict): Purchase data with keys matching table columns

        Returns:
            int: ID of inserted record, or None if failed
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Enhanced insert query with all new fields
            insert_query = """
                INSERT INTO costco_purchases (
                    purchase_date, purchase_time, store_location, receipt_number,
                    item_code, item_name, item_price, item_quantity, item_unit_price,
                    tax_indicator, item_type, item_department, discount_reference,
                    discount_amount, subtotal, tax_total, total_amount,
                    membership_number, warehouse_number, transaction_number,
                    register_number, operator_number, instant_savings,
                    fuel_quantity, fuel_grade, fuel_unit_price,
                    payment_method, store_address, raw_data
                ) VALUES (
                    %(purchase_date)s, %(purchase_time)s, %(store_location)s, %(receipt_number)s,
                    %(item_code)s, %(item_name)s, %(item_price)s, %(item_quantity)s, %(item_unit_price)s,
                    %(tax_indicator)s, %(item_type)s, %(item_department)s, %(discount_reference)s,
                    %(discount_amount)s, %(subtotal)s, %(tax_total)s, %(total_amount)s,
                    %(membership_number)s, %(warehouse_number)s, %(transaction_number)s,
                    %(register_number)s, %(operator_number)s, %(instant_savings)s,
                    %(fuel_quantity)s, %(fuel_grade)s, %(fuel_unit_price)s,
                    %(payment_method)s, %(store_address)s, %(raw_data)s
                ) RETURNING id;
            """

            # Convert raw_data to JSON string if it's a dict
            if isinstance(purchase_data.get("raw_data"), dict):
                purchase_data["raw_data"] = json.dumps(purchase_data["raw_data"])

            # Execute the query
            cur.execute(insert_query, purchase_data)
            record_id = cur.fetchone()[0]

            conn.commit()
            return record_id

        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to insert Costco purchase: {e}")
            print(f"[DEBUG] Purchase data keys: {list(purchase_data.keys())}")
            return None
        finally:
            cur.close()
            conn.close()

    def insert_costco_purchases_batch(self, purchases_list):
        """
        Insert multiple Costco purchase records in a batch.

        Args:
            purchases_list (list): List of purchase data dictionaries

        Returns:
            tuple: (success_count, error_count)
        """
        success_count = 0
        error_count = 0

        for purchase in purchases_list:
            try:
                record_id = self.insert_costco_purchase(purchase)
                if record_id:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"[ERROR] Batch insert error for purchase: {e}")
                error_count += 1

        print(
            f"[✓] Batch insert completed: {success_count} success, {error_count} errors"
        )
        return success_count, error_count

    def insert_walmart_purchase(self, purchase_data):
        """
        Insert a single Walmart purchase into the database.

        Args:
            purchase_data (dict): Purchase data with all required fields

        Returns:
            int: Record ID if successful, None if failed
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            insert_query = """
                INSERT INTO walmart_purchases (
                    order_id, group_id, purchase_order_id, display_id,
                    purchase_date, purchase_time, order_type, fulfillment_type,
                    status_type, delivery_message, item_id, item_name,
                    item_price, line_price, item_quantity, item_unit_price,
                    item_brand, item_category, item_subcategory, item_sku,
                    item_upc, item_image_url, sales_unit_type, store_id,
                    store_name, store_address, store_city, store_state,
                    store_zip, subtotal, tax_total, shipping_total,
                    grand_total, payment_method, tracking_number, carrier,
                    delivery_date, pickup_date, is_pet_rx, is_active,
                    is_shipped_by_walmart, raw_data
                ) VALUES (
                    %(order_id)s, %(group_id)s, %(purchase_order_id)s, %(display_id)s,
                    %(purchase_date)s, %(purchase_time)s, %(order_type)s, %(fulfillment_type)s,
                    %(status_type)s, %(delivery_message)s, %(item_id)s, %(item_name)s,
                    %(item_price)s, %(line_price)s, %(item_quantity)s, %(item_unit_price)s,
                    %(item_brand)s, %(item_category)s, %(item_subcategory)s, %(item_sku)s,
                    %(item_upc)s, %(item_image_url)s, %(sales_unit_type)s, %(store_id)s,
                    %(store_name)s, %(store_address)s, %(store_city)s, %(store_state)s,
                    %(store_zip)s, %(subtotal)s, %(tax_total)s, %(shipping_total)s,
                    %(grand_total)s, %(payment_method)s, %(tracking_number)s, %(carrier)s,
                    %(delivery_date)s, %(pickup_date)s, %(is_pet_rx)s, %(is_active)s,
                    %(is_shipped_by_walmart)s, %(raw_data)s
                ) RETURNING id;
            """

            # Convert raw_data to JSON string if it's a dict
            if isinstance(purchase_data.get("raw_data"), dict):
                purchase_data["raw_data"] = json.dumps(purchase_data["raw_data"])

            # Execute the query
            cur.execute(insert_query, purchase_data)
            record_id = cur.fetchone()[0]

            conn.commit()
            return record_id

        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to insert Walmart purchase: {e}")
            print(f"[DEBUG] Purchase data keys: {list(purchase_data.keys())}")
            return None
        finally:
            cur.close()
            conn.close()

    def batch_insert_walmart_purchases(self, purchases_list):
        """
        Insert multiple Walmart purchases in batch.

        Args:
            purchases_list (list): List of purchase data dictionaries

        Returns:
            tuple: (success_count, error_count)
        """
        success_count = 0
        error_count = 0

        for purchase in purchases_list:
            try:
                record_id = self.insert_walmart_purchase(purchase)
                if record_id:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"[ERROR] Batch insert error for purchase: {e}")
                error_count += 1

        print(
            f"[✓] Batch insert completed: {success_count} success, {error_count} errors"
        )
        return success_count, error_count

    def get_recent_costco_purchases(self, days_back=30):
        """
        Get recent Costco purchases within specified days.

        Args:
            days_back (int): Number of days to look back

        Returns:
            list: List of purchase records
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT * FROM costco_purchases
                WHERE purchase_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY purchase_date DESC, created_at DESC;
            """

            cur.execute(query, (days_back,))
            columns = [desc[0] for desc in cur.description]
            results = []

            for row in cur.fetchall():
                record = dict(zip(columns, row, strict=False))
                # Convert date/time objects to strings for JSON serialization
                if record.get("purchase_date"):
                    record["purchase_date"] = record["purchase_date"].isoformat()
                if record.get("purchase_time"):
                    record["purchase_time"] = str(record["purchase_time"])
                if record.get("created_at"):
                    record["created_at"] = record["created_at"].isoformat()
                if record.get("updated_at"):
                    record["updated_at"] = record["updated_at"].isoformat()
                results.append(record)

            return results

        except Exception as e:
            print(f"[ERROR] Failed to get recent purchases: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_costco_purchase_summary(self, days_back=30):
        """
        Get summary statistics for Costco purchases.

        Args:
            days_back (int): Number of days to look back

        Returns:
            dict: Summary statistics
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT
                    COUNT(*) as total_items,
                    COUNT(DISTINCT receipt_number) as total_receipts,
                    COUNT(DISTINCT purchase_date) as shopping_days,
                    SUM(item_price) as total_spent,
                    AVG(item_price) as avg_item_price,
                    MIN(purchase_date) as earliest_purchase,
                    MAX(purchase_date) as latest_purchase
                FROM costco_purchases
                WHERE purchase_date >= CURRENT_DATE - INTERVAL '%s days';
            """

            cur.execute(query, (days_back,))
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()

            if row:
                summary = dict(zip(columns, row, strict=False))
                # Convert date objects to strings
                if summary.get("earliest_purchase"):
                    summary["earliest_purchase"] = summary[
                        "earliest_purchase"
                    ].isoformat()
                if summary.get("latest_purchase"):
                    summary["latest_purchase"] = summary["latest_purchase"].isoformat()
                return summary
            return {}

        except Exception as e:
            print(f"[ERROR] Failed to get purchase summary: {e}")
            return {}
        finally:
            cur.close()
            conn.close()


def parse_costco_receipt_format(receipt_text):
    """
    Parse Costco receipt text format into structured data.

    Args:
        receipt_text (str): Raw receipt text in the format provided

    Returns:
        dict: Parsed receipt data
    """
    lines = receipt_text.strip().split("\n")

    # Initialize receipt data
    receipt_data = {
        "items": [],
        "subtotal": None,
        "tax_total": None,
        "total_amount": None,
        "purchase_date": None,
        "store_location": None,
    }

    for line in lines:
        line = line.strip()

        if line.startswith(("E\t", "E ")):
            # Regular item line: E	1751772	DOTS PRETZEL	9.99 N
            parts = line.split("\t") if "\t" in line else line.split()
            if len(parts) >= 4:
                item = {
                    "item_type": parts[0],
                    "item_code": parts[1],
                    "item_name": parts[2],
                    "item_price": float(parts[3])
                    if parts[3].replace(".", "").isdigit()
                    else 0.0,
                    "tax_indicator": parts[4] if len(parts) > 4 else "N",
                }
                receipt_data["items"].append(item)

        elif "SUBTOTAL" in line:
            # SUBTOTAL	360.59
            parts = line.split()
            if len(parts) >= 2:
                receipt_data["subtotal"] = float(parts[1])

        elif "TAX" in line and "SUBTOTAL" not in line:
            # TAX	1.41
            parts = line.split()
            if len(parts) >= 2:
                receipt_data["tax_total"] = float(parts[1])

        elif "Total" in line:
            # ****	Total	362.00
            parts = line.split()
            if len(parts) >= 2:
                receipt_data["total_amount"] = float(parts[-1])

    return receipt_data
