# Grocery Genie - Multi-Retailer Grocery Data Collector

A comprehensive grocery data collection system that gathers purchase data from multiple retailers (Costco, Walmart, Publix) and stores it in a PostgreSQL database. Deployed on K3s with staging and production environments.

🚀 **CI/CD Pipeline Status: TESTING PYPROJECT.TOML FIX** - Code quality checks should now pass with fixed ruff configuration! (Build #34)

[![CI/CD Pipeline](https://github.com/tuolden/grocery-genie/actions/workflows/build-and-deploy.yml/badge.svg)](https://github.com/tuolden/grocery-genie/actions/workflows/build-and-deploy.yml)

## 🎯 **Overview**

This project supports multiple retailers with different collection methods:

### **Costco (Automated)**

- **`costco_scraper.py`** - Scrapes receipts using official Costco API
- **`yaml_to_database.py`** - Loads YAML receipt files into database

### **Walmart (Manual Collection)**

- **Manual HTML collection** - Save order pages from browser
- **`walmart_data_loader.py`** - Processes HTML files and loads to database

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- PostgreSQL database
- Costco account

### **Installation**

1. **Clone the repository:**
```bash
git clone https://github.com/tuolden/grocery-genie.git
cd grocery-genie
```

2. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL database credentials
```

### **Usage**

#### **Costco (Automated)**

See **[README_COSTCO.md](README_COSTCO.md)** for complete instructions.

**Quick workflow:**

1. Get Costco API tokens from browser dev tools
2. Update tokens in `costco_scraper.py`
3. Run scraper: `python costco_scraper.py`
4. Load to database: `python yaml_to_database.py`

#### **Walmart (Manual Collection)**

See **[README_WALMART.md](README_WALMART.md)** for complete instructions.

**Quick workflow:**

1. **Manual Collection:** Log into Walmart.com and navigate to your orders
2. **Save Order List Pages:** Save HTML from orders list pages to `raw/walmart/`
3. **Save Order Detail Pages:** Click each order → save detail page HTML to `raw/walmart/`
4. **Process Data:** Run `python walmart_data_loader.py`

## 📁 **Project Structure**

```text
grocery-genie/
├── README.md                  # This file
├── README_COSTCO.md          # Detailed Costco scraper instructions
├── README_WALMART.md         # Detailed Walmart collection instructions
├── README_STAGING.md         # Staging environment documentation
├── costco_scraper.py         # Main Costco scraper
├── walmart_data_loader.py    # Walmart data processor
├── yaml_to_database.py       # Database loader
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image definition
├── healthcheck.py            # Container health check script
├── tests/                    # Test suite
│   └── smoke/               # Smoke tests for system validation
├── data/
│   ├── costco/              # Costco YAML files storage
│   └── walmart/             # Walmart YAML files storage
├── raw/
│   └── walmart/             # Raw Walmart HTML files
├── kubernetes/               # K3s deployment manifests
│   ├── staging/             # Staging environment
│   ├── production/          # Production environment
│   └── argocd-*.yaml       # ArgoCD applications
└── scripts/
    ├── __init__.py
    └── grocery_db.py        # Database module
```

## 🎯 **Features**

- ✅ **Official Costco API** - No bot detection issues
- ✅ **Complete receipt data** - All fields including fuel, payments, taxes
- ✅ **YAML file storage** - Individual files per receipt
- ✅ **Enhanced database** - 25+ fields per item
- ✅ **Duplicate prevention** - Smart tracking of processed files
- ✅ **Token management** - Clear instructions for token refresh
- ✅ **K3s Deployment** - Staging and production environments
- ✅ **GitOps CI/CD** - ArgoCD-based deployments
- ✅ **Smoke Testing** - Automated staging validation

## 🚀 **Deployment**

### **Staging and Production Environments**

This project supports separate staging and production environments on K3s:

- **Staging**: `staging.api.grocery-genie.com` - Safe testing environment
- **Production**: `api.grocery-genie.com` - Live production environment

See **[README_STAGING.md](README_STAGING.md)** for complete deployment instructions.

### **CI/CD Pipeline**

1. **Push to main** → Deploy to staging → Run smoke tests
2. **Create release** → Deploy to production (after staging validation)
3. **ArgoCD** automatically syncs Kubernetes manifests
4. **GitHub Actions** handles build, test, and deployment orchestration

## 🗄️ **Database Schema**

### **Costco Purchases Table**

Enhanced `costco_purchases` table includes:

- Receipt information (dates, store, receipt numbers)
- Item details (descriptions, prices, quantities, departments)
- Costco-specific fields (membership, warehouse, transaction numbers)
- Fuel data (quantity, grade, unit prices)
- Payment information (methods, account numbers)
- Store information (complete addresses)
- Raw YAML data for complete reference

### **Walmart Purchases Table**

Comprehensive `walmart_purchases` table includes:

- Order information (order ID, dates, fulfillment type)
- Item details (names, prices, quantities, brands)
- Store information (ID, name, address)
- Payment and shipping details
- Raw JSON data for complete reference

## ⚠️ **Important Notes**

- **API tokens expire** every 15-30 minutes
- **No web scraping** - uses official Costco GraphQL API
- **YAML files persist** - only need to scrape once per period
- **Database loader** prevents duplicates automatically

## 🔧 **Configuration**

Create `.env` file with your database credentials:

```env
# PostgreSQL Database
DATABASE_URL=postgresql://user:password@localhost:5432/grocery_genie
```

## 📖 **Documentation**

- **[README_COSTCO.md](README_COSTCO.md)** - Complete Costco scraper guide
- **Token setup instructions** - Built into the scraper
- **Database schema** - Documented in grocery_db.py

## 🎉 **Benefits**

- **No bot detection** - Uses real Costco API
- **Complete data** - All receipt fields captured
- **Reliable** - No web scraping brittleness
- **Fast** - Direct API calls
- **Organized** - Clean file structure and workflow

## 📊 **Example Output**

After successful data collection and database loading:

**Costco:**

- Individual YAML files: `./data/costco/2025-06-13T18-43-00.yaml`
- Database records: Complete purchase history with all details
- Progress tracking: Automatic duplicate prevention

**Walmart:**

- Individual YAML files: `./data/walmart/2023-04-02T19-03-09.yaml`
- Database records: 503 items loaded from 20 orders
- Manual collection workflow with automated processing

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License.
