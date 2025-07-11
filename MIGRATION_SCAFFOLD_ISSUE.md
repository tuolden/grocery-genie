# 🚀 Repository Migration Scaffold - CI/CD Pipeline Modernization

## 🎯 Overview

This issue outlines the complete migration scaffold for modernizing repositories to use ArgoCD-based CI/CD pipelines with comprehensive testing and monitoring.

## 📋 Migration Steps

### 🔧 Step 0: GitHub Runner Setup

**🟡 BRIGHT YELLOW BACKGROUND: CRITICAL INFRASTRUCTURE STEP**

Create GitHub self-hosted runner for the repository.

**Location:** `/Users/guslopezorozco-local/personal/github-runners/runner-deployment/`

**Actions:**
1. **🔍 LOG:** Create file `github-runner-<repo-name>.yaml`
2. **🔍 LOG:** Apply Kubernetes deployment
3. **🔍 LOG:** Verify runner registration

**File Template:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <repo-name>-runner
  labels:
    app: github-runner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: github-runner-<repo-name>
  template:
    metadata:
      labels:
        app: github-runner-<repo-name>
    spec:
      containers:
        - name: runner
          image: myoung34/github-runner:latest
          env:
            - name: RUNNER_NAME
              value: k3s-<repo-name>-runner
            - name: REPO_URL
              value: https://github.com/tuolden/<repo-name>
            - name: ACCESS_TOKEN
              valueFrom:
                secretKeyRef:
                  name: github-runner-<repo-name>-secret
                  key: GITHUB_TOKEN
            - name: RUNNER_WORKDIR
              value: /tmp/github-runner
            - name: RUNNER_GROUP
              value: Default
            - name: ORG_RUNNER
              value: "false"
          volumeMounts:
            - name: docker-sock
              mountPath: /var/run/docker.sock
      volumes:
        - name: docker-sock
          hostPath:
            path: /var/run/docker.sock
```

**Secret Creation:**
```bash
# 🔍 LOG: Creating GitHub runner secret
kubectl create secret generic github-runner-<repo-name>-secret \
  --from-literal=GITHUB_TOKEN=$GITHUB_TOKEN \
  --namespace default

# 🔍 LOG: Applying runner deployment
kubectl apply -f runner-deployment/github-runner-<repo-name>.yaml

# 🔍 LOG: Verifying runner status
kubectl get pods -l app=github-runner-<repo-name>
kubectl logs -l app=github-runner-<repo-name>
```

**Definition of Done:**
- ✅ Runner appears in GitHub repository settings
- ✅ Runner shows as "Online" status
- ✅ Kubernetes pod is running successfully
- ✅ **🔍 LOG:** All deployment steps logged with timestamps

---

### 🐳 Step 0.5: Dockerization

**🟠 BRIGHT ORANGE BACKGROUND: CONTAINERIZATION REQUIRED**

Ensure all projects run in Docker containers.

**Actions:**
1. **🔍 LOG:** Check for existing Dockerfile/docker-compose.yml
2. **🔍 LOG:** Create Dockerfile if missing
3. **🔍 LOG:** Test Docker build and run
4. **🔍 LOG:** Validate functionality in container

**Dockerfile Template (if needed):**
```dockerfile
FROM node:18-alpine
# or FROM python:3.9-slim
# or FROM openjdk:11-jre-slim

WORKDIR /app
COPY package*.json ./
# or COPY requirements.txt ./
# or COPY pom.xml ./

RUN npm install
# or RUN pip install -r requirements.txt
# or RUN mvn dependency:resolve

COPY . .

EXPOSE 3000
# or EXPOSE 8080

CMD ["npm", "start"]
# or CMD ["python", "app.py"]
# or CMD ["java", "-jar", "app.jar"]
```

**Testing Commands:**
```bash
# 🔍 LOG: Building Docker image
docker build -t <repo-name>:test .

# 🔍 LOG: Running container
docker run -d -p 3000:3000 --name <repo-name>-test <repo-name>:test

# 🔍 LOG: Testing functionality
curl -f http://localhost:3000/health || echo "Health check failed"

# 🔍 LOG: Running tests in container
docker exec <repo-name>-test npm test
# or docker exec <repo-name>-test python -m pytest
# or docker exec <repo-name>-test mvn test

