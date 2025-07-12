# Publix Data Collection System

Complete guide for collecting Publix grocery purchase data using their web API with Bearer token authentication and receipt parsing.

## 🎯 Overview

The Publix system collects purchase data through a 3-step process:
1. **List Collection** - Get all purchase transactions
2. **Detail Collection** - Get detailed receipts for each transaction  
3. **Data Processing** - Parse receipts and load into database

## 📋 Prerequisites

- Python 3.8+
- Active Publix account with purchase history
- Chrome/Firefox Developer Tools access

## 🔧 Setup Instructions

### Step 1: Extract Authentication Headers

1. **Log into Publix** at https://www.publix.com
2. **Navigate to Purchases** - Go to your account purchases page
3. **Open Developer Tools** (F12)
4. **Go to Network Tab** and filter by XHR
5. **Look for purchase list request** - Find the XHR request that loads your purchase list
6. **Copy Required Headers** from the request:

```bash
# Required headers to copy:
akamai-bm-telemetry: YOUR_TELEMETRY_HERE
authorization: Bearer YOUR_TOKEN_HERE  
ecmsid: YOUR_ECMS_ID_HERE
```

### Step 2: Update Script Configuration

Edit the authentication headers in `publix_list_scraper.py`:

```python
# Update these headers with your copied values
HEADERS = {
    'akamai-bm-telemetry': 'YOUR_TELEMETRY_HERE',
    'authorization': 'Bearer YOUR_TOKEN_HERE',
    'ecmsid': 'YOUR_ECMS_ID_HERE',
    # ... other headers remain the same
}
```

## 🚀 Data Collection Process

Run the programs in this exact order:

### 1. Collect Purchase Lists
```bash
python publix_list_scraper.py
```
**What it does:**
- Fetches all purchase transactions from Publix API
- Saves raw JSON data to `raw_publix/list-YYYY-MM-DD-HH-MM.json`
- Extracts transaction IDs for detailed collection

### 2. Collect Purchase Details  
```bash
python publix_detail_scraper.py
```
**What it does:**
- Reads transaction IDs from list files
- Fetches detailed receipt data for each transaction
- Saves detailed JSON to `raw_publix/detail-YYYY-MM-DD-HH-MM-<location>.json`
- Includes full receipt text and product information

### 3. Process Data to Database
```bash
python publix_data_processor.py
```
**What it does:**
- Processes raw JSON files into structured YAML format
- Parses receipt text to extract item details, prices, taxes
- Loads all data into `publix_purchases` database table
- Creates individual YAML files: `data/publix/YYYY-MM-DDTHH-MM-SS.yaml`

## 📊 Data Structure

### Raw Data Files
```
raw_publix/
├── list-2025-01-15-10-30.json          # Purchase list data
├── detail-2025-06-25-21-54-Weston.json # Detailed receipt data
└── detail-2025-06-13-18-43-Glade.json  # More detailed receipts
```

### Processed YAML Files
```
data/publix/
├── 2025-06-25T21-54-04.yaml           # Structured purchase data
├── 2025-06-13T18-43-00.yaml           # Individual transactions
└── 2025-05-28T19-32-15.yaml           # Ready for analysis
```

### Database Schema
Single table design: `publix_purchases` with 40+ columns including:
- **Transaction Info**: transaction_number, receipt_id, purchase_date
- **Store Details**: store_name, store_address, store_manager
- **Financial Data**: order_total, sales_tax, grand_total, savings
- **Item Details**: item_name, item_price, item_quantity, upc
- **Payment Info**: payment_method, payment_amount, auth_number
- **Receipt Data**: receipt_text, parsed_items, tax_flags

## 🔍 Sample Data Output

