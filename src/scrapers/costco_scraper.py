# ruff: noqa: E501, PTH103, PLR0911
"""
Costco Warehouse Receipts Scraper
Scrapes Costco receipts and saves them as individual YAML files.

SETUP INSTRUCTIONS:
1. Go to costco.com and log in
2. Go to My Account > Orders and Purchases
3. Click on "Warehouse" tab
4. Open browser Dev Tools (F12) > Network tab
5. Refresh the page
6. Find the 'graphql' request
7. Copy these two values from Request Headers:
   - costco-x-wcs-clientid: [paste below]
   - costco-x-authorization: Bearer [paste token below]
8. Update the tokens below and run the script
"""

import json
import os
from datetime import datetime, timedelta

import requests
import yaml

# 🔑 PASTE YOUR TOKENS HERE (from browser dev tools)
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlhrZTFoNXg5TV9ZMk5ER0YxU1hDX2xNNnVSTU5tZTJ3STBLRDlHNzl1QmciLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE3NTE0OTk4NjEsIm5iZiI6MTc1MTQ5ODk2MSwidmVyIjoiMS4wIiwiaXNzIjoiaHR0cHM6Ly9zaWduaW4uY29zdGNvLmNvbS9lMDcxNGRkNC03ODRkLTQ2ZDYtYTI3OC0zZTI5NTUzNDgzZWIvdjIuMC8iLCJzdWIiOiJlYzcxZjYyNS00MzgxLTQ1OGQtOWM5ZS1mYzZjYzVkMDU4OGUiLCJhdWQiOiJhM2E1MTg2Yi03Yzg5LTRiNGMtOTNhOC1kZDYwNGU5MzA3NTciLCJhY3IiOiJCMkNfMUFfU1NPX1dDU19zaWdudXBfc2lnbmluXzExNCIsIm5vbmNlIjoiZTBhMDZkOWQtODYxOS00ZjFiLTg4MjktOWRmYTcwY2JmNDY2IiwiaWF0IjoxNzUxNDk4OTYxLCJhdXRoX3RpbWUiOjE3NTE0NjYxMjcsImVtYWlsIjoicmFtaXJlempvMkBnbWFpbC5jb20iLCJyZW1lbWJlck1lIjoiVHJ1ZSIsIm5hbWUiOiJyYW1pcmV6am8yQGdtYWlsLmNvbSIsInVzZXJJZGVudGl0aWVzIjpbeyJpc3N1ZXIiOiJlNDQyZTZlNi0yNjAyLTRhMzktOTM3Yi04YjI4YjQ0NTdlZDMiLCJpc3N1ZXJVc2VySWQiOiJlYzcxZjYyNS00MzgxLTQ1OGQtOWM5ZS1mYzZjYzVkMDU4OGUifSx7Imlzc3VlciI6IjUwM2ZhNGY4LWYxY2EtNDA4Ni1hMDVjLTBhZGMxZTk1MTM1ZiIsImlzc3VlclVzZXJJZCI6ImVjNzFmNjI1LTQzODEtNDU4ZC05YzllLWZjNmNjNWQwNTg4ZSJ9LHsiaXNzdWVyIjoiYTNhNTE4NmItN2M4OS00YjRjLTkzYTgtZGQ2MDRlOTMwNzU3IiwiaXNzdWVyVXNlcklkIjoiQUFEOmVjNzFmNjI1LTQzODEtNDU4ZC05YzllLWZjNmNjNWQwNTg4ZSJ9LHsiaXNzdWVyIjoiNDkwMGViMWYtMGMxMC00YmQ5LTk5YzMtYzU5ZTZjMWVjZWJmIiwiaXNzdWVyVXNlcklkIjoiMTY5N2RmMWQtMDcxMS00N2UxLTk0ZWItOWU3NTgxMGQyNjUyIn0seyJpc3N1ZXIiOiIyZGQ0YjE0NS0zYmRhLTQ2NjktYWU2YS0zN2I4Y2I2ZGFmN2YiLCJpc3N1ZXJVc2VySWQiOiIxNjk3ZGYxZC0wNzExLTQ3ZTEtOTRlYi05ZTc1ODEwZDI2NTIifV0sImlzc3VlclVzZXJJZCI6IkFBRDplYzcxZjYyNS00MzgxLTQ1OGQtOWM5ZS1mYzZjYzVkMDU4OGUiLCJjbGllbnRJZCI6ImEzYTUxODZiLTdjODktNGI0Yy05M2E4LWRkNjA0ZTkzMDc1NyIsInNlbmRNZUVtYWlsIjoib2ZmIiwiaXBBZGRyZXNzIjoiMjMuMTIyLjk3LjIyNSJ9.BzpMf1FWYInTPFJ-f3Z9UxIju2Ri_DNZX751yJ68w2WTgFhkDphggLIu7aBV3nGNWjNfxRLEe-kghS7HEfsniMU4UNPcsIb0hbSxj0aDYLnqZlgi63SCp1H7V1M7YZtDwF37C9-aJ3mGN71xD3H1Dnp2oci5LwGiBK6_LgYW67op-q0oJTlZ8Aa8fVw9G68gGgkxbW8If3zrxdX_TqyfQmDxWaHO0UCvHvG_dz-fi0ZBGgy9rjvAoHY6sdPM_Vpeuy5sUTL7NgpWG3dhis1EH_6aHvrWnwLZNgwuBOJwuz9EnDuFOC-z-_vcgTt3Nr7qfjW3bk69m58d6QFJEaTM7A"  # noqa: S105
CLIENT_ID = "4900eb1f-0c10-4bd9-99c3-c59e6c1ecebf"