# 🔍 LOG: Cleanup
docker stop <repo-name>-test && docker rm <repo-name>-test
```

**Definition of Done:**
- ✅ Dockerfile exists and builds successfully
- ✅ Application runs in Docker container
- ✅ All tests pass in containerized environment
- ✅ **🔍 LOG:** Container build and test results logged

---

### ⚙️ Step 1: GitHub Actions CI Setup

**🔵 BRIGHT BLUE BACKGROUND: CI/CD PIPELINE CREATION**

Create or update GitHub Actions workflow.

**File:** `.github/workflows/ci.yaml`

**Template:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: self-hosted
    steps:
      - name: 🔍 LOG - Checkout code
        uses: actions/checkout@v4
        
      - name: 🔍 LOG - Setup environment
        run: |
          echo "🔍 LOG: Setting up build environment"
          echo "Repository: ${{ github.repository }}"
          echo "Branch: ${{ github.ref_name }}"
          echo "Commit: ${{ github.sha }}"
          
      - name: 🔍 LOG - Run tests
        run: |
          echo "🔍 LOG: Running unit tests"
          # Add your test commands here
          npm test || python -m pytest || mvn test
          
  build:
    needs: test
    runs-on: self-hosted
    steps:
      - name: 🔍 LOG - Checkout code
        uses: actions/checkout@v4
        
      - name: 🔍 LOG - Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: 🔍 LOG - Build and push Docker image
        run: |
          echo "🔍 LOG: Building Docker image"
          IMAGE_TAG=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          docker build -t $IMAGE_TAG .
          echo "🔍 LOG: Pushing image: $IMAGE_TAG"
          docker push $IMAGE_TAG
          
      - name: 🔍 LOG - Update deployment manifest
        run: |
          echo "🔍 LOG: Updating Kubernetes deployment manifest"
          sed -i "s|image: .*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}|g" kubernetes/deployment.yaml
          
      - name: 🔍 LOG - Commit updated manifest
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add kubernetes/deployment.yaml
          git commit -m "🚀 Update image to ${{ github.sha }}" || exit 0
          git push
          
      - name: 🔍 LOG - Wait for ArgoCD sync
        run: |
          echo "🔍 LOG: Waiting for ArgoCD to sync application"
          argocd app wait <app-name> --health --sync --timeout 300
          
      - name: 🔍 LOG - Run smoke tests
        run: |
          echo "🔍 LOG: Running smoke tests"
          ./scripts/smoke_test.sh
```

**Definition of Done:**
- ✅ CI workflow exists and runs successfully
- ✅ All steps complete without errors
- ✅ **🔍 LOG:** Comprehensive logging throughout pipeline

---

### 🧪 Step 2.5: CI Testing Validation

**🟢 BRIGHT GREEN BACKGROUND: VALIDATION CHECKPOINT**

**Actions:**
```bash
# 🔍 LOG: Triggering test CI run
git commit --allow-empty -m "🧪 Test CI pipeline"
git push

# 🔍 LOG: Monitor CI execution
echo "🔍 LOG: Checking GitHub Actions status"
gh run list --limit 1
gh run view --log
```

**Definition of Done:**
- ✅ CI runs without failures
- ✅ All jobs complete successfully
- ✅ **🔍 LOG:** CI execution fully logged and monitored

---

### 🚫 Step 2.6: Remove Manual kubectl Commands

**🔴 BRIGHT RED BACKGROUND: CRITICAL CLEANUP STEP**

Remove manual kubectl commands from CI pipeline.

**Actions:**
1. **🔍 LOG:** Search for forbidden commands
2. **🔍 LOG:** Remove kubectl set image commands
3. **🔍 LOG:** Remove kubectl rollout status commands
4. **🔍 LOG:** Validate CI still works

**Search Commands:**
```bash
# 🔍 LOG: Searching for forbidden kubectl commands
grep -r "kubectl set image" .github/workflows/
grep -r "kubectl rollout status" .github/workflows/
grep -r "kubectl apply" .github/workflows/

# 🔍 LOG: Remove found commands
sed -i '/kubectl set image/d' .github/workflows/ci.yaml
sed -i '/kubectl rollout status/d' .github/workflows/ci.yaml
```

**Definition of Done:**
- ✅ No manual kubectl commands in CI
- ✅ CI still runs successfully
- ✅ **🔍 LOG:** All forbidden commands removed and logged

---

### 📝 Step 3: Update Image Tag in Deployment

**🟣 BRIGHT PURPLE BACKGROUND: GITOPS INTEGRATION**

Modify CI to update image tags in deployment.yaml via Git commits.

**Actions:**
1. **🔍 LOG:** Add sed command to replace image tag
2. **🔍 LOG:** Commit and push changes to trigger ArgoCD
3. **🔍 LOG:** Verify git history shows changes

