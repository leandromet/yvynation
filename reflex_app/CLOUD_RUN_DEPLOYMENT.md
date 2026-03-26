# Cloud Run Deployment Guide

## Prerequisites

```bash
# Set your GCP project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable compute.googleapis.com

# Setup Earth Engine service account
# See: https://developers.google.com/earth-engine/guides/service_accounts
```

## Step 1: Prepare Service Account

```bash
# Download service account JSON from GCP Console
# Place it in a secure location (not in git!)

# Store path in .env
echo "SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json" >> .env
```

## Step 2: Build Docker Image

### Option A: Local Build & Push

```bash
# Build locally
docker build -t gcr.io/$PROJECT_ID/yvynation:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/yvynation:latest

# Or use Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/yvynation:latest
```

### Option B: Cloud Build (recommended)

```bash
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/yvynation:latest \
  --substitutions=_COMMIT_SHA=$(git rev-parse --short HEAD)
```

## Step 3: Deploy to Cloud Run

```bash
gcloud run deploy yvynation \
  --image gcr.io/$PROJECT_ID/yvynation:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 100 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID
```

### Passing Service Account to Cloud Run

Option 1: Mount service account key (less secure)
```bash
gcloud run deploy yvynation \
  --update-env-vars SERVICE_ACCOUNT_JSON=/secrets/sa-key.json \
  --update-secrets SERVICE_ACCOUNT_JSON=projects/$PROJECT_ID/secrets/sa-key:latest
```

Option 2: Use Workload Identity (recommended)
```bash
# Create service account
gcloud iam service-accounts create yvynation-sa \
  --display-name="Yvynation Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:yvynation-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/earthengine.admin"

# Bind to Cloud Run
gcloud run services update-template yvynation \
  --set-service-account yvynation-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 4: Verify Deployment

```bash
# Get service URL
gcloud run services describe yvynation --format='value(status.url)'

# Check logs
gcloud run services logs read yvynation --limit 100

# Monitor metrics
gcloud monitoring dashboards create --config-from-file=monitoring.yaml
```

## Step 5: Auto-scaling Configuration

```bash
# Set auto-scaling parameters
gcloud run services update yvynation \
  --max-instances 100 \
  --min-instances 1 \
  --cpu-throttling \
  --memory 2Gi
```

## Optimization Tips for Cloud Run

### 1. Memory & CPU

| Load | Memory | CPU | Cost/mo |
|------|--------|-----|---------|
| Dev | 512MB | 0.5 | ~$6 |
| Small (10 users) | 1Gi | 1 | ~$12 |
| Medium (100 users) | 2Gi | 2 | ~$25 |
| Large (1k users) | 4Gi | 4 | ~$50 |

### 2. Startup Time

Reflex startup: ~5-10 seconds

```dockerfile
# Optimize layer caching - keep requirements.txt unchanged
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .  # Copy code after pip install
```

### 3. Cost Reduction

```bash
# Use Cloud Scheduler to stop app during off-hours
gcloud scheduler jobs create http-custom yvynation-shutdown \
  --schedule="0 22 * * *" \
  --http-method=POST \
  --uri=https://your-yvynation-url.run.app/shutdown
```

## Monitoring & Alerts

### Setup Cloud Monitoring

```bash
# Create alert policy
gcloud alpha monitoring policies create \
  --display-name="Yvynation Error Rate" \
  --condition-names=error-condition

# View real-time logs
gcloud run services logs read yvynation --follow
```

### Key Metrics to Monitor

```python
# In your Reflex app:
import logging
logger = logging.getLogger(__name__)

# These automatically appear in Cloud Logging
logger.info(f"User {user_id} analyzed territory in {duration}s")
logger.error(f"EE API error: {error}")
```

## Continuous Deployment

### Option A: GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - uses: google-github-actions/setup-gcloud@v1
      
      - name: Deploy
        run: |
          gcloud run deploy yvynation \
            --source . \
            --region us-central1 \
            --platform managed
```

### Option B: Cloud Build

```yaml
# cloudbuild.yaml
steps:
  # Build
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/yvynation', '.']
  
  # Push
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/yvynation']
  
  # Deploy
  - name: 'gcr.io/cloud-builders/run'
    args:
      - 'deploy'
      - 'yvynation'
      - '--image=gcr.io/$PROJECT_ID/yvynation'
      - '--region=us-central1'
      - '--platform=managed'
```

## Database Setup (Production)

### Use Cloud SQL for PostgreSQL

```bash
# Create instance
gcloud sql instances create yvynation-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create yvynation --instance=yvynation-db

# Set connection secrets
gcloud secrets create database-url \
  --replication-policy="automatic"
```

Update Reflex config in `.env`:
```
REFLEX_DB_URL=postgresql://user:password@<cloud-sql-ip>/yvynation
```

## Security

### Network Security

```bash
# Restrict Cloud Run to internal VPC
gcloud run services update yvynation \
  --no-allow-unauthenticated \
  --service-account=yvynation-sa

# Add Cloud Armor for DDoS protection
gcloud compute security-policies create yvynation-policy \
  --description "Yvynation DDoS protection"
```

### Secrets Management

```bash
# Store Earth Engine credentials securely
gcloud secrets create ee-service-account \
  --replication-policy="automatic" \
  --data-file=path/to/sa-key.json

# Reference in Cloud Run
gcloud run services upgrade yvynation \
  --update-secrets EE_SERVICE_ACCOUNT=ee-service-account:1
```

## Troubleshooting

### Common Issues

**1. Service won't start (startup exceeded 4 minutes)**
```bash
# Increase memory
gcloud run services update yvynation --memory 2Gi

# Check logs
gcloud run services logs read yvynation --limit 50
```

**2. Earth Engine authentication fails**
```bash
# Verify service account has EE permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format='table(bindings.role)' \
  --filter="bindings.members:yvynation-sa"
```

**3. High latency (analysis takes > 30s)**
```bash
# Increase CPU
gcloud run services update yvynation --cpu 4

# Check EE API quota
# Monitor in Google Cloud Console > APIs & Services > Earth Engine
```

## Rollback

```bash
# List recent revisions
gcloud run revisions list --service=yvynation

# Roll back to previous version
gcloud run services update-traffic yvynation \
  --to-revisions=REVISION_ID=100
```

## Cleanup

```bash
# Delete Cloud Run service
gcloud run services delete yvynation --region=us-central1

# Delete container image
gcloud container images delete gcr.io/$PROJECT_ID/yvynation

# Delete Cloud SQL instance
gcloud sql instances delete yvynation-db
```

---

**Production Checklist:**
- [ ] Service account created with EE permissions
- [ ] Secrets stored in Cloud Secrets
- [ ] Cloud SQL database configured
- [ ] Cloud Monitoring alerts setup
- [ ] CD/CI pipeline configured
- [ ] SSL certificate configured
- [ ] Domain DNS records updated
- [ ] Backup strategy documented
