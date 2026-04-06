import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("INSTAGRAM_TOKEN")
API = "https://graph.facebook.com/v25.0"

print("🔍 Debugging Facebook Page Token Permissions & Linking")

# 1. Check Permissions
resp = requests.get(f"{API}/me/permissions", params={"access_token": TOKEN})
print("\n📋 Permissions:", resp.json())

# 2. Check Linked IG Account
resp = requests.get(f"{API}/me", params={"fields": "instagram_business_account,name", "access_token": TOKEN})
print("\n🔗 Linked IG Account:", resp.json())
