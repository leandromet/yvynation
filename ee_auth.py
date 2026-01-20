'''
Earth Engine authentication utilities for Cloud Run deployment.
Handles service account authentication via environment variables.
'''

import os
import json
import ee
from google.oauth2 import service_account

def initialize_earth_engine():
    """
    Initialize Earth Engine with service account credentials.
    
    For Cloud Run:
    - Set EE_PRIVATE_KEY and EE_SERVICE_ACCOUNT_EMAIL as environment variables
    - Or use ADC (Application Default Credentials) if running on Google Cloud
    
    For Streamlit Cloud:
    - Use st.secrets with service account JSON
    
    Returns:
        ee module (initialized)
    """
    
    # Try Cloud Run environment variables first
    private_key = os.environ.get('EE_PRIVATE_KEY')
    service_account_email = os.environ.get('EE_SERVICE_ACCOUNT_EMAIL')
    project_id = os.environ.get('GCP_PROJECT_ID', 'ee-leandromet')
    
    if private_key and service_account_email:
        try:
            # Build credentials from environment variables
            credentials_dict = {
                'type': 'service_account',
                'project_id': project_id,
                'private_key_id': os.environ.get('EE_PRIVATE_KEY_ID', ''),
                'private_key': private_key,
                'client_email': service_account_email,
                'client_id': os.environ.get('EE_CLIENT_ID', ''),
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            }
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    'https://www.googleapis.com/auth/earthengine',
                    'https://www.googleapis.com/auth/cloud-platform'
                ]
            )
            ee.Initialize(credentials, project=project_id)
            return ee
        except Exception as e:
            print(f"Error initializing with environment variables: {e}")
    
    # Try Application Default Credentials (for Google Cloud environment)
    try:
        ee.Initialize(project=project_id)
        return ee
    except Exception as e:
        print(f"Error with Application Default Credentials: {e}")
    
    # Fallback - this will fail but provides helpful error message
    raise RuntimeError(
        "Failed to initialize Earth Engine. "
        "Set EE_PRIVATE_KEY and EE_SERVICE_ACCOUNT_EMAIL environment variables, "
        "or ensure Application Default Credentials are configured."
    )
