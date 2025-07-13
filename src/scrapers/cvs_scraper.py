#!/usr/bin/env python3
"""
CVS Order Scraper

Scrapes CVS order data using their retail API endpoints.
Requires manual token extraction from browser session.
"""

import os
from datetime import datetime

import requests
import yaml


class CVSScraper:
    def __init__(self):
        self.base_url = "https://www.cvs.com/api/retail/orders/v1"
        self.session = requests.Session()

        # Required headers
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,es-419;q=0.8,es;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.cvs.com",
            "referer": "https://www.cvs.com/account/order/order-history",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "x-api-key": "MUST_CHANGE_API_HERE",
            "x-new-encrypt": "Y",
            "adrum": "isAjax:true",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
        }

        # These need to be extracted from browser session
        self.access_token = None
        self.cookies = None
        self.ec_card_no = None
        self.member_ids = []

    def set_authentication(
        self, access_token: str, cookies: str, ec_card_no: str, member_ids: list[str]
    ):
        """
        Set authentication tokens extracted from browser session.

        Args:
            access_token: JWT token from access_token cookie
            cookies: Full cookie string from browser
            ec_card_no: ExtraCare card number
            member_ids: List of encrypted member IDs
        """
        self.access_token = access_token
        self.cookies = cookies
        self.ec_card_no = ec_card_no
        self.member_ids = member_ids

        # Set cookies in session
        self.session.headers.update(self.headers)
        self.session.headers["cookie"] = cookies

    def get_orders_list(self, months: int = 12, page: int = 1) -> dict | None:
        """
        Get list of orders from CVS API.

        Args:
            months: Number of months to retrieve (default: 12)
            page: Page number for pagination (default: 1)

        Returns:
            API response with orders list or None if failed
        """
        if not self.access_token or not self.ec_card_no:
            print("❌ Authentication not set. Call set_authentication() first.")
            return None

        url = f"{self.base_url}/list"

        payload = {
            "orders": {
                "ecCardNo": self.ec_card_no,
                "memberId": self.member_ids,
                "numberOfMonths": months,
                "category": [],
                "status": [],
                "type": [],
            },
            "page": {
                "number": page,
                "totalResults": 50,  # Adjust as needed
            },
        }

        try:
            print(f"🔍 Fetching orders list (page {page}, {months} months)...")
            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data.get('orders', []))} orders")
                return data
            print(f"❌ Failed to get orders: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"❌ Error fetching orders: {e}")
            return None

    def get_order_details(self, order_number: str, order_type: str = "STORE") -> dict | None:
        """
        Get detailed information for a specific order.

        Args:
            order_number: Order number (e.g., "7019-13-6385-20250629")
            order_type: Order type (default: "STORE")

        Returns:
            API response with order details or None if failed
        """
        if not self.access_token or not self.ec_card_no:
            print("❌ Authentication not set. Call set_authentication() first.")
            return None

        url = f"{self.base_url}/details"

        payload = {
            "orderNumber": order_number,
            "orderType": order_type,
            "ecCardNo": self.ec_card_no,
            "memberId": self.member_ids,
        }

        try:
            print(f"🔍 Fetching details for order {order_number}...")
            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved details for order {order_number}")
                return data
            print(f"❌ Failed to get order details: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        except Exception as e:
            print(f"❌ Error fetching order details: {e}")
            return None

    def save_order_yaml(self, order_data: dict, output_dir: str = "data/cvs") -> str | None:
        """
        Save order data as YAML file.

        Args:
            order_data: Order data dictionary
            output_dir: Output directory for YAML files

        Returns:
            Path to saved file or None if failed
        """
        try:
            os.makedirs(output_dir, exist_ok=True)

            # Extract date from order data
            order_date = order_data.get("date", "")
            if order_date:
                # Parse ISO date format: "2025-06-29T15:05:00Z"
                dt = datetime.fromisoformat(order_date.replace("Z", "+00:00"))
                filename = f"{dt.strftime('%Y-%m-%dT%H-%M-%S')}.yaml"
            else:
                # Fallback to current timestamp
                filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.yaml"

            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                yaml.dump(order_data, f, default_flow_style=False, sort_keys=False)

            print(f"💾 Saved: {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error saving YAML: {e}")
            return None

    def scrape_all_orders(self, months: int = 12, save_details: bool = True) -> list[dict]:
        """
        Scrape all orders and optionally their details.

        Args:
            months: Number of months to retrieve
            save_details: Whether to fetch and save detailed order information

        Returns:
            List of all order data
        """
        all_orders = []
        page = 1

        while True:
            # Get orders list
            orders_response = self.get_orders_list(months=months, page=page)
            if not orders_response:
                break

            orders = orders_response.get("orders", [])
            if not orders:
                break

            for order in orders:
                order_number = order.get("number")
                order_type = order.get("type", ["STORE"])[0] if order.get("type") else "STORE"

                if save_details and order_number:
                    # Get detailed order information
                    details = self.get_order_details(order_number, order_type)
                    if details:
                        # Merge list data with details
                        order.update(details)

                # Save order as YAML
                self.save_order_yaml(order)
                all_orders.append(order)

            # Check if this is the last page
            page_info = orders_response.get("page", {})
            if page_info.get("isLastPage", True):
                break

            page += 1

        return all_orders


def main():
    """
    Main function with example usage.

    IMPORTANT: You need to manually extract these values from your browser:
    1. Log into CVS.com
    2. Go to Order History page
    3. Open Developer Tools (F12)
    4. Look at Network tab for API calls
    5. Extract the required values from the request headers/payload
    """

    print("🏪 CVS ORDER SCRAPER")
    print("=" * 50)

    # Initialize scraper
    scraper = CVSScraper()

    # MANUAL SETUP REQUIRED - Extract these from browser session
    print("⚠️  MANUAL SETUP REQUIRED:")
    print("1. Log into CVS.com")
    print("2. Go to Order History page")
    print("3. Open Developer Tools (F12)")
    print("4. Look at Network tab for API calls to /api/retail/orders/v1/list")
    print("5. Extract the following values and update this script:")
    print()

    # Try the OAuth2 token you discovered
    access_token = "MUST_CHANGE_TOKEN_HERE"  # noqa: S105  # From OAuth2 API response
    cookies = "MUST_CHANGE_cookies_HERE"  # Full cookie string from request
    ec_card_no = "539742276"  # ExtraCare card number
    member_ids = [
        "yfCOSP9KdssdlnVcSIpBGG5nq+i9alDZio96vRH/UGM=",
        "xLDfMCXifJImN3CREh4Cmlwu09sxSB3Ereu3lm6WoM8=",
    ]  # Encrypted member IDs

    if access_token == "YOUR_access_token_HERE":  # noqa: S105
        print("❌ Please update the authentication values in the script!")
        print("   See the comments above for instructions.")
        return

    # Set authentication
    scraper.set_authentication(access_token, cookies, ec_card_no, member_ids)

    # Scrape orders
    print("\n🚀 Starting CVS order scraping...")
    orders = scraper.scrape_all_orders(months=12, save_details=True)

    print("\n🎉 SCRAPING COMPLETED!")
    print(f"📊 Total orders retrieved: {len(orders)}")
    print("📁 YAML files saved to: ./data/cvs")


if __name__ == "__main__":
    main()
