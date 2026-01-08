
import requests
import json
import uuid

url = 'http://localhost:5000/containers'
data = {
    'id': f"CONT-{uuid.uuid4().hex[:6].upper()}",
    'name': 'Test_QA_Container',
    'subsidiary': 'KBN Group',
    'department': 'QA_Testing',
    'function': 'Testing',
    'confidentiality_level': 'Internal',
    'created_by': 'Admin_Test_Bot',
    'physical_page_count': 0
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
