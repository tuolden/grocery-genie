# ArgoCD CRON Jobs for Grocery Genie Data Loading

## 🎯 **Overview**

This document describes the ArgoCD-managed CRON job system that automatically loads grocery data from `./data/` directories into staging and production databases daily at 11:30 PM EST.

## 🏗️ **Architecture**

### **ArgoCD Applications**
- **Staging**: `grocery-genie-staging` → `kubernetes/staging/`
- **Production**: `grocery-genie-production` → `kubernetes/production/`

### **CRON Job Schedule (EST)**
```
11:30 PM - CVS Data Loader
11:35 PM - Costco Data Loader  
11:40 PM - Walmart Data Loader
11:45 PM - Publix Data Loader
11:50 PM - Other Purchases Loader
```

## 📁 **Data Flow**

### **Data Directories**
```
./data/
├── cvs/           # CVS YAML files
├── costco/        # Costco YAML files  
├── walmart/       # Walmart YAML files
├── publix/        # Publix YAML files
└── other/         # Other purchases YAML files
```

### **Database Tables**
- `cvs_purchases`
- `costco_purchases` 
- `walmart_purchases`
- `publix_purchases`
- `other_purchases`

## 🚀 **CRON Job Details**

### **CVS Data Loader**
- **Schedule**: `30 23 * * *` (11:30 PM EST daily)
- **Script**: `src/loaders/cvs_data_loader.py`
- **Data Source**: `./data/cvs/*.yaml`
- **Target Table**: `cvs_purchases`

### **Costco Data Loader**
- **Schedule**: `35 23 * * *` (11:35 PM EST daily)
- **Script**: `src/loaders/yaml_to_database.py`
- **Data Source**: `./data/costco/*.yaml`
- **Target Table**: `costco_purchases`

### **Walmart Data Loader**
- **Schedule**: `40 23 * * *` (11:40 PM EST daily)
- **Script**: `src/loaders/walmart_data_loader.py`
- **Data Source**: `./data/walmart/*.yaml`
- **Target Table**: `walmart_purchases`

### **Publix Data Loader**
- **Schedule**: `45 23 * * *` (11:45 PM EST daily)
- **Script**: `src/loaders/publix_data_processor.py`
- **Data Source**: `./data/publix/*.yaml`
- **Target Table**: `publix_purchases`

### **Other Purchases Loader**
- **Schedule**: `50 23 * * *` (11:50 PM EST daily)
- **Script**: `src/loaders/other_purchases_loader.py`
- **Data Source**: `./data/other/*.yaml`
- **Target Table**: `other_purchases`

## 🔧 **Configuration**

### **Environment Variables**
```yaml
env:
- name: ENV
  value: "staging" | "production"
- name: DB_HOST
  valueFrom:
    configMapKeyRef:
      name: grocery-genie-config
      key: DB_HOST
- name: DB_PORT
  valueFrom:
    configMapKeyRef:
      name: grocery-genie-config
      key: DB_PORT
- name: DB_NAME
  valueFrom:
    configMapKeyRef:
      name: grocery-genie-config
      key: DB_NAME
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: grocery-genie-secrets
      key: DB_USER
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: grocery-genie-secrets
      key: DB_PASSWORD
```

### **Resource Allocation**

#### **Staging Environment**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### **Production Environment**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 📊 **Monitoring & Logging**

### **Job History**
- **Staging**: 3 successful + 3 failed jobs retained
- **Production**: 5 successful + 5 failed jobs retained

### **CRON Job Policies**
- **Concurrency**: `Forbid` (prevents overlapping jobs)
- **Restart Policy**: `OnFailure`
- **Time Zone**: `America/New_York` (EST)

### **Monitoring Commands**
```bash
# Check CRON job status
kubectl get cronjobs -n staging
kubectl get cronjobs -n production

# Check job history
kubectl get jobs -n staging -l component=data-loader
kubectl get jobs -n production -l component=data-loader

# Check pod logs
kubectl logs -n staging -l retailer=cvs
kubectl logs -n production -l retailer=costco
```

## 🛠️ **Deployment**

### **ArgoCD Setup**
1. **Connect Repository** in ArgoCD UI:
   - Repository URL: `https://github.com/tuolden/grocery-genie.git`
   - Username: `tuolden`
   - Password: `******`

2. **Create Applications**:
   - **Staging**: Path `kubernetes/staging/`
   - **Production**: Path `kubernetes/production/`

### **Manual Deployment**
```bash
# Deploy staging CRON jobs
kubectl apply -f kubernetes/staging/cronjob-data-loaders.yaml

# Deploy production CRON jobs  
kubectl apply -f kubernetes/production/cronjob-data-loaders.yaml
```

## 🔄 **Data Processing Workflow**

### **Daily Process**
1. **11:30 PM EST**: CVS data loader processes `./data/cvs/*.yaml`
2. **11:35 PM EST**: Costco data loader processes `./data/costco/*.yaml`
3. **11:40 PM EST**: Walmart data loader processes `./data/walmart/*.yaml`
4. **11:45 PM EST**: Publix data loader processes `./data/publix/*.yaml`
5. **11:50 PM EST**: Other purchases loader processes `./data/other/*.yaml`

### **Upsert Logic**
- All loaders use **upsert logic** to prevent duplicates
- Existing records are updated, new records are inserted
- **Idempotent operations** - safe to run multiple times

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Missing Data Files**: CRON jobs will log warnings but continue
2. **Database Connection**: Check secrets and config maps
3. **Resource Limits**: Monitor memory/CPU usage during peak loads
4. **Time Zone**: All schedules use EST (`America/New_York`)

### **Debug Commands**
```bash
# Check CRON job configuration
kubectl describe cronjob cvs-data-loader -n staging

# Check recent job execution
kubectl get jobs -n staging --sort-by=.metadata.creationTimestamp

# View job logs
kubectl logs job/cvs-data-loader-<timestamp> -n staging

# Manual job trigger
kubectl create job --from=cronjob/cvs-data-loader manual-cvs-load -n staging
```

## 🎯 **Benefits**

✅ **Automated Data Loading**: Daily processing without manual intervention  
✅ **Environment Separation**: Staging and production databases isolated  
✅ **Resource Management**: Appropriate resource allocation per environment  
✅ **Monitoring**: Job history and logging for troubleshooting  
✅ **GitOps**: ArgoCD manages deployment and configuration  
✅ **Scalability**: Easy to add new retailers or modify schedules  

This system ensures reliable, automated data loading for the complete 4-retailer grocery data collection system.