**Implementation:**
```bash
# 🔍 LOG: Updating deployment.yaml with new image tag
echo "🔍 LOG: Current image tag in deployment.yaml:"
grep "image:" kubernetes/deployment.yaml

NEW_TAG="${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
echo "🔍 LOG: Updating to new tag: $NEW_TAG"

sed -i "s|image: .*|image: $NEW_TAG|g" kubernetes/deployment.yaml

echo "🔍 LOG: Updated image tag in deployment.yaml:"
grep "image:" kubernetes/deployment.yaml

# 🔍 LOG: Committing changes
git add kubernetes/deployment.yaml
git commit -m "🚀 Update image tag to ${{ github.sha }}"
git push origin main

echo "🔍 LOG: Git commit completed, ArgoCD should detect changes"
```

**Definition of Done:**
- ✅ Image tag updates trigger ArgoCD sync
- ✅ Changes appear in git history
- ✅ **🔍 LOG:** All image tag updates logged with before/after values

---

### 🏗️ Step 4: ArgoCD Kubernetes Manifests

**🔶 BRIGHT AMBER BACKGROUND: KUBERNETES DEPLOYMENT SETUP**

Create complete Kubernetes manifests for ArgoCD deployment.

**Directory:** `kubernetes/`

**Files to create:**

**1. application.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <repo-name>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/tuolden/<repo-name>
    targetRevision: main
    path: kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

**2. deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <repo-name>
  labels:
    app: <repo-name>
spec:
  replicas: 2
  selector:
    matchLabels:
      app: <repo-name>
  template:
    metadata:
      labels:
        app: <repo-name>
    spec:
      containers:
      - name: <repo-name>
        image: ghcr.io/tuolden/<repo-name>:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**3. service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <repo-name>-service
spec:
  selector:
    app: <repo-name>
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: ClusterIP
```

**4. ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <repo-name>-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - <repo-name>.yourdomain.com
    secretName: <repo-name>-tls
  rules:
  - host: <repo-name>.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <repo-name>-service
            port:
              number: 80
```

**5. configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <repo-name>-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  # Add other configuration as needed
```

**6. secret.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <repo-name>-secret
type: Opaque
data:
  # Add base64 encoded secrets as needed
  # Example: database-password: <base64-encoded-value>
```

**Creation Commands:**
```bash
# 🔍 LOG: Creating Kubernetes directory and manifests
mkdir -p kubernetes

echo "🔍 LOG: Creating application.yaml"
# Create application.yaml with repo-specific values

echo "🔍 LOG: Creating deployment.yaml"
# Create deployment.yaml with proper image reference

echo "🔍 LOG: Creating service.yaml"
# Create service.yaml

echo "🔍 LOG: Creating ingress.yaml"
# Create ingress.yaml with proper hostname

echo "🔍 LOG: Creating configmap.yaml"
# Create configmap.yaml

echo "🔍 LOG: Creating secret.yaml"
# Create secret.yaml

echo "🔍 LOG: All Kubernetes manifests created"
ls -la kubernetes/
```

**Definition of Done:**
- ✅ All 6 Kubernetes manifest files exist
- ✅ ArgoCD application is configured
- ✅ **🔍 LOG:** All manifest creation steps logged

---

### 🔄 Step 4.5: ArgoCD Deployment Verification

**🔸 BRIGHT CYAN BACKGROUND: DEPLOYMENT VALIDATION**

**Actions:**
```bash
# 🔍 LOG: Applying ArgoCD application
echo "🔍 LOG: Creating ArgoCD application"
kubectl apply -f kubernetes/application.yaml

# 🔍 LOG: Checking ArgoCD application status
echo "🔍 LOG: Checking ArgoCD application status"
argocd app get <repo-name>

# 🔍 LOG: Syncing application
echo "🔍 LOG: Syncing ArgoCD application"
argocd app sync <repo-name>

# 🔍 LOG: Waiting for healthy status
echo "🔍 LOG: Waiting for application to become healthy"
argocd app wait <repo-name> --health --timeout 300
```

**Definition of Done:**
- ✅ ArgoCD application deploys successfully
- ✅ All resources are healthy
- ✅ **🔍 LOG:** Deployment status fully monitored and logged

---

### ⏱️ Step 4.6: ArgoCD Health & Sync Wait in CI

**🟨 BRIGHT LIME BACKGROUND: CI INTEGRATION WITH ARGOCD**

Add ArgoCD sync health check to CI pipeline.

