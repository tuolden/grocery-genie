# Grocery Genie Troubleshooting Guide

## 🎯 **Overview**

This guide provides solutions for common issues encountered when running Grocery Genie, including data loading problems, API errors, deployment issues, and database connectivity problems.

---

## 🔍 **Quick Diagnostics**

### **System Health Check**

```bash
# Run comprehensive health check
python src/utils/healthcheck.py

# Verify data loading system
python scripts/verify_data_loaded.py

# Test all data loaders
python scripts/run_manual_data_loaders.py --verify-only

# Check API endpoints
curl http://localhost:8080/health
```

### **Common Status Commands**

```bash
# Check database connectivity
python -c "from src.scripts.grocery_db import GroceryDB; db = GroceryDB(); print('✅ Database connected')"

# Verify file permissions
ls -la data/ raw/ logs/

# Check Python environment
python --version
pip list | grep -E "(psycopg2|requests|beautifulsoup4|pyyaml)"
```

---

## 🗃️ **Database Issues**

### **Connection Errors**

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check database service status
sudo systemctl status postgresql

# Verify connection parameters
echo $DB_HOST $DB_PORT $DB_NAME $DB_USER

# Test direct connection
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME

# Check firewall rules
sudo ufw status
sudo iptables -L | grep 5432
```

**Environment Variables**:
```bash
# Set required variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=grocery_genie
export DB_USER=your_username
export DB_PASSWORD=your_password
```

### **Permission Errors**

**Problem**: `permission denied for table`

**Solutions**:
```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE grocery_genie TO your_username;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- Check current permissions
\dp
\l
```

### **Table Creation Issues**

**Problem**: Tables not created automatically

**Solutions**:
```bash
# Manually create tables
python -c "from src.scripts.grocery_db import GroceryDB; db = GroceryDB(); db.ensure_tables()"

# Check table existence
psql -d grocery_genie -c "\dt"

# View table schemas
psql -d grocery_genie -c "\d costco_purchases"
```

---

## 📁 **Data Loading Issues**

### **Import Errors**

**Problem**: `No module named 'src'`

**Solutions**:
```bash
# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/grocery-genie"

# Run from project root
cd /path/to/grocery-genie
python scripts/run_manual_data_loaders.py

# Check current directory
pwd
ls -la src/
```

### **File Not Found Errors**

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solutions**:
```bash
# Create required directories
mkdir -p data/cvs data/costco data/walmart data/publix data/other
mkdir -p raw/walmart raw/publix
mkdir -p logs

