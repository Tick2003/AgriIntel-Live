import requests

try:
    print("Testing CEDA API...")
    r = requests.get("https://api.ceda.ashoka.edu.in/v1/commodities", timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("Response:", r.text[:200])
    else:
        print("Failed to access CEDA API")
except Exception as e:
    print(f"Error: {e}")
