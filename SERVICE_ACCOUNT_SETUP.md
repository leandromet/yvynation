# Earth Engine Service Account Setup for Streamlit Cloud

This guide walks you through creating and configuring a Google Cloud service account for Earth Engine API access in Streamlit Cloud.

## Step 1: Create a Google Cloud Project (if you don't have one)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "NEW PROJECT"
4. Name it (e.g., "yvynation-ee") and click "CREATE"

## Step 2: Enable Earth Engine API

1. In the Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Earth Engine API"
3. Click on it and click **ENABLE**

## Step 3: Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS**
3. Select **Service Account**
4. Fill in the details:
   - Service account name: `streamlit-ee-service` (or similar)
   - Service account ID: auto-generated
   - Click **CREATE AND CONTINUE**
5. Grant roles (on the next screen):
   - Click **+ GRANT ROLE**
   - Search for and select **Editor** role (gives full access)
   - Click **CONTINUE**
6. Click **DONE**

## Step 4: Create and Download the Key

1. In the Cloud Console, go to **APIs & Services** > **Service Accounts**
2. Find the service account you just created
3. Click on it to open the details
4. Go to the **KEYS** tab
5. Click **+ CREATE NEW KEY**
6. Choose **JSON**
7. A JSON file will download automatically (save it securely)
8. The JSON contains your credentials - **keep it secret!**

## Step 5: Register Service Account with Earth Engine

1. Go to [Google Earth Engine Sign Up](https://earthengine.google.com/signup/)
2. Sign in with the Google account that owns the Cloud project
3. Use the email from the service account JSON file:
   - Open the JSON file
   - Find the `client_email` field
   - Copy it (looks like: `streamlit-ee-service@project-id.iam.gserviceaccount.com`)
4. Paste it in the Earth Engine signup form
5. Accept terms and complete signup

**Note:** Earth Engine approval can take a few minutes to a few hours.

## Step 6: Add Service Account Email to Earth Engine Project (Optional)

If you're using a specific Earth Engine project, add the service account email:

1. Go to [Earth Engine Code Editor](https://code.earthengine.google.com/)
2. Go to **Assets** > **Projects** (or your specific project)
3. Click the project name
4. In settings, add the service account email as a collaborator with appropriate permissions

## Step 7: Configure Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app dashboard: [share.streamlit.io](https://share.streamlit.io)
2. Find your app in the list
3. Click the three dots menu → **Settings**
4. Go to the **Secrets** section
5. In the text editor, add:

```toml
[google]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-ee-service@project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

[ee_project_id]
value = "ee-leandromet"
```

**To get these values:**
- Open your downloaded JSON file
- Copy all the content except the `type` field (keep it as "service_account")
- Add `ee_project_id` from your Earth Engine project

## Step 8: Update Your Application Code

Your `streamlit_app.py` already imports `ee` and initializes it. Update the initialization at the top:

```python
import ee
import streamlit as st
import json
from google.oauth2 import service_account

# Initialize Earth Engine with service account
@st.cache_resource
def init_ee():
    """Initialize Earth Engine with service account credentials."""
    try:
        # Try to get credentials from Streamlit secrets
        if "google" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["google"]
            )
            ee.Initialize(credentials)
        else:
            # Fallback to default authentication (local development)
            ee.Initialize()
    except Exception as e:
        st.error(f"Earth Engine initialization failed: {e}")
        st.stop()

init_ee()
```

## Step 9: Test Locally (Optional)

1. Create a `.streamlit/secrets.toml` file (git-ignored):
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

2. Copy your JSON service account key content into it:
```toml
[google]
type = "service_account"
project_id = "..."
# ... (rest of the JSON)
```

3. Run locally:
```bash
streamlit run streamlit_app.py
```

## Step 10: Push to GitHub and Deploy

```bash
# Make sure secrets.toml is NOT committed (it's in .gitignore)
git add .
git commit -m "Add Earth Engine service account support for Streamlit Cloud"
git push
```

Your Streamlit Cloud app will automatically use the secrets you configured in the dashboard.

## Troubleshooting

### "Earth Engine is not initialized" Error
- Check that the service account email is registered with Earth Engine
- Wait a few minutes after registration (it can take time to activate)
- Verify the service account has Earth Engine API access

### "Permission denied" or "Not found" errors
- Ensure the service account has the Editor role in the Cloud project
- Check that Earth Engine API is enabled in the Cloud project
- Verify the service account email is added to your Earth Engine project

### JSON key security
- Never commit the service account JSON to GitHub
- Only store it in Streamlit Cloud secrets or local `.streamlit/secrets.toml`
- The `.gitignore` file already protects this

## Service Account Cost Considerations

- Google Cloud offers a free tier with credits ($300 for new accounts)
- Earth Engine API access via service account is **free**
- You may incur costs for other GCP services (Compute, Storage, etc.)
- For this app, costs should be minimal

## References

- [Google Cloud Service Accounts Documentation](https://cloud.google.com/docs/authentication/service-accounts)
- [Earth Engine Python API Setup](https://developers.google.com/earth-engine/guides/auth)
- [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-cloud/deploy-your-app/secrets-management)
