# 🚀 Staging Environment Setup for Grocery Genie

This document describes the staging environment setup for the Grocery Genie K3s deployment, implementing the requirements from GitHub Issue #6.

## 🎯 Overview

The staging environment provides a safe, isolated testing environment that mirrors production while allowing for comprehensive testing without affecting production data or infrastructure.

## 🏗️ Architecture

### Namespace Isolation
- **Staging**: `staging` namespace
- **Production**: `production` namespace

### Ingress Routing
- **Staging**: `staging.api.grocery-genie.com` → `staging` namespace
- **Production**: `api.grocery-genie.com` → `production` namespace

### Environment Configuration
- Separate ConfigMaps and Secrets per namespace
- Environment-specific settings (logging, retention, etc.)
- Staging uses debug logging and shorter data retention

## 📁 Directory Structure

```
kubernetes/
├── staging/                    # Staging environment manifests
│   ├── namespace.yaml         # Staging namespace
│   ├── deployment.yaml        # Staging deployment
│   ├── service.yaml          # Staging service
│   ├── ingress.yaml          # Staging ingress (staging.api.*)
│   ├── configmap.yaml        # Staging configuration
│   ├── secrets.yaml          # Staging secrets
│   └── pvc.yaml              # Staging persistent volumes
├── production/                # Production environment manifests
│   ├── namespace.yaml        # Production namespace
│   ├── deployment.yaml       # Production deployment
│   ├── service.yaml         # Production service
│   ├── ingress.yaml         # Production ingress (api.*)
│   ├── configmap.yaml       # Production configuration
│   ├── secrets.yaml         # Production secrets
│   └── pvc.yaml             # Production persistent volumes
├── argocd-staging-application.yaml    # ArgoCD staging app
└── argocd-production-application.yaml # ArgoCD production app
```

## 🔄 CI/CD Workflow

### On Push to Main Branch
1. **Test**: Run unit tests and comprehensive test suite
2. **Build**: Build and push Docker image to GHCR
3. **Deploy to Staging**: Update staging manifests and commit
4. **Smoke Test**: Run staging-specific smoke tests
5. **Notify**: Report staging deployment status

### On Release Tag
1. All staging steps (above)
2. **Deploy to Production**: Update production manifests and commit
3. **Notify**: Report production deployment status

## 🧪 Staging Smoke Tests

The staging environment includes comprehensive smoke tests that:
- ✅ Only run in staging environment (`ENV=staging`)
- ✅ Test database connectivity and data integrity
- ✅ Validate file system access
- ✅ Check environment configuration
- ✅ Test API endpoints (if available)
- ✅ Use mirrored production data (read-only)
- ❌ Never modify production data

## 🛠️ Setup Instructions

### 1. Deploy ArgoCD Applications

```bash
# Apply ArgoCD applications
kubectl apply -f kubernetes/argocd-staging-application.yaml
kubectl apply -f kubernetes/argocd-production-application.yaml
```

### 2. Configure Secrets

Update the base64-encoded secrets in:
- `kubernetes/staging/secrets.yaml` - Staging database credentials
- `kubernetes/production/secrets.yaml` - Production database credentials

```bash
# Encode secrets
echo -n "your-staging-db-host" | base64
echo -n "your-production-db-host" | base64
```

### 3. Configure Ingress Domains

Update the ingress hostnames in:
- `kubernetes/staging/ingress.yaml` - Set your staging domain
- `kubernetes/production/ingress.yaml` - Set your production domain

### 4. Verify Deployment

```bash
# Check staging deployment
kubectl get pods -n staging
kubectl get ingress -n staging

# Check production deployment
kubectl get pods -n production
kubectl get ingress -n production
```

## 🔧 Environment Variables

### Staging Environment
- `ENV=staging`
- `ENABLE_DEBUG_LOGGING=true`
- `ENABLE_SMOKE_TESTS=true`
- `LOG_LEVEL=DEBUG`
- `DATA_RETENTION_DAYS=30`

### Production Environment
- `ENV=production`
- `ENABLE_DEBUG_LOGGING=false`
- `ENABLE_SMOKE_TESTS=false`
- `LOG_LEVEL=INFO`
- `DATA_RETENTION_DAYS=365`

## 🔒 Security Considerations

### Staging
- Uses separate database with mirrored/anonymized data
- Debug logging enabled for troubleshooting
- Shorter data retention for storage efficiency
- Can be fully rebuilt from scratch

### Production
- Uses production database with real data
- Minimal logging for performance
- Longer data retention for compliance
- Protected from automated rebuilds
- Manual approval required for sensitive changes

## 📊 Monitoring and Logging

### Health Checks
- Liveness probe: `python healthcheck.py`
- Readiness probe: `python healthcheck.py`
- Custom health check script validates:
  - Database connectivity
  - File system access
  - Required directories

### Logging
- Staging: DEBUG level with extensive logging
- Production: INFO level with essential logging
- Persistent log storage via PVCs
- Separate log volumes per environment

## 🚨 Troubleshooting

### Common Issues

1. **ArgoCD not syncing**
   ```bash
   kubectl get applications -n argocd
   kubectl describe application grocery-genie-staging -n argocd
   ```

2. **Pod not starting**
   ```bash
   kubectl logs -n staging deployment/grocery-genie
   kubectl describe pod -n staging -l app=grocery-genie
   ```

3. **Database connection issues**
   ```bash
   kubectl exec -n staging deployment/grocery-genie -- python healthcheck.py
   ```

4. **Ingress not working**
   ```bash
   kubectl get ingress -n staging
   kubectl describe ingress grocery-genie-ingress -n staging
   ```

### Smoke Test Failures
- Check environment variables are set correctly
- Verify database credentials in secrets
- Ensure staging database is accessible
- Check file system permissions

## 📝 Next Steps

1. Configure actual database credentials in secrets
2. Set up proper domain names for ingress
3. Configure SSL certificates with cert-manager
4. Set up monitoring and alerting
5. Implement database backup/restore for staging
6. Add more comprehensive smoke tests as needed

## 🔗 Related Documentation

- [Main README](README.md) - Project overview
- [GitHub Issue #6](https://github.com/tuolden/grocery-genie/issues/6) - Original requirements
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/) - GitOps deployment
- [K3s Documentation](https://k3s.io/) - Lightweight Kubernetes