**CI Addition:**
```yaml
- name: 🔍 LOG - Wait for ArgoCD sync and health
  run: |
    echo "🔍 LOG: Starting ArgoCD sync wait"
    echo "🔍 LOG: Application name: <repo-name>"
    echo "🔍 LOG: Timeout: 300 seconds"

    # Wait for sync and health
    argocd app wait <repo-name> --health --sync --timeout 300

    if [ $? -eq 0 ]; then
      echo "🔍 LOG: ✅ ArgoCD sync and health check PASSED"
      argocd app get <repo-name> --output json | jq '.status'
    else
      echo "🔍 LOG: ❌ ArgoCD sync and health check FAILED"
      argocd app get <repo-name> --output json | jq '.status'
      exit 1
    fi
```

**Definition of Done:**
- ✅ CI fails if ArgoCD doesn't sync/health
- ✅ Sync status is printed to logs
- ✅ **🔍 LOG:** Comprehensive ArgoCD status logging

---

### 🧪 Step 5: Smoke Test Script and CI Integration

**🔥 BRIGHT ORANGE-RED BACKGROUND: CRITICAL TESTING STEP**

Create comprehensive smoke tests for post-deployment validation.

**File:** `scripts/smoke_test.sh` or `scripts/smoke_test.py`

**Bash Version:**
```bash
#!/bin/bash
set -e

echo "🔍 LOG: Starting smoke tests"
echo "🔍 LOG: Timestamp: $(date)"

# Configuration
BASE_URL="https://<repo-name>.yourdomain.com"
TIMEOUT=30

echo "🔍 LOG: Testing base URL: $BASE_URL"

# Test health endpoint
echo "🔍 LOG: Testing health endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$BASE_URL/health")
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "🔍 LOG: ✅ Health check PASSED (HTTP $HTTP_CODE)"
else
    echo "🔍 LOG: ❌ Health check FAILED (HTTP $HTTP_CODE)"
    exit 1
fi

# Test main endpoints
ENDPOINTS=("/api/status" "/api/version" "/")

for endpoint in "${ENDPOINTS[@]}"; do
    echo "🔍 LOG: Testing endpoint: $endpoint"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$BASE_URL$endpoint")

    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo "🔍 LOG: ✅ Endpoint $endpoint PASSED (HTTP $HTTP_CODE)"
    else
        echo "🔍 LOG: ❌ Endpoint $endpoint FAILED (HTTP $HTTP_CODE)"
        exit 1
    fi
done

echo "🔍 LOG: 🎉 All smoke tests PASSED"
echo "🔍 LOG: Smoke test completed at: $(date)"
```

**Python Version (for APIs):**
```python
#!/usr/bin/env python3
import requests
import sys
import time
from datetime import datetime

def log(message):
    print(f"🔍 LOG: {message}")

def test_endpoint(url, expected_status=200, timeout=30):
    log(f"Testing endpoint: {url}")
    try:
        response = requests.get(url, timeout=timeout)
        log(f"Response status: {response.status_code}")

        if response.status_code == expected_status:
            log(f"✅ Endpoint {url} PASSED")
            return True
        else:
            log(f"❌ Endpoint {url} FAILED (expected {expected_status}, got {response.status_code})")
            return False
    except Exception as e:
        log(f"❌ Endpoint {url} FAILED with exception: {e}")
        return False

def main():
    log(f"Starting smoke tests at {datetime.now()}")

    base_url = "https://<repo-name>.yourdomain.com"
    log(f"Base URL: {base_url}")

    endpoints = [
        f"{base_url}/health",
        f"{base_url}/api/status",
        f"{base_url}/api/version",
        f"{base_url}/"
    ]

    all_passed = True

    for endpoint in endpoints:
        if not test_endpoint(endpoint):
            all_passed = False

    if all_passed:
        log("🎉 All smoke tests PASSED")
        sys.exit(0)
    else:
        log("❌ Some smoke tests FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**CI Integration:**
```yaml
- name: 🔍 LOG - Run smoke tests
  run: |
    echo "🔍 LOG: Making smoke test script executable"
    chmod +x scripts/smoke_test.sh

    echo "🔍 LOG: Running smoke tests"
    ./scripts/smoke_test.sh

    if [ $? -eq 0 ]; then
      echo "🔍 LOG: ✅ Smoke tests PASSED"
    else
      echo "🔍 LOG: ❌ Smoke tests FAILED"
      exit 1
    fi
```

**Definition of Done:**
- ✅ Smoke test script validates all critical endpoints
- ✅ CI prints all stdout and exits on error
- ✅ **🔍 LOG:** Comprehensive test execution logging

---

### 🛡️ Step 6: Ensure ArgoCD is Sole Deployment Path

**🚨 BRIGHT RED-ORANGE BACKGROUND: CRITICAL SECURITY STEP**

Remove all manual deployment methods and enforce ArgoCD-only deployments.

**Actions:**
1. **🔍 LOG:** Remove all kubectl apply commands
2. **🔍 LOG:** Remove image mutation via CLI
3. **🔍 LOG:** Ensure CI only pushes to Git
4. **🔍 LOG:** Static analysis of all scripts

**Cleanup Commands:**
```bash
# 🔍 LOG: Searching for manual deployment commands
echo "🔍 LOG: Scanning for forbidden deployment commands"

