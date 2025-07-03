"""
Debug script to examine Walmart JSON structure
"""

import json
from bs4 import BeautifulSoup

def debug_walmart_file(filename):
    """Debug a single Walmart file to see JSON structure."""
    print(f"🔍 Debugging: {filename}")
    print("=" * 50)
    
    # Read the file
    with open(f"raw/walmart/{filename}", 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract JSON
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the __NEXT_DATA__ script tag
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if next_data_script and next_data_script.string:
        try:
            json_data = json.loads(next_data_script.string.strip())
            print("✅ Found __NEXT_DATA__ JSON")
            
            # Explore the structure
            print("\n📋 Top-level keys:")
            for key in json_data.keys():
                print(f"  - {key}")
            
            # Look for props
            if 'props' in json_data:
                print("\n📋 props keys:")
                for key in json_data['props'].keys():
                    print(f"  - {key}")
                
                # Look for pageProps
                if 'pageProps' in json_data['props']:
                    print("\n📋 pageProps keys:")
                    for key in json_data['props']['pageProps'].keys():
                        print(f"  - {key}")
                    
                    # Look for initialData
                    if 'initialData' in json_data['props']['pageProps']:
                        print("\n📋 initialData keys:")
                        for key in json_data['props']['pageProps']['initialData'].keys():
                            print(f"  - {key}")
                        
                        # Look for data
                        if 'data' in json_data['props']['pageProps']['initialData']:
                            print("\n📋 data keys:")
                            data = json_data['props']['pageProps']['initialData']['data']
                            for key in data.keys():
                                print(f"  - {key}")

                            # Look for order (individual order detail page)
                            if 'order' in data:
                                print("\n📋 order keys:")
                                order = data['order']
                                for key in order.keys():
                                    print(f"  - {key}")

                                # Show basic order info
                                print(f"\n📦 Order ID: {order.get('id', 'N/A')}")
                                print(f"📦 Order Type: {order.get('type', 'N/A')}")
                                print(f"📦 Order Date: {order.get('orderDate', 'N/A')}")

                                # Look for groups_2101 (seems to be the items)
                                if 'groups_2101' in order:
                                    print(f"\n📋 Found groups_2101 with {len(order['groups_2101'])} groups")

                                    if order['groups_2101']:
                                        group = order['groups_2101'][0]
                                        print("\n📋 First group keys:")
                                        for key in group.keys():
                                            print(f"  - {key}")

                                        # Look for items
                                        if 'items' in group:
                                            print(f"\n📋 Found {len(group['items'])} items")
                                            if group['items']:
                                                item = group['items'][0]
                                                print("\n📋 First item keys:")
                                                for key in item.keys():
                                                    print(f"  - {key}")

                                                # Show item name and price
                                                print(f"\n📦 Item: {item.get('name', 'N/A')}")
                                                if 'priceInfo' in item:
                                                    price_info = item['priceInfo']
                                                    print("\n📋 priceInfo keys:")
                                                    for key in price_info.keys():
                                                        print(f"  - {key}")
                                                    if 'linePrice' in price_info:
                                                        print(f"💰 Line Price: {price_info['linePrice'].get('displayValue', 'N/A')}")
                                                    if 'itemPrice' in price_info:
                                                        print(f"💰 Item Price: {price_info['itemPrice'].get('displayValue', 'N/A')}")

                                # Look for priceDetails at order level
                                if 'priceDetails' in order:
                                    print("\n📋 Order priceDetails keys:")
                                    price_details = order['priceDetails']
                                    for key in price_details.keys():
                                        print(f"  - {key}")

                                    # Show totals
                                    if 'subTotal' in price_details:
                                        print(f"💰 Subtotal: {price_details['subTotal'].get('displayValue', 'N/A')}")
                                    if 'taxTotal' in price_details:
                                        print(f"💰 Tax: {price_details['taxTotal'].get('displayValue', 'N/A')}")
                                    if 'grandTotal' in price_details:
                                        print(f"💰 Total: {price_details['grandTotal'].get('displayValue', 'N/A')}")

                                # Look for orderGroups in the order (fallback)
                                if 'orderGroups' in order:
                                    print(f"\n📋 Found {len(order['orderGroups'])} order groups")

                                    if order['orderGroups']:
                                        group = order['orderGroups'][0]
                                        print("\n📋 First order group keys:")
                                        for key in group.keys():
                                            print(f"  - {key}")

                                        # Look for items
                                        if 'items' in group:
                                            print(f"\n📋 Found {len(group['items'])} items")
                                            if group['items']:
                                                item = group['items'][0]
                                                print("\n📋 First item keys:")
                                                for key in item.keys():
                                                    print(f"  - {key}")

                                                # Show item name and price
                                                print(f"\n📦 Item: {item.get('name', 'N/A')}")
                                                if 'priceInfo' in item:
                                                    price_info = item['priceInfo']
                                                    if 'linePrice' in price_info:
                                                        print(f"💰 Price: {price_info['linePrice'].get('displayValue', 'N/A')}")

                                        # Look for priceDetails
                                        if 'priceDetails' in group:
                                            print("\n📋 priceDetails keys:")
                                            price_details = group['priceDetails']
                                            for key in price_details.keys():
                                                print(f"  - {key}")

                                            # Show totals
                                            if 'subTotal' in price_details:
                                                print(f"💰 Subtotal: {price_details['subTotal'].get('displayValue', 'N/A')}")
                                            if 'grandTotal' in price_details:
                                                print(f"💰 Total: {price_details['grandTotal'].get('displayValue', 'N/A')}")

                                        # Look for store
                                        if 'store' in group:
                                            store = group['store']
                                            print(f"\n🏪 Store: {store.get('name', 'N/A')}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
    else:
        print("❌ No __NEXT_DATA__ script tag found")

if __name__ == "__main__":
    # Debug a few files
    test_files = ['jul16', 'feb01', 'apr2']
    
    for filename in test_files:
        debug_walmart_file(filename)
        print("\n" + "="*70 + "\n")
