# Costco Grocery Scraper - Streamlined Solution

## 🎯 **Overview**

This streamlined solution consists of just **2 programs**:

1. **`costco_scraper.py`** - Scrapes Costco receipts and saves as YAML files
2. **`yaml_to_database.py`** - Loads YAML files into the database

## 🚀 **Quick Start**

### **Step 1: Get Costco Tokens**

1. Go to **costco.com** and log in
2. Go to **My Account > Orders and Purchases**
3. Click on **"Warehouse"** tab
4. Open browser **Dev Tools (F12) > Network tab**
5. **Refresh the page**
6. Find the **'graphql'** request
7. Copy these values from **Request Headers**:
   - `costco-x-wcs-clientid`: [paste in costco_scraper.py]
   - `costco-x-authorization`: Bearer [paste token in costco_scraper.py]

### **Step 2: Update Tokens**

Edit `costco_scraper.py`:
```python
BEARER_TOKEN = "your_bearer_token_here"
CLIENT_ID = "your_client_id_here"
```

### **Step 3: Run Scraper**

```bash
python costco_scraper.py
```

**Default**: Last 3 months  
**Custom**: Change `months_back=3` to any number

### **Step 4: Load to Database**

```bash
python yaml_to_database.py
```

## 📁 **File Structure**

```
grocery-genie/
├── costco_scraper.py          # Main scraper
├── yaml_to_database.py        # Database loader
├── data/costco/               # YAML files storage
│   ├── 2025-06-13T18-43-00.yaml
│   ├── 2025-06-14T10-22-15.yaml
│   └── processed_files.txt    # Tracking file
└── scripts/
    └── grocery_db.py          # Database module
```

## 🎯 **Features**

### **Costco Scraper**
- ✅ **Complete receipt data** with all fields
- ✅ **Individual YAML files** per receipt
- ✅ **Date-based filenames** (2025-06-13T18-43-00.yaml)
- ✅ **Token validation** with clear instructions
- ✅ **Configurable date range** (default: 3 months)

### **Database Loader**
- ✅ **Batch processing** of all YAML files
- ✅ **Duplicate prevention** with tracking
- ✅ **Enhanced database schema** with all Costco fields
- ✅ **Progress reporting** and error handling

### **Database Schema**
Enhanced `costco_purchases` table includes:
- **Receipt info**: dates, store, receipt numbers
- **Item details**: descriptions, prices, quantities, departments
- **Costco-specific**: membership, warehouse, transaction numbers
- **Fuel data**: quantity, grade, unit prices
- **Payment info**: methods, account numbers
- **Store info**: complete addresses
- **Raw data**: complete YAML for reference

## 🔄 **Workflow**

1. **Run scraper** → Gets receipts → Saves YAML files
2. **Run loader** → Reads YAML files → Inserts to database
3. **Repeat** as needed (tokens expire every 15-30 minutes)

## ⚠️ **Important Notes**

- **Tokens expire** every 15-30 minutes
- **Get fresh tokens** when you see 401 errors
- **YAML files persist** - only need to scrape once
- **Database loader** tracks processed files (no duplicates)
- **Default range**: 3 months (modify as needed)

## 🎉 **Benefits**

- ✅ **No bot detection** (uses real API)
- ✅ **Complete data** (all receipt fields)
- ✅ **Persistent storage** (YAML files)
- ✅ **Flexible processing** (scrape once, load many times)
- ✅ **Clean architecture** (2 focused programs)

## 🔧 **Troubleshooting**

### **Token Expired (401 Error)**
```
❌ AUTHENTICATION FAILED
💡 Your token has expired. Get a fresh one:
```
**Solution**: Follow Step 1 to get new tokens

### **No YAML Files Found**
```
❌ No YAML files found in ./data/costco
💡 Run the Costco scraper first
```
**Solution**: Run `python costco_scraper.py` first

### **Database Connection Error**
```
❌ Database connection failed
```
**Solution**: Check PostgreSQL is running and credentials are correct

## 📊 **Example Output**

### **Scraper Success**
```
🎉 SCRAPING COMPLETED SUCCESSFULLY!
✅ Successfully saved 23 receipts to ./data/costco/
📦 Total items: 287
💡 Next step: Run the database loader
```

### **Database Loader Success**
```
🎉 YAML TO DATABASE IMPORT COMPLETED!
✅ Successful files: 23
📦 Total items imported: 287
💡 Your Costco data is now in the database!
```

## 🎯 **Next Steps**

After successful import, your Costco data is ready for:
- 📊 **Analysis and reporting**
- 🔍 **Querying with SQL**
- 📈 **Spending pattern analysis**
- 🛒 **Shopping history tracking**
