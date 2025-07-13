#!/usr/bin/env python3
"""
Publix Purchase Detail Scraper

Reads transaction IDs from raw/publix/*.json files and fetches detailed receipt data
for each purchase using the Publix detail API.

Usage:
1. Ensure you have purchase list files in raw/publix/
2. Update the authentication tokens below
3. Run: python publix_detail_scraper.py
"""

import json
import os
from datetime import datetime
from urllib.parse import quote

import requests
import urllib3

# Disable SSL warnings for this script
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PublixDetailScraper:
    """Scraper for Publix purchase detail API."""

    def __init__(self):
        # ⚠️ TOKENS FROM YOUR BROWSER REQUEST ⚠️
        self.bearer_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkwxeE10aHh3aFNMa0VaX2hldV9PNmF6NXF3dTNNbXI2azRDOHhjeHExc1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI0MmUzZDU3NC00ZDM4LTRkNzMtODhkYS0xYjg5NGFmYjUwY2EiLCJpc3MiOiJodHRwczovL2FjY291bnQucHVibGl4LmNvbS8zNzJjZGU1ZS1lZmEyLTRkYTUtOWI2Mi05ZWU5ZmQ5YzRiYjgvdjIuMC8iLCJleHAiOjE3NTE1NzMyMDgsIm5iZiI6MTc1MTU2OTYwOCwic3ViIjoiNWFlMTNiZjItN2MwMC00MmJkLTg4NTQtMTdlM2Y0MTlmOWYwIiwiT2JqZWN0IEdVSUQiOiI5NTg3M2E1Yy05ZmNmLTRiZGEtYTcyNy03MTY1Nzg0MWMyMjIiLCJwbHMiOjE3NTE1NTY1MDksImVtYWlsIjoicmFtaXJlempvMkBnbWFpbC5jb20iLCJuYW1lIjoiSmVubnkgQ29yb21vdG8gUmFtaXJleiBSb25kb24iLCJnaXZlbl9uYW1lIjoiSmVubnkgQ29yb21vdG8iLCJmYW1pbHlfbmFtZSI6IlJhbWlyZXogUm9uZG9uIiwiaXNGb3Jnb3RQYXNzd29yZCI6ZmFsc2UsIm5vbmNlIjoiNjM4ODcxNjY0MDcwOTYzNDUxLk9ETmtOVFpqWTJZdFlqZGpaUzAwWVdFM0xUaGlOVFl0TjJKaU9HUmhaV1ZpT0dVeE16RXpZVGsxWkdVdFlUSTFaaTAwTm1OaUxXRmpaR1V0Tmpjd1pEaGtPRGcwTVdabSIsInNjcCI6InB1YmxpeC5yZWFkIiwiYXpwIjoiNDJlM2Q1NzQtNGQzOC00ZDczLTg4ZGEtMWI4OTRhZmI1MGNhIiwidmVyIjoiMS4wIiwiaWF0IjoxNzUxNTY5NjA4fQ.KlX2YY9tXlZc4yk94BWu9U1h3N0D2PvttUSIsvItkvpYsxiNg3lmldJZnfuqW9MEg37RWW8Nigesi8xVOY2uhFoDp8HzCr1auk1-pv8bP---69HVeniCfuBulytYojeT7p3QF4hZYcIyORyEMMsbPa_Me9d4_oMRPLQ5R4q-pcTPT5R57AOjVa7eK9m2-NXyy2qcpNtPQyhB_hgmAx_vPl0pQ10ZRi2Wr0eZcv2vxQHbYWJ-FyLGrlYdAIzEgPTBrFRPhGeqENGeJxtUy4pd0xgNzvnEIfY-lNk800IzMMOe85r4d9sw6k8C2MLo6WKdKnpr7HF5o4CFp0-XgUZDyw"  # noqa: S105
        self.ecmsid = "cAKvj8yJFGsQGWEHxIqI5Q=="
        self.store_id = "583"
        self.akamai_telemetry = "a=B1F935F505CBEFDC415942B2C85F3A1F&&&e=MzE0MDgxOTczNDc0MzFGRTlBQzU5NkZCQTZCMkE3QTh+WUFBUXVBWXNGeEliamJDWEFRQUE2VHVWMFJ4Sjd4SUFlc2Z2cUZvejR3bEpuWXNvY1lDWDN1cHAwMjNTQk1taXllV01pdzYzdGpOek9jdFluNVQ2VFRCekdxUDhzMERMenI4bjZCQ2w5RHhlVnJVUzBBSXRSWTYvMTVKNkN0QWJWMzRrS3BYWEk0OTFtK21Td1FlNVg1c3lId1FwcmlCcUxYcVhvUUIxbzl3MUxScmhKdlBwak4vZUF2YTJaaEpVazFkWmM0cUwwMHFiWnR6U1I2ZFo1YWt2TjVjNWVEQVRqMklSaDNJMlBTK1BUVGNITGE5VmpkS1FxaEVSQlFHc3FIVzN0QnBnUGZudnYwTndUNTgzTFB3bllTV2dURk9nQWxybDFJWGgrZTN2aUlSTzNWeEMxU3p2UU85cGxsSGdFSUZFcnMwQ1JtS3lRM1doMjRTbEpjUmZ0Sm42T2VkbGllWHo2MkI0T09GcU0yZ21HMEJnRW9ZWE1NcG5aSm44OERaZFZ4aWh1YTh1WUFrZFA0eWxqNHJrM24yUENTRlFROWdkN3lVa0paQzZ5a01wZHA5Q0ViQlAwTVNKazBUMjFnK1dOOHd2UHJkYXc0Wk1jelNyNzU1VEVoWUxxdmxOamd5WU5uZlltcU1Vcll5M3RFNElkdDZDc1dCRm9KUWMrdXEzd1dWdzdPR0xiU2ZObks1QkgzUTF+NDYwNTIzNn4zMzYwMDY1&&&sensor_data=MzsxOzI7MDs0NjA1MjM2O2ZQTzg0WUFyekFFR2Q3YXJFY280WmlzK28zaitsN1NKc051dGUwZVVNWnM9OzcsMSwwLDAsMSwwOyIiPmp6IkppdCJZJTlYTmpBIkttcnciaSJnOWNOIjRXZSJDdUYiV2ZgLDIibS1EWSJsM0xTSiJxVmNWIkZtR0wgayIgWWxNIkoiLl4iRyJIUEAidHFuQVIiVTl+Ilg+RXRnIj9nI3cicEdlQmQ7LFhUIilaWyJdIiI8Ik4xcCJQdXpYT3cpVnR+InNCbiIrVUtWLHh4IkN+ImRNOG1RKilZWm9EIjQrIkR4MCtDIj1gIk8mdiEhYCQiRU9SIkIiIiU7SSJsfX4iUS1iUSZhKFdMd0giOldaIjR0bEQ2UyIkZHkieCJqdGAiNyJhYEJzWSI6O20iSnZkIiB2YF1kaEwjLV5CIkhQOiIsIiIsIixddSJiIiU+ImYiMU5FIm4idzgyVyhIczB7Pkh+dmZSMDZYaGN4TmwsQXk4K1BGV0JOdmNrNW9hYWl6O2ElSmYiJVBwImtEZCJyIklxYSwuWXx7QXkoSV55alkiVSIzKH4iZCBzNVkiKGdyIm5kfmh7eUFhRTdPNWIiIjoidW9zInZHZHh9IissTSJjIk81MWMvIkkxNyJuQjx7VyJpIiJNIlM5Ii1LIjNzRSJLIk9LaEtRZCtvNT5vbCRfN1gyXVB2fm47ZDQ2dTk8JG4mcmdRW1JgKy9NODRnIl0iWWYgIkR2TSAmIlRYfTAiVXNDY3ItMSJgbDwiNTYoTUMianx5IjsiSiJQTU8ie0Z4IksiOEFhSEFmJSoiaEU2IklTJCJnQTpRdXRxejVUJl4/LDVuKmQlKFs1MHYrTVp8O0J1dz8hMnwjbyhlTiBPSyRhM05+PS0zZDxKK0lkN0dyNiIlIi96YyJhIiIvInd0UCI7IiJSIj94SiJtIiJqIk1aTCJENiJfQUUibStaImoiIlYiSHB9IjZrV3B9ImMxdCI+SWhUXzFMUVVZO257bT9FeSJuVGtxImIiQnstcGkiIjluJSIzKVkiTEk/ImBZTTkiRiJBUmxNQUVkLlIzaVIqciJVIldLKCItaDk8a3tgIj8oZkEiRSBlKTQiLWg+IjgiIm8iI2JnInNRcHZZIkJJRiJGfTphRzljYSJpSSJOISFFKEJdXlZtMSNdYTNdQSIrKCgiV3FlZTFMMV9VIDFZInNjJjwiaS0+NmwiZ3d8NCJZMyxPY3ZiIk8tZiJybFZJKV4rViI7ZT4iTHw3IlFnaCItdkJYUlFgInojLXF3aV9uWiBVQ2FbQzo3Rk1xeC5dYHY/eztKcGxOP00hcVJ3SUA2LztPITpmVm5VXyolQ1V0TGhTT11qVn5yY1tiLCFAJHgtZmdrWilPbE9fKkEgOG81SXxicVU5cHRTa20ldzV0Ty59I0wtPVNIa3xYbyJDaGoiTCpgIiAiUCJTV20ibm9yImsibWxtTFEiWkJXIkNYXiItcUBdPXopeiI4SWgiQUIrcj5jVyxQSSIgci0iYH4vSz80VntwUmBmMC1dWCJzd2siTHplNFk+IihtImo2XSIsam5KIi0iJjYiXzE5ImpjV18iLCIiNiJgMngiWCZbR2tDO2ImLHciN1tyT1Q0PyJ6IiJsUXMiSE0ibDh3VCUiWVgiaTU9PFdufFh+IlhpImNfOXFjbDkiMlpXIlUrayxGU1kibHlfIm4iZUpwTVcgMDdzVF9lRmgiISFYImlfNSI+IiJeIlslUSJwInVpK008Y0c4IkUiKyBiInoiIjYifTZKIlAiIisieTUtIngiN1FnUkF8KlpyOCZ2WE8xMCwiby56bCMwZTYjS0ZxYyJiInBhXiJZRHhtXWJBWzYiWFNlfUQiVzAzIi11ZyJpIiJ5InxdQCJnIiIuInQybSJ7IiJEfC0="

        # API configuration
        self.detail_base_url = "https://services.publix.com/api/v1/PurchaseHistory/detail"
        self.list_dir = "raw/publix"
        self.detail_dir = "raw/publix"

        # Create directories if they don't exist
        os.makedirs(self.detail_dir, exist_ok=True)

        # Request headers
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,es-419;q=0.8,es;q=0.7",
            "akamai-bm-telemetry": self.akamai_telemetry,
            "authorization": f"Bearer {self.bearer_token}",
            "connection": "keep-alive",
            "ecmsid": self.ecmsid,
            "host": "services.publix.com",
            "origin": "https://www.publix.com",
            "publixstore": self.store_id,
            "referer": "https://www.publix.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

    def parse_purchase_datetime(self, date_str: str) -> tuple:
        """Parse Publix date format to get date and time components."""
        try:
            # Parse "2025-06-25T21:54:04" format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H-%M")
        except Exception as e:
            print(f"[WARNING] Could not parse date {date_str}: {e}")
            return "unknown-date", "00-00"

    def clean_store_name(self, store_name: str) -> str:
        """Clean store name for filename."""
        return store_name.replace(" ", "-").replace("&", "and").lower()

    def get_purchase_detail(self, transaction_key: str) -> dict | None:
        """Get detailed receipt data for a single purchase."""
        try:
            # URL encode the transaction key
            encoded_key = quote(transaction_key, safe="")
            url = f"{self.detail_base_url}?transactionKey={encoded_key}"

            print(f"🔍 Fetching detail for transaction: {transaction_key[:20]}...")

            response = requests.get(
                url,
                headers=self.headers,
                timeout=30,
                verify=False,  # Bypass SSL verification
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ Retrieved detail data")
                return data
            print(f"❌ Failed to get detail: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        except Exception as e:
            print(f"❌ Error fetching detail: {e}")
            return None

    def save_detail_file(self, purchase_data: dict, detail_data: dict) -> bool:
        """Save purchase detail to a JSON file."""
        try:
            # Extract info from original purchase data
            purchase = purchase_data.get("purchase", {})
            purchase_date_str = purchase.get("PurchaseDate", "")
            store_name = purchase.get("StoreName", "unknown-store")

            # Parse date and time
            date_part, time_part = self.parse_purchase_datetime(purchase_date_str)
            clean_store = self.clean_store_name(store_name)

            # Create filename: detail-YYYY-MM-DD-HH-MM-<location>.json
            filename = f"detail-{date_part}-{time_part}-{clean_store}.json"
            filepath = os.path.join(self.detail_dir, filename)

            # Combine original purchase data with detail data
            combined_data = {
                "scraped_at": datetime.now().isoformat(),
                "source": "publix_detail_api",
                "original_purchase": purchase,
                "detail": detail_data,
            }

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error saving detail: {e}")
            return False

    def load_purchase_files(self) -> list[dict]:
        """Load all purchase list files from raw/publix directory."""
        purchase_files = []

        if not os.path.exists(self.list_dir):
            print(f"❌ Directory {self.list_dir} does not exist")
            return purchase_files

        json_files = [
            f
            for f in os.listdir(self.list_dir)
            if f.endswith(".json") and not f.startswith("detail-")
        ]

        print(f"📁 Found {len(json_files)} purchase list files")

        for filename in sorted(json_files):
            filepath = os.path.join(self.list_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                    purchase_files.append(data)
                    print(f"   📄 Loaded: {filename}")
            except Exception as e:
                print(f"   ❌ Error loading {filename}: {e}")

        return purchase_files

    def scrape_all_details(self) -> None:
        """Scrape detailed receipt data for all purchases."""
        print("🏪 PUBLIX PURCHASE DETAIL SCRAPER")
        print("=" * 50)
        print("⚠️  MANUAL SETUP REQUIRED:")
        print("1. Ensure you have purchase list files in raw/publix/")
        print("2. Update Bearer token if expired (same as list scraper)")
        print("3. Run this script to get detailed receipt data")
        print()

        # Load all purchase files
        purchase_files = self.load_purchase_files()

        if not purchase_files:
            print("❌ No purchase files found to process")
            return

        total_purchases = len(purchase_files)
        processed_details = 0
        error_count = 0

        print(f"🚀 Processing {total_purchases} purchases for detailed data...")
        print()

        for i, purchase_data in enumerate(purchase_files, 1):
            purchase = purchase_data.get("purchase", {})
            transaction_id = purchase.get("Id", "")
            store_name = purchase.get("StoreName", "Unknown")
            purchase_date = purchase.get("PurchaseDate", "")
            total_price = purchase.get("TotalPrice", 0)

            print(f"📦 [{i}/{total_purchases}] {store_name} - {purchase_date} (${total_price})")

            if not transaction_id:
                print("   ⚠️  No transaction ID found, skipping")
                error_count += 1
                continue

            # Get detailed receipt data
            detail_data = self.get_purchase_detail(transaction_id)

            if detail_data:
                if self.save_detail_file(purchase_data, detail_data):
                    processed_details += 1
                else:
                    error_count += 1
            else:
                error_count += 1

            print()

        print("🎉 DETAIL SCRAPING COMPLETED!")
        print("=" * 50)
        print("📊 SUMMARY:")
        print(f"   📦 Total purchases processed: {total_purchases}")
        print(f"   ✅ Successfully retrieved details: {processed_details}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📁 Detail files saved to: {self.detail_dir}")


if __name__ == "__main__":
    scraper = PublixDetailScraper()
    scraper.scrape_all_details()
