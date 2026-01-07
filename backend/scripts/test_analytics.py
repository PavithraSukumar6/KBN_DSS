import requests

try:
    res = requests.get('http://localhost:5000/analytics')
    print(f"Status: {res.status_code}")
    print("Content:", res.text[:500])
    try:
        print("JSON:", res.json())
    except:
        print("Not JSON")
except Exception as e:
    print(f"Error: {e}")
