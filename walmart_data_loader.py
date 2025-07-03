"""
Walmart Data Loader
Processes HTML files from raw/walmart/ and loads them into the database.

Usage:
    python walmart_data_loader.py

This script will:
1. Read all HTML files from raw/walmart/ (excluding orders-page-* files)
2. Extract JSON data from each HTML file
3. Parse order and item information
4. Save individual YAML files to data/walmart/
5. Load all data into the walmart_purchases database table
"""

import os
import re
import json
import yaml
from datetime import datetime, date
from bs4 import BeautifulSoup
from scripts.grocery_db import GroceryDB

def extract_json_from_html(html_content):
    """Extract JSON data from Walmart HTML page."""
    try:
        # Look for the __NEXT_DATA__ script tag
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the __NEXT_DATA__ script tag
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if next_data_script and next_data_script.string:
            return json.loads(next_data_script.string.strip())

        # Fallback: look for script tags with order data
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            if script.string and ('orderGroups' in script.string or 'priceDetails' in script.string):
                return json.loads(script.string.strip())

        return None

    except Exception as e:
        print(f"[ERROR] Failed to extract JSON: {e}")
        return None

def parse_order_data(json_data, filename):
    """Parse order data from extracted JSON."""
    try:
        # Navigate to order data in __NEXT_DATA__ structure
        try:
            order = json_data['props']['pageProps']['initialData']['data']['order']
        except (KeyError, TypeError):
            print(f"[WARNING] Could not find order data in {filename}")
            return None

        # Extract basic order information
        order_info = {
            'filename': filename,
            'raw_data': json_data,
            'order_id': order.get('id'),
            'order_type': order.get('type'),
            'order_date': order.get('orderDate'),
            'display_id': order.get('displayId'),
            'items': [],
            'order_totals': {}
        }

        # Extract order totals from priceDetails
        if 'priceDetails' in order:
            price_details = order['priceDetails']
            order_info['order_totals'] = {
                'subtotal': price_details.get('subTotal', {}).get('value'),
                'tax_total': price_details.get('taxTotal', {}).get('value'),
                'grand_total': price_details.get('grandTotal', {}).get('value'),
            }

        # Extract items from groups_2101
        if 'groups_2101' in order and order['groups_2101']:
            group = order['groups_2101'][0]

            # Extract group-level information
            order_info.update({
                'group_id': group.get('id'),
                'fulfillment_type': group.get('fulfillmentType'),
                'purchase_order_id': group.get('purchaseOrderId'),
                'is_pet_rx': group.get('isPetRx', False),
                'delivery_message': group.get('deliveryMessage'),
            })

            # Extract store information
            if 'store' in group:
                store = group['store']
                order_info.update({
                    'store_id': store.get('id'),
                    'store_name': store.get('name'),
                    'store_address': store.get('address', {}).get('addressLineOne'),
                })

            # Extract items
            if 'items' in group:
                order_info['items'] = parse_walmart_items(group['items'])

        return order_info

    except Exception as e:
        print(f"[ERROR] Failed to parse order data from {filename}: {e}")
        return None

def parse_walmart_items(items_data):
    """Parse items from Walmart order data."""
    parsed_items = []

    for item in items_data:
        item_info = {
            'item_id': item.get('id'),
            'item_quantity': item.get('quantity', 1),
        }

        # Extract product information
        if 'productInfo' in item:
            product_info = item['productInfo']
            item_info['item_name'] = product_info.get('name')

            # Extract image URL
            if 'imageInfo' in product_info:
                image_info = product_info['imageInfo']
                item_info['item_image_url'] = image_info.get('thumbnailUrl')

        # Extract price information
        if 'priceInfo' in item:
            price_info = item['priceInfo']
            if 'linePrice' in price_info:
                item_info['item_price'] = price_info['linePrice'].get('value')
                item_info['line_price'] = price_info['linePrice'].get('value')
            if 'itemPrice' in price_info:
                item_info['item_unit_price'] = price_info['itemPrice'].get('value')

        # Extract sales unit type
        if 'orderedSalesUnit' in item:
            item_info['sales_unit_type'] = item['orderedSalesUnit']

        parsed_items.append(item_info)

    return parsed_items

