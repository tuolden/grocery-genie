# Manual Testing for ArgoCD CRON Jobs

## 🎯 **Overview**

This document provides comprehensive instructions for manually testing the ArgoCD CRON job data loading system without waiting for the scheduled execution times (11:30-11:50 PM EST).

## 📁 **Manual Testing Scripts**

### **1. Manual Data Loaders Runner**
**File**: `scripts/run_manual_data_loaders.py`

Runs all data loaders manually to simulate the exact CRON job functionality.

### **2. Data Verification Script**
**File**: `scripts/verify_data_loaded.py`

Verifies that data has been properly loaded into all database tables.

## 🚀 **Quick Start - Run All Tests**

### **Basic Test (All Loaders)**
```bash
# Run all data loaders and verify results
python scripts/run_manual_data_loaders.py

# Verify data was loaded correctly
python scripts/verify_data_loaded.py --detailed
```

### **Environment-Specific Testing**
```bash
# Test staging environment
python scripts/run_manual_data_loaders.py --staging
python scripts/verify_data_loaded.py --staging --detailed

# Test production environment
python scripts/run_manual_data_loaders.py --production
python scripts/verify_data_loaded.py --production --detailed
```

## 🔧 **Detailed Usage**

### **Manual Data Loaders Runner**

#### **Run All Loaders**
```bash
# Basic execution
python scripts/run_manual_data_loaders.py

# With verbose logging
python scripts/run_manual_data_loaders.py --verbose

# Staging environment
python scripts/run_manual_data_loaders.py --staging --verbose
```

#### **Run Specific Loader**
```bash
# CVS only
python scripts/run_manual_data_loaders.py --loader cvs

# Costco only
python scripts/run_manual_data_loaders.py --loader costco

# Walmart only
python scripts/run_manual_data_loaders.py --loader walmart

# Publix only
python scripts/run_manual_data_loaders.py --loader publix

# Other purchases only
python scripts/run_manual_data_loaders.py --loader other
```

#### **Verification Only**
```bash
# Only verify data, don't run loaders
python scripts/run_manual_data_loaders.py --verify-only

# Verify with environment
python scripts/run_manual_data_loaders.py --verify-only --staging
```

### **Data Verification Script**

#### **Basic Verification**
```bash
# Simple verification
python scripts/verify_data_loaded.py

# Detailed statistics
python scripts/verify_data_loaded.py --detailed

# Recent data only (last 30 days)
python scripts/verify_data_loaded.py --recent
```

#### **Export Results**
```bash
# Export verification results to JSON
python scripts/verify_data_loaded.py --export --detailed

# Export staging results
python scripts/verify_data_loaded.py --staging --export --detailed
```

## 📊 **Expected Output**

### **Successful Run Example**
```
🚀 MANUAL DATA LOADERS TEST RUNNER
============================================================
🌍 Environment: local
📅 Started: 2025-07-13 15:45:00

🔄 RUNNING ALL DATA LOADERS
============================================================

⏰ Starting CVS loader...
🏪 CVS DATA LOADER
------------------------------------------
🔧 Creating database tables...
📄 Found 5 YAML files
✅ Processed 5 files successfully
✅ CVS loader completed
⏱️  CVS loader took 2.34 seconds

⏰ Starting Costco loader...
🏪 COSTCO DATA LOADER
------------------------------------------
📄 Found 12 YAML files
✅ Inserted 45 items from 2025-06-13T18-43-00.yaml
✅ Costco loader completed
⏱️  Costco loader took 3.21 seconds

[... similar output for Walmart, Publix, Other ...]

🔍 VERIFYING DATA LOADED
------------------------------------------
✅ CVS     :     25 records
✅ Costco  :     45 records
✅ Walmart :     18 records
✅ Publix  :     32 records
✅ Other   :     12 records
------------------------------------------
📊 TOTAL RECORDS: 132

🎉 MANUAL DATA LOADERS TEST SUMMARY
============================================================
📊 LOADER RESULTS:
   CVS     : ✅ SUCCESS (2.34s)
   Costco  : ✅ SUCCESS (3.21s)
   Walmart : ✅ SUCCESS (1.87s)
   Publix  : ✅ SUCCESS (4.12s)
   Other   : ✅ SUCCESS (0.95s)

🔍 DATA VERIFICATION:
   CVS     : ✅ 25 records
   Costco  : ✅ 45 records
   Walmart : ✅ 18 records
   Publix  : ✅ 32 records
   Other   : ✅ 12 records

📈 OVERALL RESULTS:
   ✅ Successful loaders: 5/5
   📊 Total records: 132

🎉 ALL TESTS PASSED! Data loading system is working correctly.
```