### YAML Structure
```yaml
transaction_number: "1234567890"
receipt_id: "abc123def456"
purchase_date: "2025-06-25"
purchase_time: "21:54:04"
store_name: "Publix Super Market #1234"
store_info:
  name: "Publix Super Market #1234"
  address: "123 Main Street"
  manager: "John Smith"
  phone: "555-123-4567"
order_total: 45.67
sales_tax: 3.21
grand_total: 48.88
products:
  - ItemName: "Organic Bananas"
    ItemQuantity: 2
    UPC: "1234567890123"
    ItemImageUrl: "https://..."
receipt_items:
  - name: "ORGANIC BANANAS"
    price: 3.98
    tax_flag: "F"
    is_voided: false
savings:
  digital_coupon: 1.50
  total_savings: 2.25
```

## 📈 Expected Results

**Typical Collection Results:**
- **Purchase Lists**: 1-2 files per collection run
- **Detail Files**: 10-50+ individual receipt files  
- **YAML Files**: Same number as detail files
- **Database Items**: 200-500+ individual grocery items
- **Time Range**: 6+ months of purchase history

## 🔒 Security Notes

- **Never commit real tokens** - Use placeholders in code
- **Tokens expire** - Re-extract headers when collection fails
- **Rate limiting** - Built-in delays prevent API blocking
- **Data privacy** - Raw files contain personal purchase data

## 🛠️ Troubleshooting

### Authentication Errors
```bash
# Error: 401 Unauthorized
# Solution: Re-extract headers from browser
```

### No Data Found
```bash
# Error: Empty purchase lists
# Solution: Check date ranges and account activity
```

### Database Errors
```bash
# Error: Field too long
# Solution: Database schema auto-adjusts field sizes
```

## 📁 File Organization

```
grocery-genie/
├── publix_list_scraper.py       # Step 1: Collect purchase lists
├── publix_detail_scraper.py     # Step 2: Collect receipt details  
├── publix_data_processor.py     # Step 3: Process to database
├── raw_publix/                  # Raw JSON data storage
├── data/publix/                 # Processed YAML files
└── README_PUBLIX.md            # This documentation
```

## 🎯 Integration

Part of the complete **4-retailer grocery data collection system**:
- ✅ **Costco** - Automated GraphQL API
- ✅ **Walmart** - Manual HTML processing
- ✅ **CVS** - OAuth2 API automation  
- ✅ **Publix** - Bearer token + receipt parsing

All retailers use consistent database design and YAML processing workflows.

## 🔄 Advanced Usage

### Automated Collection

```bash
# Run complete collection pipeline
./collect_publix_data.sh

# Or run individual steps with error handling
python publix_list_scraper.py && \
python publix_detail_scraper.py && \
python publix_data_processor.py
```

### Data Analysis

```python
# Query database for insights
from scripts.grocery_db import GroceryDB

db = GroceryDB()
conn = db.get_connection()

# Get spending by store
cur.execute("""
    SELECT store_name, COUNT(*) as visits, SUM(grand_total) as total_spent
    FROM publix_purchases
    GROUP BY store_name
    ORDER BY total_spent DESC
""")
```

### Reprocessing Data

```bash
# Reprocess existing raw data
python publix_data_processor.py

# Clear database and reload
python -c "
from scripts.grocery_db import GroceryDB
db = GroceryDB()
conn = db.get_connection()
cur = conn.cursor()
cur.execute('DELETE FROM publix_purchases')
conn.commit()
"
python publix_data_processor.py
```

## 💡 Pro Tips

1. **Header Extraction**: Use Chrome DevTools Network tab, filter by "Fetch/XHR"
2. **Token Lifespan**: Publix tokens typically last 24-48 hours
3. **Store Locations**: System automatically detects and saves store information
4. **Receipt Parsing**: Handles complex receipt formats including FSA, coupons, taxes
5. **Error Recovery**: Scripts continue processing even if individual receipts fail
6. **Data Validation**: Automatic verification of parsed vs. API totals

## 📞 Support

For issues with:

- **Authentication**: Re-extract headers from fresh browser session
- **Data Processing**: Check `publix_data_processor.py` logs for parsing errors
- **Database**: Verify PostgreSQL connection and table permissions
- **API Changes**: Update request headers and endpoints as needed

---

## 🎉 Ready to Go

Publix data collection system ready! 🛒✨