def parse_order_date(order_date_str):
    """Parse order date from Walmart format like '2022-07-16T11:23:23.000-0400'."""
    try:
        if order_date_str:
            # Parse the ISO format date
            # Remove timezone info for simpler parsing
            date_part = order_date_str.split('T')[0]
            return datetime.strptime(date_part, '%Y-%m-%d').date()
    except Exception as e:
        print(f"[WARNING] Could not parse order date {order_date_str}: {e}")

    return None

def parse_order_time(order_date_str):
    """Parse order time from Walmart format like '2022-07-16T11:23:23.000-0400'."""
    try:
        if order_date_str and 'T' in order_date_str:
            # Extract time part
            time_part = order_date_str.split('T')[1].split('.')[0]  # Remove milliseconds
            return datetime.strptime(time_part, '%H:%M:%S').time()
    except Exception as e:
        print(f"[WARNING] Could not parse order time {order_date_str}: {e}")

    return None

def extract_date_from_filename(filename):
    """Extract date from filename like 'jul16', 'feb01', etc. (fallback method)."""
    try:
        # Map month abbreviations to numbers
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        # Extract month and day from filename
        match = re.match(r'([a-z]{3})(\d{1,2})', filename.lower())
        if match:
            month_str, day_str = match.groups()
            month = month_map.get(month_str)
            day = int(day_str)

            # Assume current year or previous year based on current date
            current_year = datetime.now().year
            current_month = datetime.now().month

            # If the month is in the future, assume previous year
            year = current_year if month <= current_month else current_year - 1

            return date(year, month, day)

    except Exception as e:
        print(f"[WARNING] Could not extract date from filename {filename}: {e}")

    return None

