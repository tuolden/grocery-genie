# Grocery Genie - Complete Project Documentation

## 🎯 **Project Overview**

**Grocery Genie** is a comprehensive multi-retailer grocery data collection and processing system that automatically gathers purchase data from 5 major retailers (Costco, Walmart, CVS, Publix, and other stores), processes it into structured YAML files, and loads it into a PostgreSQL database for analysis and tracking.

**Key Purpose**: Automate grocery purchase data collection, standardize data across retailers, and provide a unified database for grocery spending analysis and inventory tracking.

---

## 🚀 **How to Run the Program**

### **Prerequisites**
- **Python 3.11+** (recommended)
- **PostgreSQL 13+** database
- **Docker** (for containerized deployment)
- **Git** for version control
- **K3s cluster** (for production deployment)

### **Required Environment Variables**
Create a `.env` file in the project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grocery_genie
DB_USER=your_username
DB_PASSWORD=your_password

# Environment
ENV=local  # Options: local, staging, production

# Optional: API Configuration
API_PORT=8080
```

### **Installation & Setup**

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

3. **Set up database:**
```bash
# Create PostgreSQL database
createdb grocery_genie

# Initialize database tables (automatic on first run)
python src/scripts/grocery_db.py
```

### **Start Commands**

#### **Manual Data Loading (Recommended for Testing)**
```bash
# Run all data loaders
python scripts/run_manual_data_loaders.py

# Run specific retailer loader
python scripts/run_manual_data_loaders.py --loader cvs
python scripts/run_manual_data_loaders.py --loader costco
python scripts/run_manual_data_loaders.py --loader walmart
python scripts/run_manual_data_loaders.py --loader publix
python scripts/run_manual_data_loaders.py --loader other

# Verify data loading
python scripts/verify_data_loaded.py
```

#### **Individual Scrapers (Data Collection)**
```bash
# Costco scraper (requires manual token setup)
python src/scrapers/costco_scraper.py

# CVS scraper (requires authentication headers)
python src/scrapers/cvs_scraper.py

# Publix scraper (requires authentication headers)
python src/scrapers/publix_list_scraper.py
python src/scrapers/publix_detail_scraper.py
```

#### **API Server (Optional)**
```bash
# Start receipt matcher API
python src/api/receipt_matcher_api.py
# Server runs on http://localhost:8080
```

#### **Docker Deployment**
```bash
# Build container
docker build -t grocery-genie .

# Run container
docker run -d \
  --name grocery-genie \
  -p 8080:8080 \
  -e DB_HOST=your_db_host \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  grocery-genie
```

---

## 🧪 **How to Test the Program**

### **Unit Tests**
```bash
# Run all unit tests
python -m pytest tests/ -v

# Run specific test files
python tests/test_receipt_matcher_unit.py
python tests/test_other_purchases_loader.py
```

### **Integration Tests**
```bash
# Run integration test suite
python tests/run_all_tests.py

# Test database connectivity
python src/utils/healthcheck.py
```

### **Smoke Tests**
```bash
# Run all smoke tests
python tests/smoke/run_all_smoke_tests.py

# Run staging smoke test
python tests/run_staging_smoke_test.py

# Individual smoke tests
python tests/smoke/test_simple_staging_smoke.py
python tests/smoke/test_receipt_matcher_smoke.py
```

### **Manual Testing**
```bash
# Test data loading system
python scripts/run_manual_data_loaders.py --verify-only

# Test with sample data
python scripts/run_manual_data_loaders.py --loader other
```

### **Sample Test Data**
- **Location**: `./test_data/` and `./data/` directories
- **Format**: YAML files with standardized grocery purchase structure
- **Sample Files**: 
  - `data/other/2025-07-10T14-30-00.yaml` (sample grocery purchase)
  - `data/costco/2025-06-13T18-43-00.yaml` (Costco receipt)

---

## 🌐 **Deployment Info**

### **Production Environment**
- **Platform**: K3s Kubernetes cluster
- **Staging URL**: `https://staging.api.grocery-genie.com`
- **Production URL**: `https://api.grocery-genie.com`
- **Container Registry**: `ghcr.io/tuolden/grocery-genie`

### **API Endpoints**

**Base URL**: `https://api.grocery-genie.com`

