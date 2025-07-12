#!/usr/bin/env python3
"""
Publix Purchases List Scraper

Scrapes the Publix purchases list API and saves each purchase as a separate JSON file
in the raw/publix directory, organized by purchase date.

Usage:
1. Update the authentication tokens below
2. Run: python publix_list_scraper.py
"""

import json
import os
from datetime import datetime

import requests
import urllib3

# Disable SSL warnings for this script
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PublixListScraper:
    """Scraper for Publix purchases list API."""

    def __init__(self):
        # ⚠️ UPDATE THESE VALUES WITH YOUR ACTUAL TOKENS ⚠️
        self.bearer_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkwxeE10aHh3aFNMa0VaX2hldV9PNmF6NXF3dTNNbXI2azRDOHhjeHExc1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI0MmUzZDU3NC00ZDM4LTRkNzMtODhkYS0xYjg5NGFmYjUwY2EiLCJpc3MiOiJodHRwczovL2FjY291bnQucHVibGl4LmNvbS8zNzJjZGU1ZS1lZmEyLTRkYTUtOWI2Mi05ZWU5ZmQ5YzRiYjgvdjIuMC8iLCJleHAiOjE3NTE1NzMyMDgsIm5iZiI6MTc1MTU2OTYwOCwic3ViIjoiNWFlMTNiZjItN2MwMC00MmJkLTg4NTQtMTdlM2Y0MTlmOWYwIiwiT2JqZWN0IEdVSUQiOiI5NTg3M2E1Yy05ZmNmLTRiZGEtYTcyNy03MTY1Nzg0MWMyMjIiLCJwbHMiOjE3NTE1NTY1MDksImVtYWlsIjoicmFtaXJlempvMkBnbWFpbC5jb20iLCJuYW1lIjoiSmVubnkgQ29yb21vdG8gUmFtaXJleiBSb25kb24iLCJnaXZlbl9uYW1lIjoiSmVubnkgQ29yb21vdG8iLCJmYW1pbHlfbmFtZSI6IlJhbWlyZXogUm9uZG9uIiwiaXNGb3Jnb3RQYXNzd29yZCI6ZmFsc2UsIm5vbmNlIjoiNjM4ODcxNjY0MDcwOTYzNDUxLk9ETmtOVFpqWTJZdFlqZGpaUzAwWVdFM0xUaGlOVFl0TjJKaU9HUmhaV1ZpT0dVeE16RXpZVGsxWkdVdFlUSTFaaTAwTm1OaUxXRmpaR1V0Tmpjd1pEaGtPRGcwTVdabSIsInNjcCI6InB1YmxpeC5yZWFkIiwiYXpwIjoiNDJlM2Q1NzQtNGQzOC00ZDczLTg4ZGEtMWI4OTRhZmI1MGNhIiwidmVyIjoiMS4wIiwiaWF0IjoxNzUxNTY5NjA4fQ.KlX2YY9tXlZc4yk94BWu9U1h3N0D2PvttUSIsvItkvpYsxiNg3lmldJZnfuqW9MEg37RWW8Nigesi8xVOY2uhFoDp8HzCr1auk1-pv8bP---69HVeniCfuBulytYojeT7p3QF4hZYcIyORyEMMsbPa_Me9d4_oMRPLQ5R4q-pcTPT5R57AOjVa7eK9m2-NXyy2qcpNtPQyhB_hgmAx_vPl0pQ10ZRi2Wr0eZcv2vxQHbYWJ-FyLGrlYdAIzEgPTBrFRPhGeqENGeJxtUy4pd0xgNzvnEIfY-lNk800IzMMOe85r4d9sw6k8C2MLo6WKdKnpr7HF5o4CFp0-XgUZDyw"
        self.ecmsid = "cAKvj8yJFGsQGWEHxIqI5Q=="
        self.store_id = "583"
        self.akamai_telemetry = "a=B1F935F505CBEFDC415942B2C85F3A1F&&&e=NEM0QTU4NzI4MzQyNDY3MUY5ODgxRjkyMjgxNDdFODJ+WUFBUUUvd3hGODNWM01TWEFRQUF0RWF2MFJ6QVNOa2ZoYjRvTFZSZi9mVXBrL2ZmZXdQR0NIRXEyZmREOXFveEp4Z3MwZG1TcUtEYUdrMTNlQmtpTWlGODFkajVLQTlnblZHY3laYTdiV2pvZ1FYbjhWSXJZT3FUZFQ0YWJuQ1llb3M4MDRMbUU3Y2VmYzVkT1RMOVRRL1lXRHJOQ3NPOVIyY2NoT3NWS01uYWdwek4vK1hXajJOdEgzcFFhNFdYVGhxalAwWUxPait2U3FSUEk1bEZ1YWhRZ2dYTE5TU3FBSHRjOHNVUlVZSVlYSklmUjBJN2pmbjB2QjIyQi8wNXhoR1d3VjJMMzFham03aUQ2djN1WnFvVjBQRDFERDFKcWlJMFMyd1YvQ1g4RC9adlplWEtpODVUcVlqaTRoamVtU3hldzdBaFY3MUdHSVhvKzV1cUY3cGI5akhJbWREZkJjVmIrcElYZ1F5d3ZOcHYwWDUzZ3F0N0JzY2pWbTVaYWtBcFZzblVGTVo2YjUwZmJVQzNuR1preXJnVC95VG53b1Z2cHExcVdRVzZZUVpBdUJUL3V1Z2VSR3FLOWpoeTVxcytCczVaemVlYWZXaytIZnMxY25FV3lhYnlvT3NNWUxxcWsvbHZJUGhSZzEvQnBrLy9DMjQ2WXB1OHVuQ1NZUEtydDNjU0d2cmpEQ3ZGU1pHTGNkZFpRMkpDQ1VIMVdiYWZTclh3aDdKdGxTVXRSbXF0dWFHVlFZbTVnc0g1WnpUK0ZxS3JBUT09fjM0MjU1ODV+NDYwMTE1Nw==&&&sensor_data=MzsxOzI7MDszNDI1NTg1O2ZQTzg0WUFyekFFR2Q3YXJFY280WmlzK28zaitsN1NKc051dGUwZVVNWnM9OzMsNTEsMCwwLDEsMDsiIixQSSIjZDMiR3ZuYGciY2YpJSIlIno7fWwiaDE8ImdadCJaYzMwQSI1fXt0IlttaytyIlJLVnEiJig2Sng5Ink6fHkiTiJkdGlWKSxdJEFWdEtYQi93JG5ea1Bfdl14KEVsIEdxZy1HdFJsbTQ7bmAgJCNKajBrbFJJS34iJCJwSncifGtWNU4iN0ZUIlV4LVJYIlpNLlMicjBQLlpJXktzImd7eyJ9IktLY3VFYixKIyZLP0N1R0tQfkAqIj8iP3FVInJhcXpwX11QVCkicHxqImpaYz1rdXQiUFEiNmheI2R8ICl+bTwiRl4ifT13QSYkYVQiOm0iZTRSRHF2RiJnZVMiQCIlIm0oQiI5YkUidDJRbGsiJT12Iih5UTd0TSJ5PyoiRyJfcjYiRSJwfEs4ZSJQclciT1g/Ikche1h+X2wsazM6Im9zOSJqIiJ1InMzdSJxIlV0OSAiUiJ4cCQiPCJafH1vKSlCfUdhfThBNmVPPTc0IWUzbi5SfWAoZTVjeTcxfVt7IFt3bUBReyZjWCJOLHsiP1tFImsiQEpMS2ZsPGcsNUQtOGtGUCJbInxXRyJfWUwuVSItNi0iITgjblhuXisqeGM8LyIiTCIkLnIiTiR6LU0id2pBImYiSGp0K1giQE9PIkNIJCo6IkwiIisic3wiMksiTU5hImIiaG9pSyQqJGBMQEA8YjFqcVFoZ1piIVBAZTFrSjszYCxeWXshVWNeZTl3PVsiWyJJaVgiXj1AcEciLypVYSIgT2AkeDllIl55aSJ3X2l5LSJANTUiMyJlIjdUSSIgYW0iOyJnc2hWeDoldiJoaUEiRmxoIi9qOUc1LlZPdyxvPiZbYXgzP3E5ZWZLYGBENGptLis3O3xeTXZZOnJoOndVMVM+NG9ZSH1DQEU9Vi49bntCIjAiWihdIn0iIi8ibklFInIiIkIiVC8xImsiIk8iLkpsIk01IjRCNSJuT3cieCIibSI1QzciICRuOTkiKVorIj1HSDdlPiRyREc3XTFWQH5gIkFIYj4iTCJEbD1jbyIidUc7InZfZyJ4YHEiMWwlVSIzIiIpIn45MyJbOVg5aEIifHtIcyI+TntNPSJvUlQiVSIiZiJMJkkiVXNLfGEiXipuIlI1MT1OIWNOIjFtIjIkZ0ZXeHFVcCpYLGlNJm5IIj5CfSJ3MVdBemtpeGVbTD8iV35AKyJxd0UvayI2bV85IlZ0Y110RCAiUVFSIiBzfVU/VDh+InxGMSImLE8ibk8yIkg3Kk1ZQl8ielJhYlliRmg+YGlQfG5wR0o3QHshWHAjbUA+Yj1EViYrYDNVfmR5e1JQKjAqL25IbSotdHdRRWkvTF9ZLDJ6KjhYR3hDUEtCITMwK14zeiRHZWZobXFhV1Bvc095T0hdcyxCZ3YreXUgdSM5K0ZpWW1lb2p2Ilc1YSIvV0MiayIrImM1PCJQUzAiWiImaSZFUSI5NzoiMlZBIkgkbHtyL0xnIlViMSJnSThNaVY5fC00IjpKWCIqcFtqNilfe3tLYT1qLFhlISEiYWVFIjc8Ni43KSJHRyIhJDsiQzA3YSJtImdEIilEUCI4UG5qIjsiImEiIEFCIm9Rd3tyRmFqNVs1IjZRK0JbV1oiISJbInFuVSIkbiI9fmM+aSJVYCIsVUh7WC1SbiUifD4iSThPYndCaCJKUXYiOWc/QSpfeCJzaDAiJCJ7SlBWL11tbDNDaSxhLSJaMXYiSyFGIj0iIm4iemxNIikiVF45d3F8UG5FaiJeIjVjaiJ8IiJxIktCdCImIiIxIiNzNCIrIm5MY0Bsd0IhdHR8KmMySV5gIntLWz5EIHNBeTBELCUiMyJ8UTQicl50TVZzQzpOIjZoYUFrImhyKSI1TW0ieiIibCJhOjMidCIiJSJuaigiUCIqbH53cGFsRDFIPm8oTTlnPzBeLEIwZGladzZlXUc+enZ2UHJgSSloTm9sO2FSZ08lWWRaQDE3UnM6NWVYfXxlIkM/Vg=="  # From akamai-bm-telemetry header

        # API configuration
        self.base_url = (
            "https://services.publix.com/api/v4/customer/publix/purchaseslist"
        )
        self.raw_dir = "raw/publix"

        # Create raw directory if it doesn't exist
        os.makedirs(self.raw_dir, exist_ok=True)

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

    def parse_purchase_date(self, date_str: str) -> str:
        """Parse Publix date format to YYYY-MM-DD."""
        try:
            # Parse "2025-06-25T21:54:04" format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[WARNING] Could not parse date {date_str}: {e}")
            return "unknown-date"

    def get_purchases_page(
        self, page: int = 1, items_per_page: int = 100
    ) -> dict | None:
        """Get a single page of purchases from Publix API."""
        params = {
            "page": page,
            "itemsPerPage": items_per_page,
            "sortOrder": "DESC",
            "filter": "NONE",
        }

        try:
            print(f"🔍 Fetching purchases page {page}...")
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30,
                verify=False,  # Bypass SSL verification
            )

            if response.status_code == 200:
                data = response.json()
                print(
                    f"✅ Page {page}: Found {len(data.get('PurchasesList', []))} purchases"
                )
                return data
            print(f"❌ Failed to get page {page}: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        except Exception as e:
            print(f"❌ Error fetching page {page}: {e}")
            return None

    def save_purchase_file(self, purchase: dict) -> bool:
        """Save a single purchase to a JSON file."""
        try:
            # Parse purchase date for filename
            purchase_date = self.parse_purchase_date(purchase.get("PurchaseDate", ""))
            store_name = (
                purchase.get("StoreName", "unknown-store").replace(" ", "-").lower()
            )
            total_price = purchase.get("TotalPrice", 0)

            # Create filename: YYYY-MM-DD_store-name_$total.json
            filename = f"{purchase_date}_{store_name}_{total_price:.2f}.json"
            filepath = os.path.join(self.raw_dir, filename)

            # Add metadata to purchase data
            purchase_data = {
                "scraped_at": datetime.now().isoformat(),
                "source": "publix_list_api",
                "purchase": purchase,
            }

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(purchase_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error saving purchase: {e}")
            return False

    def scrape_all_purchases(self) -> None:
        """Scrape all purchases from Publix API and save to files."""
        print("🏪 PUBLIX PURCHASES LIST SCRAPER")
        print("=" * 50)
        print("⚠️  MANUAL SETUP REQUIRED:")
        print("1. Log into Publix.com")
        print("2. Go to Purchase History page")
        print("3. Open Developer Tools (F12)")
        print("4. Look at Network tab for API calls to /purchaseslist")
        print("5. Extract from REQUEST HEADERS:")
        print("   - authorization: Bearer [JWT_TOKEN]")
        print("   - ecmsid: [SESSION_ID]")
        print("   - publixstore: [STORE_ID]")
        print("   - akamai-bm-telemetry: [TELEMETRY_DATA]")
        print("6. Update this script with your actual values")
        print()

        total_purchases = 0
        saved_purchases = 0
        page = 1

        while True:
            # Get current page with 100 items
            page_data = self.get_purchases_page(page, items_per_page=100)

            if not page_data:
                print(f"❌ Failed to get page {page}, stopping")
                break

            purchases = page_data.get("PurchasesList", [])
            total_count = page_data.get("TotalCount", 0)
            total_pages = page_data.get("TotalPages", 1)

            print(
                f"📊 Page {page}/{total_pages}: Found {len(purchases)} purchases (Total: {total_count})"
            )

            if not purchases:
                print(f"📄 No purchases found on page {page}")
                break

            # Process each purchase on this page
            page_saved = 0
            for purchase in purchases:
                total_purchases += 1
                if self.save_purchase_file(purchase):
                    saved_purchases += 1
                    page_saved += 1

            print(
                f"   ✅ Saved {page_saved}/{len(purchases)} purchases from page {page}"
            )

            # Check if this is the last page
            if page >= total_pages:
                print(f"📄 Reached last page ({total_pages})")
                break

            # Continue to next page
            page += 1
            print(f"🔄 Moving to page {page}...")
            print()

        print("\n🎉 SCRAPING COMPLETED!")
        print("=" * 50)
        print("📊 SUMMARY:")
        print(f"   📦 Total purchases found: {total_purchases}")
        print(f"   💾 Successfully saved: {saved_purchases}")
        print(f"   ❌ Failed to save: {total_purchases - saved_purchases}")
        print(f"   📁 Files saved to: {self.raw_dir}")


if __name__ == "__main__":
    scraper = PublixListScraper()
    scraper.scrape_all_purchases()
