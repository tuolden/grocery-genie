# Grocery Genie Deployment Guide

## 🎯 **Overview**

This guide covers deploying Grocery Genie to production environments using Docker, Kubernetes (K3s), and ArgoCD for GitOps-based continuous deployment.

---

## 🏗️ **Architecture Overview**

### **Deployment Environments**
- **Local Development**: Docker Compose for testing
- **Staging**: K3s cluster with staging database
- **Production**: K3s cluster with production database

### **Components**
- **Application Container**: Main Grocery Genie application
- **PostgreSQL Database**: Data storage
- **ArgoCD**: GitOps deployment management
- **CRON Jobs**: Automated data loading (5 jobs per environment)

---

## 🐳 **Docker Deployment**

### **Building the Container**

```bash
# Clone repository
git clone https://github.com/tuolden/grocery-genie.git
cd grocery-genie

# Build Docker image
docker build -t grocery-genie:latest .

# Tag for registry
docker tag grocery-genie:latest ghcr.io/tuolden/grocery-genie:latest

# Push to registry
docker push ghcr.io/tuolden/grocery-genie:latest
```

### **Running with Docker Compose**

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  grocery-genie:
    image: ghcr.io/tuolden/grocery-genie:latest
    ports:
      - "8080:8080"
    environment:
      - ENV=production
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=grocery_genie
      - DB_USER=grocery_user
      - DB_PASSWORD=secure_password
    depends_on:
      - postgres
    volumes:
      - ./data:/app/data
      - ./raw:/app/raw
      - ./logs:/app/logs

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=grocery_genie
      - POSTGRES_USER=grocery_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

```bash
# Start services
docker-compose up -d

# Check health
curl http://localhost:8080/health

# View logs
docker-compose logs -f grocery-genie
```

---

## ☸️ **Kubernetes (K3s) Deployment**

### **Prerequisites**

```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Verify installation
kubectl get nodes

# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### **Database Setup**

Create `postgres-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: grocery-genie
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: "grocery_genie"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: grocery-genie
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### **Application Deployment**

The application uses the existing Kubernetes manifests:

```bash
# Deploy staging environment
kubectl apply -f kubernetes/staging/

# Deploy production environment  
kubectl apply -f kubernetes/production/

# Verify deployments
kubectl get pods -n staging
kubectl get pods -n production
```

---

## 🔄 **ArgoCD GitOps Setup**

### **Installing ArgoCD Applications**

```bash
# Apply ArgoCD applications
kubectl apply -f kubernetes/argocd-staging.yaml
kubectl apply -f kubernetes/argocd-production.yaml

# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### **ArgoCD Application Configuration**

The applications are configured to:
- **Source**: `https://github.com/tuolden/grocery-genie.git`
- **Path**: `kubernetes/staging/` or `kubernetes/production/`
- **Sync Policy**: Automatic with self-healing
- **Sync Options**: Prune resources, create namespace

### **Monitoring ArgoCD Sync**

```bash
# Check application status
kubectl get applications -n argocd

# View sync status
argocd app get grocery-genie-staging
argocd app get grocery-genie-production

# Manual sync (if needed)
argocd app sync grocery-genie-staging
```

---

## ⏰ **CRON Jobs Configuration**

### **Staging CRON Jobs**

Located in `kubernetes/staging/cronjob-data-loaders.yaml`:

```yaml
# 5 CRON jobs running at 11:30-11:50 PM EST
- CVS Data Loader (11:30 PM)
- Costco Data Loader (11:35 PM)  
- Walmart Data Loader (11:40 PM)
- Publix Data Loader (11:45 PM)
- Other Data Loader (11:50 PM)
```

### **Production CRON Jobs**

Located in `kubernetes/production/cronjob-data-loaders.yaml`:

- Same schedule as staging
- Different resource allocations
- Production database connections
- Enhanced monitoring and alerting

### **Monitoring CRON Jobs**

```bash
# Check CRON job status
kubectl get cronjobs -n staging
kubectl get cronjobs -n production

# View recent job runs
kubectl get jobs -n staging
kubectl get jobs -n production

# Check job logs
kubectl logs -n staging job/grocery-genie-cronjob-cvs-<timestamp>
```

---

## 🔧 **Configuration Management**

### **ConfigMaps**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grocery-genie-config
  namespace: staging
data:
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "grocery_genie_staging"
  ENV: "staging"
```

### **Secrets**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grocery-genie-secrets
  namespace: staging
type: Opaque
data:
  DB_USER: <base64-encoded-username>
  DB_PASSWORD: <base64-encoded-password>
```

### **Environment-Specific Configuration**

**Staging**:
- Smaller resource limits
- Debug logging enabled
- Shorter job history retention
- Test database connections

**Production**:
- Higher resource limits
- Production logging levels
- Longer job history retention
- Production database connections

---

## 📊 **Monitoring and Logging**

### **Health Checks**

```bash
# Application health
kubectl exec -it deployment/grocery-genie-staging -- python src/utils/healthcheck.py

# Database connectivity
kubectl exec -it deployment/postgres -- psql -U grocery_user -d grocery_genie -c "SELECT 1;"

# API endpoints
curl https://staging.api.grocery-genie.com/health
curl https://api.grocery-genie.com/health
```

### **Log Collection**

```bash
# Application logs
kubectl logs -f deployment/grocery-genie-staging -n staging
kubectl logs -f deployment/grocery-genie-production -n production

# CRON job logs
kubectl logs -f cronjob/grocery-genie-cronjob-cvs -n staging

# Database logs
kubectl logs -f deployment/postgres -n staging
```

### **Metrics and Alerting**

Future enhancements will include:
- Prometheus metrics collection
- Grafana dashboards
- AlertManager notifications
- Custom health check endpoints

---

## 🚀 **Deployment Checklist**

### **Pre-Deployment**

- [ ] Database credentials configured
- [ ] Container images built and pushed
- [ ] Kubernetes manifests updated
- [ ] ArgoCD applications configured
- [ ] Environment variables set

### **Deployment**

- [ ] Apply Kubernetes manifests
- [ ] Verify pod startup
- [ ] Check health endpoints
- [ ] Test CRON job execution
- [ ] Validate data loading

### **Post-Deployment**

- [ ] Monitor application logs
- [ ] Verify database connections
- [ ] Test API endpoints
- [ ] Check ArgoCD sync status
- [ ] Validate CRON job schedules

---

## 🔧 **Troubleshooting**

### **Common Issues**

**Pod Startup Failures**:
```bash
# Check pod status
kubectl describe pod <pod-name> -n <namespace>

# View container logs
kubectl logs <pod-name> -n <namespace>

# Check resource constraints
kubectl top pods -n <namespace>
```

**Database Connection Issues**:
```bash
# Test database connectivity
kubectl exec -it deployment/postgres -- psql -U grocery_user -d grocery_genie

# Check service endpoints
kubectl get endpoints -n <namespace>

# Verify secrets
kubectl get secret grocery-genie-secrets -o yaml
```

**CRON Job Failures**:
```bash
# Check job status
kubectl describe cronjob <cronjob-name> -n <namespace>

# View failed job logs
kubectl logs job/<job-name> -n <namespace>

# Manual job execution
kubectl create job --from=cronjob/<cronjob-name> <manual-job-name>
```

---

## 📞 **Support**

- **Deployment Issues**: [GitHub Issues](https://github.com/tuolden/grocery-genie/issues)
- **Documentation**: [Project Overview](PROJECT_OVERVIEW.md)
- **Email**: tuolden@gmail.com

---

**This deployment guide ensures reliable, scalable, and maintainable production deployments of Grocery Genie.**