# Search all files for kubectl apply
grep -r "kubectl apply" . --exclude-dir=.git || echo "🔍 LOG: No kubectl apply found"

# Search for kubectl set image
grep -r "kubectl set image" . --exclude-dir=.git || echo "🔍 LOG: No kubectl set image found"

# Search for kubectl patch
grep -r "kubectl patch" . --exclude-dir=.git || echo "🔍 LOG: No kubectl patch found"

# Search for docker push to production
grep -r "docker push.*prod" . --exclude-dir=.git || echo "🔍 LOG: No direct production pushes found"

echo "🔍 LOG: Forbidden command scan completed"

# Remove any found manual deployment commands
echo "🔍 LOG: Removing any manual deployment commands"
find . -name "*.sh" -o -name "*.yaml" -o -name "*.yml" | xargs sed -i '/kubectl apply/d'
find . -name "*.sh" -o -name "*.yaml" -o -name "*.yml" | xargs sed -i '/kubectl set image/d'
find . -name "*.sh" -o -name "*.yaml" -o -name "*.yml" | xargs sed -i '/kubectl patch/d'

echo "🔍 LOG: Manual deployment commands removed"
```

**CI Validation:**
```bash
# 🔍 LOG: Validating CI only uses GitOps
echo "🔍 LOG: Validating CI pipeline uses only GitOps approach"

# Check that CI only commits to Git
if grep -q "git push" .github/workflows/ci.yaml; then
    echo "🔍 LOG: ✅ CI uses Git push (GitOps approach)"
else
    echo "🔍 LOG: ❌ CI missing Git push step"
    exit 1
fi

# Check that CI doesn't use kubectl for deployment
if grep -q "kubectl apply\|kubectl set image\|kubectl patch" .github/workflows/ci.yaml; then
    echo "🔍 LOG: ❌ CI still contains manual kubectl commands"
    exit 1
else
    echo "🔍 LOG: ✅ CI is clean of manual kubectl commands"
fi

echo "🔍 LOG: CI validation completed successfully"
```

**Definition of Done:**
- ✅ No kubectl apply, set image, or patch commands anywhere
- ✅ CI only pushes to Git repository
- ✅ ArgoCD is the sole deployment mechanism
- ✅ **🔍 LOG:** Complete static analysis and cleanup logged

---

## 🎯 Migration Success Criteria

### ✅ Completion Checklist

**Infrastructure:**
- [ ] GitHub self-hosted runner operational
- [ ] Docker containerization complete
- [ ] All tests pass in containers

**CI/CD Pipeline:**
- [ ] GitHub Actions workflow functional
- [ ] No manual kubectl commands in CI
- [ ] Image tag updates via Git commits
- [ ] ArgoCD sync integration working

**Kubernetes Deployment:**
- [ ] All 6 Kubernetes manifests created
- [ ] ArgoCD application deployed and healthy
- [ ] Ingress and services accessible

**Testing & Validation:**
- [ ] Smoke tests pass consistently
- [ ] ArgoCD health checks integrated
- [ ] GitOps-only deployment enforced

### 📊 Logging Requirements

**Every step must include:**
- 🔍 **Timestamp logging** for all operations
- 🔍 **Before/after state capture** for changes
- 🔍 **Error handling and rollback logging**
- 🔍 **Success/failure status for each operation**
- 🔍 **Resource status monitoring** (pods, services, ingress)

### 🚨 Rollback Strategy

If any step fails:
1. **🔍 LOG:** Capture complete error state
2. **🔍 LOG:** Revert Git commits if necessary
3. **🔍 LOG:** Remove ArgoCD application if deployed
4. **🔍 LOG:** Restore original CI configuration
5. **🔍 LOG:** Document failure reason and resolution

### 📈 Success Metrics

**Performance Indicators:**
- ✅ Zero manual deployments after migration
- ✅ 100% GitOps deployment coverage
- ✅ Automated rollback capability
- ✅ Complete audit trail via Git history
- ✅ Smoke test success rate > 99%

---

## 🏷️ Labels

- `migration`
- `ci-cd`
- `argocd`
- `kubernetes`
- `gitops`
- `high-priority`

## 👥 Assignees

- Migration AI Agents
- DevOps Team

---

**🔍 LOG: Migration scaffold issue created with comprehensive logging and bright highlighting for maximum visibility**
