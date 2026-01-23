# Streamlit Cloud Deployment Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (free at [streamlit.io](https://streamlit.io))
- Repository pushed to GitHub

## Step 1: Push to GitHub

Make sure your repository is on GitHub:
```bash
cd /home/leandromb/google_eengine/yvynation
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

## Step 2: Create `.streamlit/secrets.toml` (Local Only)

Create a local secrets file (git-ignored):
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your Earth Engine credentials:
```toml
ee_project_id = "ee-leandromet"
```

## Step 3: Authenticate Earth Engine

Run locally to set up Earth Engine credentials:
```bash
earthengine authenticate
```

This creates credentials in `~/.config/earthengine/`

## Step 4: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repository
4. Set main file path to: `streamlit_app.py`
5. Configure secrets in the "Advanced settings":
   - Add your Earth Engine project ID
   - Any other environment variables needed

## Step 5: Set Environment Variables

In Streamlit Cloud dashboard:
- Go to app settings → Secrets
- Add Earth Engine service account key (if using service account)
- Or set `ee_project_id` matching your config

## Troubleshooting

### Earth Engine Authentication Issues
If you get authentication errors:
1. Use a service account key instead of personal credentials
2. Upload the service account JSON to Streamlit Cloud secrets
3. Reference it in `config.py`:
```python
import json
import streamlit as st

if "STREAMLIT_RUNTIME_EXISTS" in st.__dict__:
    # Running on Streamlit Cloud
    ee_credentials = st.secrets.get("ee_credentials_json", {})
    ee.Initialize(ee.ServiceAccountCredentials(None, json.dumps(ee_credentials)))
else:
    # Running locally
    ee.Initialize()
```

### Dependencies
All Python dependencies should be in `requirements.txt`. The deployment uses:
- Python 3.10+
- All packages from requirements.txt

### Memory/Performance
- Streamlit Cloud has resource limits
- Cache computations with `@st.cache_data`
- Use `@st.cache_resource` for Earth Engine objects

## Files Created for Deployment

- `.streamlit/config.toml` - Streamlit configuration
- `.streamlit/secrets.toml.example` - Example secrets template
- `.gitignore` - Already configured to ignore `.streamlit/secrets.toml`
- `requirements.txt` - All dependencies listed

## Additional Notes

- The app will auto-update when you push to GitHub
- Logs are viewable in the Streamlit Cloud dashboard
- Free tier includes enough resources for small projects
- Domain: `your-username-app-name.streamlit.app`