def save_receipt_to_yaml(receipt):
    """Save individual receipt to YAML file with date/time filename."""
    try:
        # Create data directory
        data_dir = "./data/costco"
        os.makedirs(data_dir, exist_ok=True)

        # Parse transaction date for filename
        transaction_datetime = receipt.get("transactionDateTime", "")
        if transaction_datetime:
            try:
                # Parse ISO datetime and format for filename
                dt = datetime.fromisoformat(transaction_datetime.replace("Z", "+00:00"))
                filename = dt.strftime("%Y-%m-%dT%H-%M-%S.yaml")
            except Exception:
                # Fallback filename if date parsing fails
                filename = (
                    f"receipt-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.yaml"
                )
        else:
            filename = f"receipt-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.yaml"

        filepath = os.path.join(data_dir, filename)

        # Prepare YAML data structure
        yaml_data = {
            "receipt_info": {
                "warehouse_name": receipt.get("warehouseName", "Unknown"),
                "warehouse_number": receipt.get("warehouseNumber", "N/A"),
                "warehouse_short_name": receipt.get("warehouseShortName", "N/A"),
                "transaction_date": receipt.get("transactionDate", "Unknown"),
                "transaction_datetime": receipt.get("transactionDateTime", "Unknown"),
                "transaction_barcode": receipt.get("transactionBarcode", "N/A"),
                "receipt_type": receipt.get("receiptType", "Unknown"),
                "document_type": receipt.get("documentType", "Unknown"),
                "transaction_type": receipt.get("transactionType", "Unknown"),
                "transaction_number": receipt.get("transactionNumber", "N/A"),
                "register_number": receipt.get("registerNumber", "N/A"),
                "operator_number": receipt.get("operatorNumber", "N/A"),
                "company_number": receipt.get("companyNumber", "N/A"),
                "invoice_number": receipt.get("invoiceNumber", "N/A"),
                "sequence_number": receipt.get("sequenceNumber", "N/A"),
                "membership_number": receipt.get("membershipNumber", "N/A"),
            },
            "store_info": {
                "warehouse_address1": receipt.get("warehouseAddress1", ""),
                "warehouse_address2": receipt.get("warehouseAddress2", ""),
                "warehouse_city": receipt.get("warehouseCity", ""),
                "warehouse_state": receipt.get("warehouseState", ""),
                "warehouse_country": receipt.get("warehouseCountry", ""),
                "warehouse_postal_code": receipt.get("warehousePostalCode", ""),
            },
            "financial_summary": {
                "subtotal": receipt.get("subTotal", 0),
                "taxes": receipt.get("taxes", 0),
                "total": receipt.get("total", 0),
                "instant_savings": receipt.get("instantSavings", 0),
                "total_item_count": receipt.get("totalItemCount", 0),
            },
            "items": [],
            "payment_methods": [],
            "tax_breakdown": receipt.get("subTaxes", {}),
            "coupons": receipt.get("couponArray", []),
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "scraper_version": "5.0-streamlined",
                "store": "Costco",
                "source": "warehouse_receipts_api",
            },
        }

        # Process items
        items = receipt.get("itemArray", [])
        for item in items:
            item_data = {
                "item_number": item.get("itemNumber", "N/A"),
                "item_description_01": item.get("itemDescription01", "Unknown Item"),
                "item_description_02": item.get("itemDescription02", ""),
                "french_item_description_1": item.get("frenchItemDescription1", ""),
                "french_item_description_2": item.get("frenchItemDescription2", ""),
                "item_identifier": item.get("itemIdentifier", ""),
                "item_department_number": item.get("itemDepartmentNumber", "N/A"),
                "unit": item.get("unit", "N/A"),
                "amount": item.get("amount", 0),
                "item_unit_price_amount": item.get("itemUnitPriceAmount", 0),
                "tax_flag": item.get("taxFlag", "N/A"),
                "merchant_id": item.get("merchantID", ""),
                "entry_method": item.get("entryMethod", ""),
                "trans_department_number": item.get("transDepartmentNumber", ""),
                "fuel_info": {
                    "fuel_unit_quantity": item.get("fuelUnitQuantity", ""),
                    "fuel_grade_code": item.get("fuelGradeCode", ""),
                    "fuel_uom_code": item.get("fuelUomCode", ""),
                    "fuel_uom_description": item.get("fuelUomDescription", ""),
                    "fuel_uom_description_fr": item.get("fuelUomDescriptionFr", ""),
                    "fuel_grade_description": item.get("fuelGradeDescription", ""),
                    "fuel_grade_description_fr": item.get("fuelGradeDescriptionFr", ""),
                },
            }
            yaml_data["items"].append(item_data)

        # Process payment methods
        tenders = receipt.get("tenderArray", [])
        for tender in tenders:
            tender_data = {
                "tender_type_code": tender.get("tenderTypeCode", ""),
                "tender_sub_type_code": tender.get("tenderSubTypeCode", ""),
                "tender_description": tender.get("tenderDescription", "Unknown"),
                "tender_type_name": tender.get("tenderTypeName", ""),
                "tender_type_name_fr": tender.get("tenderTypeNameFr", ""),
                "amount_tender": tender.get("amountTender", 0),
                "display_account_number": tender.get("displayAccountNumber", ""),
                "sequence_number": tender.get("sequenceNumber", ""),
                "approval_number": tender.get("approvalNumber", ""),
                "response_code": tender.get("responseCode", ""),
                "transaction_id": tender.get("transactionID", ""),
                "merchant_id": tender.get("merchantID", ""),
                "entry_method": tender.get("entryMethod", ""),
                "tender_acct_txn_number": tender.get("tenderAcctTxnNumber", ""),
                "tender_authorization_code": tender.get("tenderAuthorizationCode", ""),
                "tender_entry_method_description": tender.get(
                    "tenderEntryMethodDescription", ""
                ),
                "wallet_type": tender.get("walletType", ""),
                "wallet_id": tender.get("walletId", ""),
                "stored_value_bucket": tender.get("storedValueBucket", ""),
            }
            yaml_data["payment_methods"].append(tender_data)

        # Save to YAML file
        with open(filepath, "w") as f:
            yaml.dump(
                yaml_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        print(f"💾 Saved: {filename}")
        return filepath

    except Exception as e:
        print(f"❌ Error saving receipt: {e}")
        return None


def get_warehouse_receipts(months_back=3):
    """Get warehouse receipts for the specified number of months back."""

    # Check if tokens are set
    if (
        BEARER_TOKEN == "PASTE_YOUR_BEARER_TOKEN_HERE"  # noqa: S105
        or CLIENT_ID == "PASTE_YOUR_CLIENT_ID_HERE"
    ):
        print("❌ TOKENS NOT SET!")
        print()
        print("📝 SETUP INSTRUCTIONS:")
        print("1. Go to costco.com and log in")
        print("2. Go to My Account > Orders and Purchases")
        print("3. Click on 'Warehouse' tab")
        print("4. Open browser Dev Tools (F12) > Network tab")
        print("5. Refresh the page")
        print("6. Find the 'graphql' request")
        print("7. Copy these values from Request Headers:")
        print("   - costco-x-wcs-clientid: [update CLIENT_ID in this file]")
        print("   - costco-x-authorization: Bearer [update BEARER_TOKEN in this file]")
        print("8. Update the tokens in this file and run again")
        return False, None

    print("🏪 Costco Warehouse Receipts Scraper")
    print("=" * 50)
    print(f"🔑 Token: {BEARER_TOKEN[:50]}...")
    print(f"🆔 Client: {CLIENT_ID}")

    try:
        # Calculate date range (last N months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)  # Approximate months
        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        print(
            f"📅 Querying: {start_date_str} to {end_date_str} (last {months_back} months)"
        )

        # API endpoint
        url = "https://ecom-api.costco.com/ebusiness/order/v1/orders/graphql"

        # Headers - exact match from successful requests
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,es-419;q=0.8,es;q=0.7",
            "client-identifier": "481b1aec-aa3b-454b-b81b-48187e28f205",
            "connection": "keep-alive",
            "content-type": "application/json-patch+json",
            "costco-x-authorization": f"Bearer {BEARER_TOKEN}",
            "costco-x-wcs-clientid": CLIENT_ID,
            "costco.env": "ecom",
            "costco.service": "restOrders",
            "host": "ecom-api.costco.com",
            "origin": "https://www.costco.com",
            "referer": "https://www.costco.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        # Enhanced GraphQL query with all fields
        query = """query receiptsWithCounts($startDate: String!, $endDate: String!,$documentType:String!,$documentSubType:String!) {
    receiptsWithCounts(startDate: $startDate, endDate: $endDate,documentType:$documentType,documentSubType:$documentSubType) {
    inWarehouse
    gasStation
    carWash
    gasAndCarWash
    receipts{
      warehouseName
      receiptType
      documentType
      transactionDateTime
      transactionDate
      companyNumber
      warehouseNumber
      operatorNumber
      warehouseName
      warehouseShortName
      registerNumber
      transactionNumber
      transactionType
      transactionBarcode
      total
      warehouseAddress1
      warehouseAddress2
      warehouseCity
      warehouseState
      warehouseCountry
      warehousePostalCode
      totalItemCount
      subTotal
      taxes
      total
      invoiceNumber
      sequenceNumber
      itemArray {
        itemNumber
        itemDescription01
        frenchItemDescription1
        itemDescription02
        frenchItemDescription2
        itemIdentifier
        itemDepartmentNumber
        unit
        amount
        taxFlag
        merchantID
        entryMethod
        transDepartmentNumber
        fuelUnitQuantity
        fuelGradeCode
        itemUnitPriceAmount
        fuelUomCode
        fuelUomDescription
        fuelUomDescriptionFr
        fuelGradeDescription
        fuelGradeDescriptionFr
      }
      tenderArray {
        tenderTypeCode
        tenderSubTypeCode
        tenderDescription
        amountTender
        displayAccountNumber
        sequenceNumber
        approvalNumber
        responseCode
        tenderTypeName
        transactionID
        merchantID
        entryMethod
        tenderAcctTxnNumber
        tenderAuthorizationCode
        tenderTypeName
        tenderTypeNameFr
        tenderEntryMethodDescription
        walletType
        walletId
        storedValueBucket
      }
      subTaxes {
        tax1
        tax2
        tax3
        tax4
        aTaxPercent
        aTaxLegend
        aTaxAmount
        aTaxPrintCode
        aTaxPrintCodeFR
        aTaxIdentifierCode
        bTaxPercent
        bTaxLegend
        bTaxAmount
        bTaxPrintCode
        bTaxPrintCodeFR
        bTaxIdentifierCode
        cTaxPercent
        cTaxLegend
        cTaxAmount
        cTaxIdentifierCode
        dTaxPercent
        dTaxLegend
        dTaxAmount
        dTaxPrintCode
        dTaxPrintCodeFR
        dTaxIdentifierCode
        uTaxLegend
        uTaxAmount
        uTaxableAmount
      }
      couponArray {
        upcnumberCoupon
      }
      instantSavings
      membershipNumber
    }
  }
}"""

        # Variables for the query
        variables = {
            "startDate": start_date_str,
            "endDate": end_date_str,
            "text": f"Last {months_back} Months",
            "documentType": "all",
            "documentSubType": "all",
        }

        payload = {
            "query": query,
            "variables": variables,
        }

        print("\n🌐 Making API request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"📡 Response Status: {response.status_code}")

        if response.status_code == 200:  # noqa: PLR2004
            data = response.json()
            print("✅ API CALL SUCCESSFUL!")

            # Save raw response
            with open("warehouse_receipts_response.json", "w") as f:
                json.dump(data, f, indent=2)
            print("💾 Raw response saved to: warehouse_receipts_response.json")

            # Parse the response
            if "data" in data and "receiptsWithCounts" in data["data"]:
                receipts_data = data["data"]["receiptsWithCounts"]
                receipts = receipts_data.get("receipts", [])

                print("\n📊 WAREHOUSE RECEIPTS RESULTS:")
                print(
                    f"   🏪 In-warehouse receipts: {receipts_data.get('inWarehouse', 0)}"
                )
                print(
                    f"   ⛽ Gas station receipts: {receipts_data.get('gasStation', 0)}"
                )
                print(f"   🚗 Car wash receipts: {receipts_data.get('carWash', 0)}")
                print(f"   🔄 Gas + Car wash: {receipts_data.get('gasAndCarWash', 0)}")
                print(f"   📄 Total receipts found: {len(receipts)}")

                # Save ALL receipts to YAML files
                if receipts:
                    print(f"\n💾 Saving ALL {len(receipts)} receipts to YAML files...")
                    saved_count = 0
                    total_items = 0

                    for receipt in receipts:
                        yaml_file = save_receipt_to_yaml(receipt)
                        if yaml_file:
                            saved_count += 1
                        total_items += len(receipt.get("itemArray", []))

                    print(
                        f"✅ Successfully saved {saved_count} receipts to ./data/costco/"
                    )
                    print(f"📦 Total items: {total_items}")
                    print("\n🎉 SUCCESS! All receipts saved as YAML files!")
                    print("📁 Location: ./data/costco/")
                    print("💡 Ready for database import!")

                    return True, data
                print("⚠️ No receipts found for the specified period")
                return True, data

            print("⚠️ Unexpected API response format")
            if "errors" in data:
                print(f"Errors: {data['errors']}")
            return False, data

        if response.status_code == 401:  # noqa: PLR2004
            print("❌ AUTHENTICATION FAILED")
            print("💡 Your token has expired. Get a fresh one:")
            print("   1. Go to costco.com > My Account > Orders and Purchases")
            print("   2. Click on 'Warehouse' tab")
            print("   3. Open Dev Tools (F12) > Network tab")
            print("   4. Refresh the page")
            print("   5. Find 'graphql' request")
            print("   6. Copy the new Bearer token and Client ID")
            print("   7. Update BEARER_TOKEN and CLIENT_ID in this file")
            return False, None
        print(f"❌ API ERROR: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        return False, None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, None


def main():
    """Main entry point for Costco scraper."""
    print("🏪 Costco Warehouse Receipts Scraper")
    print("=" * 60)
    print("📝 Scrapes Costco receipts and saves as YAML files")
    print("🎯 Default: Last 3 months (modify months_back parameter)")
    print()

    # Run scraper for last 3 months (change this number as needed)
    success, _ = get_warehouse_receipts(months_back=3)

    if success:
        print("\n🎉 SCRAPING COMPLETED SUCCESSFULLY!")
        print("💡 Next step: Run the database loader to import YAML files")
    else:
        print("\n❌ Scraping failed")
        print("🔄 Check token setup and try again")

    print("\n📝 Remember: Tokens expire every 15-30 minutes")
    print("🔄 Update tokens when needed")


if __name__ == "__main__":
    main()