### **Detailed Verification Example**
```
🔍 DATA VERIFICATION SCRIPT
==================================================
🌍 Environment: local
📅 Verification Time: 2025-07-13 15:50:00
📅 Scope: All data

📊 VERIFYING ALL TABLES
--------------------------------------------------
🔍 Checking CVS...
   ✅ 25 total records
   📅 5 recent records (30 days)
   🛒 18 unique items
   📅 Date range: 2025-06-01 to 2025-07-10

🔍 Checking Costco...
   ✅ 45 total records
   📅 12 recent records (30 days)
   🛒 32 unique items
   📅 Date range: 2025-05-15 to 2025-07-12

[... similar for other retailers ...]

🕐 CHECKING DATA FRESHNESS
--------------------------------------------------
   CVS            : 2025-07-10 (🟡 3 days ago)
   Costco         : 2025-07-12 (🟢 Today)
   Walmart        : 2025-07-08 (🟡 5 days ago)
   Publix         : 2025-07-11 (🟡 2 days ago)
   Other Purchases: 2025-07-09 (🟡 4 days ago)

🎯 VERIFICATION SUMMARY
==================================================
📊 OVERALL RESULTS:
   ✅ Successful tables: 5/5
   📦 Total records: 132
   🟢 Working tables: 5
   🟡 Empty tables: 0
   🔴 Error tables: 0

🕐 DATA FRESHNESS:
   📅 Tables with recent data (≤7 days): 5/5

🎉 VERIFICATION PASSED: All tables have data!
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Missing Data Directories**
```
❌ CVS data directory not found: data/cvs
```
**Solution**: Ensure data directories exist and contain YAML files:
```bash
ls -la data/cvs/
ls -la data/costco/
ls -la data/walmart/
ls -la data/publix/
ls -la data/other/
```

#### **2. Database Connection Errors**
```
❌ Database connection failed: connection refused
```
**Solution**: Check database configuration and ensure database is running.

#### **3. Import Errors**
```
❌ CVS loader failed: No module named 'loaders.cvs_data_loader'
```
**Solution**: Run from project root directory:
```bash
cd /path/to/grocery-genie
python scripts/run_manual_data_loaders.py
```

### **Debug Mode**
```bash
# Enable verbose logging for detailed error information
python scripts/run_manual_data_loaders.py --verbose

# Check specific loader
python scripts/run_manual_data_loaders.py --loader cvs --verbose
```

## 📋 **Pre-Test Checklist**

### **Before Running Tests**
- [ ] Ensure you're in the project root directory
- [ ] Database is running and accessible
- [ ] Data directories exist with YAML files:
  - [ ] `data/cvs/` has CVS YAML files
  - [ ] `data/costco/` has Costco YAML files
  - [ ] `data/walmart/` has Walmart YAML files (or `raw/walmart/` has HTML files)
  - [ ] `data/publix/` has Publix YAML files (or `raw/publix/` has JSON files)
  - [ ] `data/other/` has other purchase YAML files
- [ ] Python dependencies are installed
- [ ] Database tables are created (scripts will create them if needed)

### **Environment Variables**
For staging/production testing, ensure these are set:
```bash
# Staging
export ENV=staging
export DB_HOST=staging-db-host
export DB_NAME=grocery_genie_staging

# Production
export ENV=production
export DB_HOST=production-db-host
export DB_NAME=grocery_genie_production
```

## 🎯 **Test Scenarios**

### **1. Full System Test**
```bash
# Test complete data loading pipeline
python scripts/run_manual_data_loaders.py --verbose
python scripts/verify_data_loaded.py --detailed --export
```

### **2. Individual Retailer Tests**
```bash
# Test each retailer separately
for retailer in cvs costco walmart publix other; do
    echo "Testing $retailer..."
    python scripts/run_manual_data_loaders.py --loader $retailer --verbose
done
```

### **3. Environment Validation**
```bash
# Test staging environment
python scripts/run_manual_data_loaders.py --staging
python scripts/verify_data_loaded.py --staging --detailed

# Test production environment (be careful!)
python scripts/run_manual_data_loaders.py --production
python scripts/verify_data_loaded.py --production --detailed
```

### **4. Data Freshness Check**
```bash
# Check how recent the data is
python scripts/verify_data_loaded.py --recent --detailed
```

## 📈 **Success Criteria**

### **All Tests Pass When:**
- ✅ All 5 loaders complete successfully
- ✅ All 5 database tables have records
- ✅ No error messages in output
- ✅ Data verification shows expected record counts
- ✅ Data freshness is reasonable (within expected timeframe)

### **Partial Success When:**
- ⚠️ Some loaders work, others fail (check data availability)
- ⚠️ Some tables have data, others are empty
- ⚠️ Data is older than expected (check data collection)

### **Failure When:**
- ❌ All loaders fail
- ❌ No data in any tables
- ❌ Database connection errors
- ❌ Import/module errors

## 🔄 **Integration with CRON Jobs**

These manual tests simulate the exact same processes that run automatically via CRON jobs:

- **11:30 PM EST**: CVS Data Loader → `python scripts/run_manual_data_loaders.py --loader cvs`
- **11:35 PM EST**: Costco Data Loader → `python scripts/run_manual_data_loaders.py --loader costco`
- **11:40 PM EST**: Walmart Data Loader → `python scripts/run_manual_data_loaders.py --loader walmart`
- **11:45 PM EST**: Publix Data Loader → `python scripts/run_manual_data_loaders.py --loader publix`
- **11:50 PM EST**: Other Purchases Loader → `python scripts/run_manual_data_loaders.py --loader other`

**Manual testing validates that the CRON job system will work correctly when deployed.**
