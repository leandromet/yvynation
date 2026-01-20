# Cloud Run Deployment Configuration

## Environment Variables for Cloud Run

You need to set the following secrets in Cloud Run:

### Option 1: Using a Service Account Key File (Recommended)

1. Download your service account key JSON from Google Cloud Console
2. Extract these values from the JSON:

```bash
# From your streamlit-ee-service@ee-leandromet.iam.gserviceaccount.com service account

gcloud secrets create EE_PRIVATE_KEY --data-file=private-key-path.json

# Or manually:
gcloud secrets create EE_PRIVATE_KEY --replication-policy="automatic" --data-file=- << 'EOF'
{paste the private_key value from service account JSON}
EOF

gcloud secrets create EE_SERVICE_ACCOUNT_EMAIL --replication-policy="automatic" --data-file=- << 'EOF'
streamlit-ee-service@ee-leandromet.iam.gserviceaccount.com
EOF

gcloud secrets create GCP_PROJECT_ID --replication-policy="automatic" --data-file=- << 'EOF'
ee-leandromet
EOF
```

### Option 2: Using Application Default Credentials (Simpler)

If you deploy Cloud Run from Google Cloud, it automatically uses ADC:

```bash
gcloud run deploy yvynation \
  --source . \
  --platform managed \
  --region us-central1 \
  --service-account streamlit-ee-service@ee-leandromet.iam.gserviceaccount.com \
  --memory 2Gi \
  --allow-unauthenticated
```

This way you don't need to manage secrets at all!

## Full Deployment Command

```bash
# Set project
gcloud config set project ee-leandromet

# Deploy with service account for ADC
gcloud run deploy yvynation \
  --source . \
  --platform managed \
  --region us-central1 \
  --service-account streamlit-ee-service@ee-leandromet.iam.gserviceaccount.com \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=ee-leandromet"
```

## Security - Keep Credentials Safe

✅ **DO:**
- Use Cloud Run's service account attachment (recommended)
- Use Google Cloud Secret Manager
- Never commit private keys to GitHub
- The `.gcloudignore` file excludes `*.json` files

❌ **DON'T:**
- Hardcode credentials in Python files
- Commit service account keys to Git
- Use the same key in production and testing
- Share credentials via email/chat

## Verify Deployment

```bash
# Check deployment status
gcloud run services describe yvynation --region us-central1

# View logs
gcloud run services logs read yvynation --region us-central1 --limit 50
```