```
GET  /health              - Health check endpoint
POST /match               - Trigger receipt matching
GET  /status              - Get last run status
GET  /api/receipts        - List recent receipts (if implemented)
```

### **CRON Jobs (Automated Data Loading)**

**Schedule**: Daily at 11:30-11:50 PM EST (5-minute intervals)

```
11:30 PM - CVS Data Loader       (src/loaders/cvs_data_loader.py)
11:35 PM - Costco Data Loader    (src/loaders/yaml_to_database.py)
11:40 PM - Walmart Data Loader   (src/loaders/walmart_data_loader.py)
11:45 PM - Publix Data Loader    (src/loaders/publix_data_processor.py)
11:50 PM - Other Data Loader     (src/loaders/other_purchases_loader.py)
```

**Manual Run Commands**:
```bash
# Run all CRON jobs manually
python scripts/run_manual_data_loaders.py

# Run specific CRON job
python src/loaders/cvs_data_loader.py
python src/loaders/yaml_to_database.py
```

---

## ❤️‍🩹 **Health Monitoring**

### **Health Check Endpoint**
- **URL**: `GET /health`
- **Response**: `200 OK` with JSON status
- **Checks**: Database connectivity, file system access, container health

### **Container Health Check**
```bash
# Docker health check (runs every 30 seconds)
python src/utils/healthcheck.py
```

### **Manual Health Validation**
```bash
# Verify system is functional
python scripts/verify_data_loaded.py

# Check database connectivity
python -c "from src.scripts.grocery_db import GroceryDB; db = GroceryDB(); print('✅ Database connected')"

# Check API availability (if running)
curl -f http://localhost:8080/health || echo "❌ API not responding"
```

### **Monitoring Commands**
```bash
# Check CRON job status
kubectl logs -n production deployment/grocery-genie-cronjob-cvs
kubectl logs -n staging deployment/grocery-genie-cronjob-costco

# View recent data loading activity
python scripts/verify_data_loaded.py --detailed
```

---

## 📚 **Complete Documentation Index**

### **📖 Core Documentation**
- **[📋 Project Overview](PROJECT_OVERVIEW.md)** - This document (complete system overview)
- **[🗃️ Database Schema](DATABASE_SCHEMA.md)** - Database structure and relationships
- **[⚙️ ArgoCD CRON Jobs](README_ARGOCD_CRONJOBS.md)** - Automated data loading system
- **[🧪 Manual Testing Guide](README_MANUAL_TESTING.md)** - Testing procedures and validation

### **🔧 Technical Documentation**
- **[🌐 API Documentation](API_DOCUMENTATION.md)** - REST API endpoints and usage
- **[🚀 Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment procedures
- **[🔧 Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

### **🏗️ Infrastructure Documentation**
- **[🐳 Docker Configuration](../Dockerfile)** - Container definition and setup
- **[☸️ Kubernetes Manifests](../kubernetes/)** - Staging and production deployments
- **[🔄 CI/CD Pipeline](../.github/workflows/)** - Automated testing and deployment

### **📊 Data Collection Guides**
- **[🏪 Costco Scraping](../README_COSTCO.md)** - Costco API token setup and usage
- **[🛒 Walmart Collection](../README_WALMART.md)** - Manual HTML collection workflow
- **[💊 CVS Scraping](../src/scrapers/cvs_scraper.py)** - CVS API authentication
- **[🥬 Publix Collection](../src/scrapers/publix_list_scraper.py)** - Publix XHR requests

---

## 📞 **Support and Resources**

### **Getting Help**
- **GitHub Issues**: [Report Issues](https://github.com/tuolden/grocery-genie/issues)
- **Documentation**: Complete guides available in `/docs/` directory
- **Email Support**: tuolden@gmail.com

### **Community Resources**
- **Repository**: [GitHub - grocery-genie](https://github.com/tuolden/grocery-genie)
- **Releases**: [Latest Releases](https://github.com/tuolden/grocery-genie/releases)
- **CI/CD Status**: [GitHub Actions](https://github.com/tuolden/grocery-genie/actions)

---

**🎉 This comprehensive documentation ensures both humans and AI agents can effectively understand, deploy, and maintain the Grocery Genie system!**