# Check file permissions
chmod 755 data/ raw/ logs/
chmod 644 data/*/*.yaml

# Verify file structure
find data/ -name "*.yaml" | head -5
find raw/ -name "*.html" | head -5
```

### **YAML Parsing Errors**

**Problem**: `yaml.scanner.ScannerError: while scanning`

**Solutions**:
```bash
# Validate YAML files
python -c "import yaml; yaml.safe_load(open('data/costco/file.yaml'))"

# Check file encoding
file data/costco/*.yaml
head -n 5 data/costco/problematic-file.yaml

# Fix encoding issues
iconv -f ISO-8859-1 -t UTF-8 problematic-file.yaml > fixed-file.yaml
```

### **JSON Parsing Errors (Walmart)**

**Problem**: `json.JSONDecodeError: Extra data`

**Solutions**:
```bash
# Check HTML file structure
grep -n "__NEXT_DATA__" raw/walmart/file.html

# Validate JSON extraction
python -c "
from src.loaders.walmart_data_loader import extract_json_from_html
with open('raw/walmart/file.html') as f:
    data = extract_json_from_html(f.read())
    print('✅ JSON extracted successfully' if data else '❌ JSON extraction failed')
"

# Manual JSON validation
python -c "import json; json.loads('{\"test\": \"data\"}')"
```

---

## 🌐 **API Issues**

### **Server Startup Problems**

**Problem**: `Address already in use`

**Solutions**:
```bash
# Find process using port 8080
lsof -i :8080
netstat -tulpn | grep 8080

# Kill existing process
kill -9 <process_id>

# Use different port
export API_PORT=8081
python src/api/receipt_matcher_api.py
```

### **API Response Errors**

**Problem**: `500 Internal Server Error`

**Solutions**:
```bash
# Check API logs
tail -f logs/api.log

# Test with verbose output
curl -v http://localhost:8080/health

# Check database connection from API
python -c "
from src.api.receipt_matcher_api import app
with app.test_client() as client:
    response = client.get('/health')
    print(response.status_code, response.get_json())
"
```

### **CORS Issues**

**Problem**: `Access-Control-Allow-Origin` errors

**Solutions**:
```python
# Add CORS headers to API
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# Or manually add headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
```

---

## ☸️ **Kubernetes/Docker Issues**

### **Container Startup Failures**

**Problem**: Pod in `CrashLoopBackOff` state

**Solutions**:
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>

# Describe pod for events
kubectl describe pod <pod-name> -n <namespace>

# Check resource limits
kubectl top pods -n <namespace>

# Verify image availability
docker pull ghcr.io/tuolden/grocery-genie:latest
```

### **Environment Variable Issues**

**Problem**: Missing or incorrect environment variables

**Solutions**:
```bash
# Check ConfigMap
kubectl get configmap grocery-genie-config -o yaml

# Check Secrets
kubectl get secret grocery-genie-secrets -o yaml

# Verify environment in pod
kubectl exec -it <pod-name> -- env | grep DB_

# Update ConfigMap
kubectl patch configmap grocery-genie-config -p '{"data":{"DB_HOST":"new-host"}}'
```

### **Volume Mount Issues**

**Problem**: Data directories not accessible

**Solutions**:
```bash
# Check PVC status
kubectl get pvc -n <namespace>

# Verify volume mounts
kubectl describe pod <pod-name> | grep -A 10 "Mounts:"

# Check file permissions in container
kubectl exec -it <pod-name> -- ls -la /app/data/

# Fix permissions
kubectl exec -it <pod-name> -- chmod 755 /app/data/
```

---

## ⏰ **CRON Job Issues**

### **Jobs Not Running**

**Problem**: CRON jobs not executing on schedule

**Solutions**:
```bash
# Check CRON job status
kubectl get cronjobs -n <namespace>

# View job history
kubectl get jobs -n <namespace>

# Check CRON job configuration
kubectl describe cronjob <cronjob-name> -n <namespace>

# Manual job execution
kubectl create job --from=cronjob/<cronjob-name> manual-test-job
```

### **Job Failures**

**Problem**: CRON jobs failing with errors

**Solutions**:
```bash
# Check failed job logs
kubectl logs job/<failed-job-name> -n <namespace>

# Verify job configuration
kubectl get cronjob <cronjob-name> -o yaml

# Test job command manually
kubectl run test-pod --image=ghcr.io/tuolden/grocery-genie:latest --rm -it -- python src/loaders/cvs_data_loader.py
```

### **Timezone Issues**

**Problem**: CRON jobs running at wrong times

**Solutions**:
```yaml
# Set timezone in CRON job spec
spec:
  schedule: "30 23 * * *"  # 11:30 PM EST
  timeZone: "America/New_York"
```

```bash
# Verify timezone in container
kubectl exec -it <pod-name> -- date
kubectl exec -it <pod-name> -- cat /etc/timezone
```

---

## 🔧 **Performance Issues**

### **Slow Data Loading**

**Problem**: Data loaders taking too long

**Solutions**:
```bash
# Check database performance
psql -d grocery_genie -c "EXPLAIN ANALYZE SELECT * FROM costco_purchases LIMIT 1000;"

# Monitor resource usage
top
htop
iostat -x 1

# Optimize database
psql -d grocery_genie -c "VACUUM ANALYZE;"
psql -d grocery_genie -c "REINDEX DATABASE grocery_genie;"
```

### **Memory Issues**

**Problem**: Out of memory errors

**Solutions**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Increase container memory limits
kubectl patch deployment <deployment-name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"grocery-genie","resources":{"limits":{"memory":"2Gi"}}}]}}}}'

# Process files in smaller batches
python scripts/run_manual_data_loaders.py --loader cvs --batch-size 50
```

---

## 🚨 **Emergency Procedures**

### **System Recovery**

**Complete System Failure**:
```bash
# 1. Check system health
python src/utils/healthcheck.py

# 2. Restart services
sudo systemctl restart postgresql
docker-compose restart

# 3. Verify data integrity
python scripts/verify_data_loaded.py --detailed

# 4. Re-run failed jobs
python scripts/run_manual_data_loaders.py
```

### **Data Corruption Recovery**

**Database Issues**:
```sql
-- Check for corruption
SELECT * FROM pg_stat_database WHERE datname = 'grocery_genie';

-- Backup current data
pg_dump grocery_genie > backup_$(date +%Y%m%d_%H%M%S).sql

-- Restore from backup if needed
psql grocery_genie < backup_20250713_120000.sql
```

### **Rollback Procedures**

**Deployment Rollback**:
```bash
# Kubernetes rollback
kubectl rollout undo deployment/grocery-genie-staging -n staging

# ArgoCD rollback
argocd app rollback grocery-genie-staging <previous-revision>

# Docker rollback
docker-compose down
docker-compose up -d --force-recreate
```

---

## 📞 **Getting Help**

### **Log Collection**

```bash
# Collect all relevant logs
mkdir troubleshooting-logs
cp logs/*.log troubleshooting-logs/
kubectl logs deployment/grocery-genie-staging -n staging > troubleshooting-logs/k8s-staging.log
kubectl logs deployment/grocery-genie-production -n production > troubleshooting-logs/k8s-production.log

# System information
uname -a > troubleshooting-logs/system-info.txt
docker version >> troubleshooting-logs/system-info.txt
kubectl version >> troubleshooting-logs/system-info.txt
```

### **Support Channels**

- **GitHub Issues**: [Create Issue](https://github.com/tuolden/grocery-genie/issues/new)
- **Documentation**: [Project Overview](PROJECT_OVERVIEW.md)
- **Email**: tuolden@gmail.com

### **Issue Template**

When reporting issues, include:
1. **Environment**: Local/Staging/Production
2. **Error Message**: Complete error output
3. **Steps to Reproduce**: Exact commands used
4. **System Info**: OS, Python version, Docker version
5. **Logs**: Relevant log files
6. **Configuration**: Environment variables (redacted)

---

**This troubleshooting guide covers the most common issues. For complex problems, don't hesitate to reach out for support!**
