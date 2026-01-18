import requests
import json

try:
    response = requests.get('http://localhost:5000/documents', timeout=5)
    response.raise_for_status()
    data = response.json()
    
    if data:
        print("First item keys:")
        print(json.dumps(list(data[0].keys()), indent=2))
        print("First item sample:")
        print(json.dumps(data[0], indent=2))
    else:
        print("No documents returned.")

except Exception as e:
    print(f"Error: {e}")
