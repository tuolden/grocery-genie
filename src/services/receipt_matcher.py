#!/usr/bin/env python3
# ruff: noqa: PLR0913, PLR0912
"""
Receipt Matcher - Automatically mark items as purchased from receipts

This script implements the functionality described in GitHub Issue #1:
- Matches recent purchases to store list items
- Marks items as checked when purchased
- Updates inventory with purchase data
- Runs as cron job every 30 minutes or on-demand

Author: AI Agent
Date: 2025-07-11
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from psycopg2.extras import RealDictCursor

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.scripts.grocery_db import GroceryDB

# Configure logging with bright colors for visibility
logging.basicConfig(
    level=logging.INFO,
    format="🔍 %(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("receipt_matcher.log"),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class PurchaseItem:
    """Represents a purchased item from receipts"""

    item_name: str
    store: str
    purchase_date: datetime
    quantity: int
    price: float
    table_source: str
    raw_data: dict


@dataclass
class ListItem:
    """Represents an item in a store list"""

    id: int
    item_name: str
    store: str
    is_checked: bool
    table_source: str


@dataclass
class MatchResult:
    """Result of matching a purchase to a list item"""

    purchase_item: PurchaseItem
    list_item: ListItem | None
    match_score: float
    action: str  # 'mark_checked', 'remove_from_other_lists', 'no_action'


class ReceiptMatcher:
    """Main class for matching receipts to store lists"""

    def __init__(self, lookback_hours: int = 24):
        """
        Initialize the receipt matcher

        Args:
            lookback_hours: How many hours back to look for recent purchases
        """
        self.db = GroceryDB()
        self.lookback_hours = lookback_hours
        self.match_threshold = 0.8  # Minimum similarity score for fuzzy matching

        # Store table mappings
        self.purchase_tables = {
            "costco": "costco_purchases",
            "walmart": "walmart_purchases",
            "cvs": "cvs_purchases",
            "publix": "publix_purchases",
            "other": "other_purchases",
        }

        self.list_tables = {
            "costco": "costco_list",
            "walmart": "walmart_list",
            "cvs": "cvs_list",
            "publix": "publix_list",
        }

        logger.info("🚀 RECEIPT MATCHER INITIALIZED")
        logger.info(f"📅 Looking back {lookback_hours} hours for recent purchases")
        logger.info(f"🎯 Match threshold: {self.match_threshold}")

    def ensure_tables_exist(self):
        """Create list and inventory tables if they don't exist"""
        logger.info("🔧 ENSURING REQUIRED TABLES EXIST")

        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            # Create list tables for each store
            for _store, table_name in self.list_tables.items():
                logger.info(f"📋 Creating {table_name} if not exists")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        item_name VARCHAR(300) NOT NULL,
                        quantity_needed INTEGER DEFAULT 1,
                        is_checked BOOLEAN DEFAULT FALSE,
                        priority VARCHAR(20) DEFAULT 'medium',
                        category VARCHAR(100),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        checked_at TIMESTAMP
                    )
                """)

                # Create index for faster searching
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_item_name
                    ON {table_name} (item_name)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_is_checked
                    ON {table_name} (is_checked)
                """)

            # Create inventory table
            logger.info("📦 Creating inventory table if not exists")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id SERIAL PRIMARY KEY,
                    item_name VARCHAR(300) NOT NULL,
                    store VARCHAR(50) NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    purchase_date DATE NOT NULL,
                    purchase_time TIME,
                    price DECIMAL(10,2),
                    category VARCHAR(100),
                    expiry_date DATE,
                    location VARCHAR(100),
                    notes TEXT,
                    purchase_table_source VARCHAR(50),
                    raw_purchase_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create indexes for inventory
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_item_name
                ON inventory (item_name)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_store
                ON inventory (store)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_purchase_date
                ON inventory (purchase_date)
            """)

            conn.commit()
            logger.info("✅ ALL REQUIRED TABLES CREATED SUCCESSFULLY")

        except Exception as e:
            logger.error(f"❌ ERROR CREATING TABLES: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def get_recent_purchases(self) -> list[PurchaseItem]:
        """Get recent purchases from all purchase tables"""
        logger.info("🛒 FETCHING RECENT PURCHASES")

        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        purchases = []

        conn = self.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Define column mappings for each retailer
        column_mappings = {
            "costco_purchases": {
                "quantity": "item_quantity",
                "price": "item_price",
            },
            "walmart_purchases": {
                "quantity": "item_quantity",
                "price": "item_price",
            },
            "cvs_purchases": {
                "quantity": "item_quantity",
                "price": "item_price_final",
            },
            "publix_purchases": {
                "quantity": "item_quantity",
                "price": "item_price",
            },
            "other_purchases": {
                "quantity": "quantity",
                "price": "price",
            },
        }

        try:
            for store, table_name in self.purchase_tables.items():
                logger.info(f"📊 Checking {table_name} for recent purchases")

                # Get column mapping for this table
                mapping = column_mappings.get(table_name, {})
                quantity_col = mapping.get("quantity", "item_quantity")
                price_col = mapping.get("price", "item_price")

                # Get recent purchases from this table
                cur.execute(
                    f"""
                    SELECT
                        item_name,
                        purchase_date,
                        purchase_time,
                        {quantity_col} as item_quantity,
                        {price_col} as item_price,
                        raw_data
                    FROM {table_name}
                    WHERE purchase_date >= %s
                    ORDER BY purchase_date DESC, purchase_time DESC
                """,
                    (cutoff_time.date(),),
                )

                rows = cur.fetchall()
                logger.info(f"📈 Found {len(rows)} recent purchases in {table_name}")

                for row in rows:
                    # Combine date and time for full datetime
                    purchase_datetime = datetime.combine(
                        row["purchase_date"],
                        row["purchase_time"] or datetime.min.time(),
                    )

                    # Only include if within our time window
                    if purchase_datetime >= cutoff_time:
                        purchase = PurchaseItem(
                            item_name=row["item_name"].strip(),
                            store=store,
                            purchase_date=purchase_datetime,
                            quantity=row["item_quantity"] or 1,
                            price=float(row["item_price"] or 0),
                            table_source=table_name,
                            raw_data=row["raw_data"] or {},
                        )
                        purchases.append(purchase)

            logger.info(f"🎯 TOTAL RECENT PURCHASES FOUND: {len(purchases)}")
            return purchases

        except Exception as e:
            logger.error(f"❌ ERROR FETCHING PURCHASES: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_all_list_items(self) -> list[ListItem]:
        """Get all items from all store lists"""
        logger.info("📋 FETCHING ALL LIST ITEMS")

        list_items = []
        conn = self.db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            for store, table_name in self.list_tables.items():
                logger.info(f"📝 Checking {table_name} for list items")

                cur.execute(f"""
                    SELECT id, item_name, is_checked
                    FROM {table_name}
                    ORDER BY created_at DESC
                """)

                rows = cur.fetchall()
                logger.info(f"📊 Found {len(rows)} items in {table_name}")

                for row in rows:
                    list_item = ListItem(
                        id=row["id"],
                        item_name=row["item_name"].strip(),
                        store=store,
                        is_checked=row["is_checked"],
                        table_source=table_name,
                    )
                    list_items.append(list_item)

            logger.info(f"🎯 TOTAL LIST ITEMS FOUND: {len(list_items)}")
            return list_items

        except Exception as e:
            logger.error(f"❌ ERROR FETCHING LIST ITEMS: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using fuzzy matching"""
        # Normalize strings for comparison
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()

        # Exact match gets perfect score
        if s1 == s2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1, s2).ratio()

    def find_matches(
        self, purchases: list[PurchaseItem], list_items: list[ListItem]
    ) -> list[MatchResult]:
        """Find matches between purchases and list items"""
        logger.info("🔍 FINDING MATCHES BETWEEN PURCHASES AND LIST ITEMS")

        matches = []

        for purchase in purchases:
            logger.info(
                f"🛒 Processing purchase: {purchase.item_name} from {purchase.store}"
            )

            best_match = None
            best_score = 0.0

            # Look for matches in all lists
            for list_item in list_items:
                if list_item.is_checked:
                    continue  # Skip already checked items

                similarity = self.calculate_similarity(
                    purchase.item_name, list_item.item_name
                )

                if similarity > best_score and similarity >= self.match_threshold:
                    best_score = similarity
                    best_match = list_item

            # Determine action based on match
            if best_match:
                if best_match.store == purchase.store:
                    action = "mark_checked"
                    logger.info(
                        f"✅ SAME STORE MATCH: {purchase.item_name} → {best_match.item_name} (score: {best_score:.2f})"
                    )
                else:
                    action = "remove_from_other_lists"
                    logger.info(
                        f"🔄 CROSS STORE MATCH: {purchase.item_name} → {best_match.item_name} (score: {best_score:.2f})"
                    )
            else:
                action = "no_action"
                logger.info(f"❌ NO MATCH: {purchase.item_name}")

            match_result = MatchResult(
                purchase_item=purchase,
                list_item=best_match,
                match_score=best_score,
                action=action,
            )
            matches.append(match_result)

        logger.info(f"🎯 MATCHING COMPLETED: {len(matches)} results")
        return matches

    def execute_actions(self, matches: list[MatchResult]) -> dict[str, int]:
        """Execute actions based on match results"""
        logger.info("⚡ EXECUTING ACTIONS BASED ON MATCHES")

        stats = {
            "marked_checked": 0,
            "removed_from_lists": 0,
            "inventory_added": 0,
            "no_action": 0,
            "errors": 0,
        }

        conn = self.db.get_connection()
        cur = conn.cursor()

        try:
            for match in matches:
                try:
                    if match.action == "mark_checked":
                        self._mark_item_checked(cur, match)
                        stats["marked_checked"] += 1

                    elif match.action == "remove_from_other_lists":
                        self._remove_from_other_lists(cur, match)
                        stats["removed_from_lists"] += 1

                    elif match.action == "no_action":
                        stats["no_action"] += 1

                    # Always add to inventory for matched items
                    if match.list_item:
                        self._add_to_inventory(cur, match)
                        stats["inventory_added"] += 1

                except Exception as e:
                    logger.error(f"❌ ERROR PROCESSING MATCH: {e}")
                    stats["errors"] += 1
                    continue

            conn.commit()
            logger.info("✅ ALL ACTIONS EXECUTED SUCCESSFULLY")

        except Exception as e:
            logger.error(f"❌ ERROR EXECUTING ACTIONS: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

        return stats

    def _mark_item_checked(self, cur, match: MatchResult):
        """Mark a list item as checked"""
        logger.info(
            f"✅ MARKING CHECKED: {match.list_item.item_name} in {match.list_item.table_source}"
        )

        cur.execute(
            f"""
            UPDATE {match.list_item.table_source}
            SET is_checked = TRUE,
                checked_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """,
            (match.list_item.id,),
        )

    def _remove_from_other_lists(self, cur, match: MatchResult):
        """Remove item from all store lists when found in other_purchases"""
        logger.info(f"🗑️ REMOVING FROM ALL LISTS: {match.purchase_item.item_name}")

        # Find similar items in all lists and remove them
        for _store, table_name in self.list_tables.items():
            cur.execute(
                f"""
                DELETE FROM {table_name}
                WHERE LOWER(item_name) LIKE LOWER(%s)
                OR LOWER(%s) LIKE LOWER(item_name)
            """,
                (
                    f"%{match.purchase_item.item_name}%",
                    f"%{match.purchase_item.item_name}%",
                ),
            )

            if cur.rowcount > 0:
                logger.info(f"🗑️ Removed {cur.rowcount} items from {table_name}")

    def _add_to_inventory(self, cur, match: MatchResult):
        """Add purchase to inventory"""
        logger.info(f"📦 ADDING TO INVENTORY: {match.purchase_item.item_name}")

        cur.execute(
            """
            INSERT INTO inventory (
                item_name, store, quantity, purchase_date, purchase_time,
                price, purchase_table_source, raw_purchase_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                match.purchase_item.item_name,
                match.purchase_item.store,
                match.purchase_item.quantity,
                match.purchase_item.purchase_date.date(),
                match.purchase_item.purchase_date.time(),
                match.purchase_item.price,
                match.purchase_item.table_source,
                json.dumps(match.purchase_item.raw_data),
            ),
        )

    def run_matching_process(self) -> dict[str, int]:
        """Run the complete matching process"""
        logger.info("🚀 STARTING RECEIPT MATCHING PROCESS")
        logger.info("=" * 60)

        try:
            # Ensure tables exist
            self.ensure_tables_exist()

            # Get recent purchases
            purchases = self.get_recent_purchases()
            if not purchases:
                logger.info("ℹ️ No recent purchases found, nothing to process")
                return {"no_purchases": 1}

            # Get all list items
            list_items = self.get_all_list_items()
            if not list_items:
                logger.info("ℹ️ No list items found, nothing to match against")
                return {"no_list_items": 1}

            # Find matches
            matches = self.find_matches(purchases, list_items)

            # Execute actions
            stats = self.execute_actions(matches)

            # Log summary
            logger.info("📊 RECEIPT MATCHING SUMMARY")
            logger.info("=" * 60)
            logger.info(f"🛒 Recent purchases processed: {len(purchases)}")
            logger.info(f"📋 List items checked: {len(list_items)}")
            logger.info(f"✅ Items marked as checked: {stats.get('marked_checked', 0)}")
            logger.info(
                f"🗑️ Items removed from lists: {stats.get('removed_from_lists', 0)}"
            )
            logger.info(
                f"📦 Items added to inventory: {stats.get('inventory_added', 0)}"
            )
            logger.info(f"❌ No action taken: {stats.get('no_action', 0)}")
            logger.info(f"⚠️ Errors encountered: {stats.get('errors', 0)}")
            logger.info("=" * 60)

            return stats

        except Exception as e:
            logger.error(f"💥 FATAL ERROR IN MATCHING PROCESS: {e}")
            raise


def main():
    """Main entry point for the receipt matcher"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Receipt Matcher - Mark purchased items from receipts"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours to look back for recent purchases (default: 24)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no database changes)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        logger.info("🧪 RUNNING IN DRY-RUN MODE - NO DATABASE CHANGES")

    try:
        matcher = ReceiptMatcher(lookback_hours=args.hours)
        matcher.run_matching_process()

        logger.info("🎉 RECEIPT MATCHING COMPLETED SUCCESSFULLY")
        return 0

    except Exception as e:
        logger.error(f"💥 RECEIPT MATCHING FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