def save_yaml_file(order_data, output_dir):
    """Save order data as YAML file."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on order date or current time
        purchase_date = order_data.get('purchase_date')
        if purchase_date:
            if isinstance(purchase_date, str):
                timestamp = purchase_date.replace('-', '-').replace(':', '-')
            else:
                timestamp = purchase_date.strftime('%Y-%m-%dT%H-%M-%S')
        else:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        
        filename = f"{timestamp}.yaml"
        filepath = os.path.join(output_dir, filename)
        
        # Prepare data for YAML (remove non-serializable items)
        yaml_data = {
            'order_id': order_data.get('order_id'),
            'purchase_date': str(order_data.get('purchase_date', '')),
            'store_name': order_data.get('store_name'),
            'order_totals': order_data.get('order_totals', {}),
            'items': order_data.get('items', []),
            'metadata': {
                'source_file': order_data.get('filename'),
                'processed_at': datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"[✓] Saved YAML: {filename}")
        return filepath
        
    except Exception as e:
        print(f"[ERROR] Failed to save YAML file: {e}")
        return None

def process_walmart_files():
    """Main function to process all Walmart files."""
    print("🛒 WALMART DATA LOADER")
    print("=" * 50)
    
    raw_dir = "./raw/walmart"
    output_dir = "./data/walmart"
    
    if not os.path.exists(raw_dir):
        print(f"❌ Directory {raw_dir} not found!")
        return
    
    # Get all HTML files (exclude orders-page-* files)
    html_files = []
    for filename in os.listdir(raw_dir):
        if not filename.startswith('orders-page-') and not filename.startswith('.'):
            html_files.append(filename)
    
    if not html_files:
        print(f"❌ No HTML files found in {raw_dir}")
        return
    
    print(f"📁 Found {len(html_files)} files to process")
    print()
    
    # Initialize database
    db = GroceryDB()
    
    processed_count = 0
    error_count = 0
    
    for filename in sorted(html_files):
        print(f"📄 Processing: {filename}")
        
        try:
            filepath = os.path.join(raw_dir, filename)
            
            # Read HTML file
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract JSON data
            json_data = extract_json_from_html(html_content)
            if not json_data:
                print(f"   ❌ No JSON data found")
                error_count += 1
                continue
            
            # Parse order data
            order_data = parse_order_data(json_data, filename)
            if not order_data:
                print(f"   ❌ Could not parse order data")
                error_count += 1
                continue
            
            # Extract date and time from order data (preferred) or filename (fallback)
            purchase_date = None
            purchase_time = None

            if order_data.get('order_date'):
                purchase_date = parse_order_date(order_data['order_date'])
                purchase_time = parse_order_time(order_data['order_date'])

            if not purchase_date:
                purchase_date = extract_date_from_filename(filename)

            if purchase_date:
                order_data['purchase_date'] = purchase_date
            if purchase_time:
                order_data['purchase_time'] = purchase_time
            
            # Save YAML file
            yaml_file = save_yaml_file(order_data, output_dir)
            if not yaml_file:
                print(f"   ❌ Failed to save YAML file")
                error_count += 1
                continue

            # Load into database
            success_count = load_order_to_database(db, order_data)
            
            if success_count > 0:
                print(f"   ✅ Loaded {success_count} items to database")
                processed_count += 1
            else:
                print(f"   ❌ Failed to load to database")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            error_count += 1
        
        print()
    
    # Summary
    print("🎉 PROCESSING COMPLETED!")
    print("=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {processed_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📁 YAML files saved to: {output_dir}")
    print(f"   🗃️  Data loaded to: walmart_purchases table")

def load_order_to_database(db, order_data):
    """Load order data into database."""
    try:
        success_count = 0
        
        # Prepare common order fields
        common_fields = {
            'order_id': order_data.get('order_id'),
            'group_id': order_data.get('group_id'),
            'purchase_order_id': order_data.get('purchase_order_id'),
            'display_id': order_data.get('display_id'),
            'purchase_date': order_data.get('purchase_date'),
            'purchase_time': order_data.get('purchase_time'),
            'order_type': order_data.get('order_type'),
            'fulfillment_type': order_data.get('fulfillment_type'),
            'status_type': order_data.get('status_type'),
            'delivery_message': order_data.get('delivery_message'),
            'store_id': order_data.get('store_id'),
            'store_name': order_data.get('store_name'),
            'store_address': order_data.get('store_address'),
            'subtotal': order_data.get('order_totals', {}).get('subtotal'),
            'tax_total': order_data.get('order_totals', {}).get('tax_total'),
            'grand_total': order_data.get('order_totals', {}).get('grand_total'),
            'is_pet_rx': order_data.get('is_pet_rx', False),
            'is_active': order_data.get('is_active', False),
            'is_shipped_by_walmart': order_data.get('is_shipped_by_walmart', False),
            'raw_data': order_data.get('raw_data')
        }
        
        # Insert each item as a separate row
        for item in order_data.get('items', []):
            item_record = common_fields.copy()
            item_record.update({
                'item_id': item.get('item_id'),
                'item_name': item.get('item_name'),
                'item_price': item.get('item_price'),
                'line_price': item.get('line_price'),
                'item_quantity': item.get('item_quantity', 1),
                'item_unit_price': item.get('item_unit_price'),
                'item_brand': item.get('item_brand'),  # Add missing field
                'item_category': item.get('item_category'),  # Add missing field
                'item_subcategory': item.get('item_subcategory'),  # Add missing field
                'item_sku': item.get('item_sku'),  # Add missing field
                'item_upc': item.get('item_upc'),  # Add missing field
                'item_image_url': item.get('item_image_url'),
                'sales_unit_type': item.get('sales_unit_type'),
                # Add other missing fields with defaults
                'shipping_total': None,
                'tracking_number': None,
                'carrier': None,
                'delivery_date': None,
                'pickup_date': None,
                'store_city': None,
                'store_state': None,
                'store_zip': None,
                'payment_method': None,
            })
            
            record_id = db.insert_walmart_purchase(item_record)
            if record_id:
                success_count += 1
        
        return success_count
        
    except Exception as e:
        print(f"[ERROR] Failed to load order to database: {e}")
        return 0

if __name__ == "__main__":
    process_walmart_files()
