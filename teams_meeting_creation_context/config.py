import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Microsoft Azure App Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
