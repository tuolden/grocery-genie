# 🛒 Grocery Genie

**A comprehensive multi-retailer grocery data collection and processing system with automated daily data loading, receipt matching, and unified database storage.**

[![CI/CD Pipeline](https://github.com/tuolden/grocery-genie/actions/workflows/ci.yml/badge.svg)](https://github.com/tuolden/grocery-genie/actions)
[![Code Quality](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🎯 **What is Grocery Genie?**

Grocery Genie automatically collects, processes, and analyzes grocery purchase data from **5 major retailers**:
- 🏪 **Costco** - Warehouse receipts via GraphQL API
- 🛒 **Walmart** - Order history via HTML parsing
- 💊 **CVS** - Purchase data via REST API
- 🥬 **Publix** - Transaction data via XHR requests
- 📦 **Other Stores** - Manual receipt entry system

**Key Benefits:**
- 📊 **Unified Data**: Standardized format across all retailers
- 🤖 **Automated Processing**: Daily CRON jobs load data automatically
- 🔍 **Receipt Matching**: AI-powered analysis and categorization
- 📈 **Spending Analysis**: Track grocery expenses across all stores
- 🚀 **Production Ready**: K3s deployment with ArgoCD GitOps

---

## 🚀 **Quick Start**

### **1. Prerequisites**
```bash
# Required software
- Python 3.11+
- PostgreSQL 13+
- Docker (optional)
- Git
```

### **2. Installation**
```bash
# Clone repository
git clone https://github.com/tuolden/grocery-genie.git
cd grocery-genie

# Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials
```

### **3. Database Setup**
```bash
# Create PostgreSQL database
createdb grocery_genie

# Tables are created automatically on first run
```

### **4. Run the System**
```bash
# Test all data loaders
python scripts/run_manual_data_loaders.py

# Verify data loading
python scripts/verify_data_loaded.py

# Start API server (optional)
python src/api/receipt_matcher_api.py
```

---

## 📚 **Complete Documentation**

### **📖 Core Documentation**
- **[📋 Project Overview](docs/PROJECT_OVERVIEW.md)** - Complete system documentation
- **[🗃️ Database Schema](docs/DATABASE_SCHEMA.md)** - Database structure and relationships
- **[⚙️ ArgoCD CRON Jobs](docs/README_ARGOCD_CRONJOBS.md)** - Automated data loading system
- **[🧪 Manual Testing Guide](docs/README_MANUAL_TESTING.md)** - Testing procedures and validation

### **🔧 Technical Documentation**
- **[🌐 API Documentation](docs/API_DOCUMENTATION.md)** - REST API endpoints and usage
- **[🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment procedures
- **[🔧 Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[🏗️ Staging Environment](docs/README_STAGING.md)** - Staging deployment guide

### **📊 Data Collection Guides**
- **[🏪 Costco Scraping](docs/README_COSTCO.md)** - Costco API token setup and usage
- **[💊 CVS Scraping](docs/README_CVS.md)** - CVS API authentication and data collection
- **[🥬 Publix Collection](docs/README_PUBLIX.md)** - Publix XHR requests and data processing
- **[📦 Other Purchases](docs/README_OTHER_PURCHASES.md)** - Manual receipt entry system
- **[🔍 Receipt Matcher](docs/README_RECEIPT_MATCHER.md)** - AI-powered receipt analysis

### **🏗️ Infrastructure Guides**
- **[🐳 Docker Deployment](Dockerfile)** - Container configuration
- **[☸️ Kubernetes Manifests](kubernetes/)** - Staging and production deployments
- **[🔄 CI/CD Pipeline](.github/workflows/)** - Automated testing and deployment

---

## 🏗️ **System Architecture**

### **� Data Flow**
1. **Collection**: Scrapers gather data from retailer websites/APIs
2. **Processing**: Raw data converted to standardized YAML format
3. **Loading**: YAML files loaded into PostgreSQL database tables
4. **Analysis**: API endpoints provide receipt matching and analysis
5. **Automation**: Daily CRON jobs (11:30-11:50 PM EST) process new data

### **📁 Project Structure**
```
grocery-genie/
├── 📄 README.md                    # Main documentation
├── 📁 docs/                       # Complete documentation
│   ├── PROJECT_OVERVIEW.md        # Complete system overview
│   ├── API_DOCUMENTATION.md       # REST API endpoints
│   ├── DATABASE_SCHEMA.md          # Database structure
│   ├── DEPLOYMENT_GUIDE.md         # Production deployment
│   ├── TROUBLESHOOTING.md          # Common issues & solutions
│   ├── README_ARGOCD_CRONJOBS.md   # CRON jobs system
│   ├── README_MANUAL_TESTING.md    # Testing procedures
│   ├── README_STAGING.md           # Staging environment
│   ├── README_COSTCO.md            # Costco scraping guide
│   ├── README_CVS.md               # CVS data collection
│   ├── README_PUBLIX.md            # Publix data processing
│   ├── README_OTHER_PURCHASES.md   # Manual receipt entry
│   └── README_RECEIPT_MATCHER.md   # AI receipt analysis
├── 📁 src/                        # Source code
│   ├── api/                       # API endpoints
│   ├── scrapers/                  # Data collection scripts
│   ├── loaders/                   # Database loading scripts
│   ├── scripts/                   # Utility scripts
│   └── utils/                     # Helper utilities
├── 📁 scripts/                    # Manual testing scripts
│   ├── run_manual_data_loaders.py # Test all loaders
│   └── verify_data_loaded.py      # Verify data loading
├── 📁 data/                       # YAML data storage
│   ├── cvs/                       # CVS purchase data
│   ├── costco/                    # Costco receipt data
│   ├── walmart/                   # Walmart order data
│   ├── publix/                    # Publix transaction data
│   └── other/                     # Other store purchases
├── 📁 raw/                        # Raw data files
│   ├── walmart/                   # Walmart HTML files
│   └── publix/                    # Publix JSON files
├── 📁 kubernetes/                 # K3s deployment
│   ├── staging/                   # Staging environment
│   └── production/                # Production environment
├── 📁 tests/                      # Test suite
│   ├── smoke/                     # Smoke tests
│   └── unit/                      # Unit tests
├── 🐳 Dockerfile                  # Container definition
└── ⚙️ requirements.txt            # Python dependencies
```

---

## 🎯 **Key Features**

### **🤖 Automated Data Collection**
- **Daily CRON Jobs**: Automatic data loading at 11:30-11:50 PM EST
- **5-Minute Intervals**: Staggered processing to avoid resource conflicts
- **Error Handling**: Robust parsing with comprehensive logging
- **Environment Separation**: Staging and production isolation

### **📊 Data Standardization**
- **Unified YAML Format**: Consistent structure across all retailers
- **Database Schema**: Optimized PostgreSQL tables with proper indexing
- **Data Validation**: Type checking and constraint enforcement
- **Upsert Logic**: Prevents duplicates, safe to run multiple times

### **🔍 Receipt Matching & Analysis**
- **AI-Powered Matching**: Intelligent receipt categorization
- **REST API**: `/match` endpoint for receipt processing
- **Health Monitoring**: `/health` endpoint for system status
- **Real-time Processing**: Immediate analysis of uploaded receipts

### **🚀 Production Deployment**
- **K3s Kubernetes**: Production-ready container orchestration
- **ArgoCD GitOps**: Automated deployment from Git repository
- **Environment Management**: Separate staging and production configs
- **Health Checks**: Container and application-level monitoring

---

## � **Current System Status**

### **📊 Data Processing Results**
```
✅ CVS     : 1,092+ records processed
✅ Costco  : 3,169+ records processed
✅ Walmart : 2,180+ records processed
✅ Publix  : 1,827+ records processed
✅ Other   : 14+ records processed

📦 Total: 8,282+ grocery purchase records
🎯 Success Rate: 100% (5/5 loaders working)
```

### **🔧 System Health**
- ✅ **All Data Loaders**: Working perfectly
- ✅ **Database**: Connected and optimized
- ✅ **API Endpoints**: Responding correctly
- ✅ **CRON Jobs**: Scheduled and ready
- ✅ **Code Quality**: All Ruff checks pass

---

## 🧪 **Testing**

### **Quick Test Commands**
```bash
# Run all tests
python -m pytest tests/ -v

# Test data loading
python scripts/run_manual_data_loaders.py --verify-only

# Test API endpoints
curl http://localhost:8080/health

# Run smoke tests
python tests/smoke/run_all_smoke_tests.py
```

### **Manual Testing**
```bash
# Test individual retailers
python scripts/run_manual_data_loaders.py --loader cvs
python scripts/run_manual_data_loaders.py --loader costco

# Verify results
python scripts/verify_data_loaded.py --detailed
```

---

## 🌐 **Deployment**

### **Production Environment**
- **Staging**: `https://staging.api.grocery-genie.com`
- **Production**: `https://api.grocery-genie.com`
- **Container Registry**: `ghcr.io/tuolden/grocery-genie`

### **Docker Deployment**
```bash
# Build and run
docker build -t grocery-genie .
docker run -d -p 8080:8080 grocery-genie
```

### **Kubernetes Deployment**
```bash
# Deploy to staging
kubectl apply -f kubernetes/staging/

# Deploy to production
kubectl apply -f kubernetes/production/
```

---

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Run tests**: `python -m pytest tests/`
4. **Check code quality**: `ruff check && ruff format --check`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/tuolden/grocery-genie/issues)
- **Documentation**: [Project Overview](docs/PROJECT_OVERVIEW.md)
- **Email**: tuolden@gmail.com

---

**🎉 Grocery Genie - Making grocery data collection and analysis effortless!**
