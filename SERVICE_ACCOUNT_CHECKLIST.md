# Service Account Setup Checklist

## Quick Reference for Setting Up Google Cloud Service Account

### ✅ Files Created/Updated:
- `SERVICE_ACCOUNT_SETUP.md` - Complete step-by-step guide
- `streamlit_app.py` - Updated with service account authentication support
- `requirements.txt` - Added `google-auth` and `google-auth-oauthlib`
- `.gitignore` - Protected `.streamlit/secrets.toml`
- `.streamlit/config.toml` - Streamlit Cloud configuration
- `.streamlit/secrets.toml.example` - Secrets template

---

## 🚀 Quick Setup Steps:

### 1. Create Google Cloud Project & Service Account
Follow: `SERVICE_ACCOUNT_SETUP.md` → Steps 1-4

### 2. Register with Earth Engine
Follow: `SERVICE_ACCOUNT_SETUP.md` → Step 5
**Note:** Wait for approval (can take hours)

### 3. Download Service Account JSON Key
Follow: `SERVICE_ACCOUNT_SETUP.md` → Step 4

### 4. Configure Local Development (Optional)
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your service account JSON content
```

### 5. Test Locally
```bash
streamlit run streamlit_app.py
```

### 6. Push to GitHub
```bash
git add .
git commit -m "Setup service account for Earth Engine authentication"
git push
```

### 7. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Create new app → select this repository
3. Main file: `streamlit_app.py`
4. Go to app settings → Secrets
5. Paste your service account JSON (from step 3)

---

## 📋 Important Reminders

- **DO NOT** commit `.streamlit/secrets.toml` to GitHub (it's in `.gitignore`)
- **DO** keep your service account JSON file secure
- **DO** wait after Earth Engine registration before deploying
- **DO** test locally first to ensure authentication works

---

## 🔗 Key Resources

- [SERVICE_ACCOUNT_SETUP.md](./SERVICE_ACCOUNT_SETUP.md) - Detailed guide
- [Google Cloud Console](https://console.cloud.google.com/)
- [Earth Engine Signup](https://earthengine.google.com/signup/)
- [Streamlit Cloud Secrets](https://docs.streamlit.io/deploy/streamlit-cloud/deploy-your-app/secrets-management)

---

## ❓ Need Help?

Check `SERVICE_ACCOUNT_SETUP.md` → Troubleshooting section
