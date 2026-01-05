import requests
import os
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:5000"

def seed_data():
    # 1. Create a container (Confidential)
    container_data = {
        "id": "TEST-CONF-001",
        "subsidiary": "KBN North",
        "department": "HR",
        "function": "Payroll",
        "date_range": "2023",
        "confidentiality_level": "Confidential",
        "source_location": "Main Vault",
        "created_by": "Gokul_Admin"
    }
    res = requests.post(f"{BASE_URL}/containers", json=container_data)
    if res.status_code in [201, 409]:
        print("Container created or already exists.")
    else:
        print(f"Failed to create container: {res.text}")
        return

    # 2. Create a dummy image
    dummy_image = "test_confidential.png"
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "CONFIDENTIAL TEST DOCUMENT", fill=(255, 255, 0))
    img.save(dummy_image)

    # 3. Upload the document
    with open(dummy_image, "rb") as f:
        files = {"file": (dummy_image, f, "image/png")}
        data = {
            "container_id": "TEST-CONF-001",
            "uploader_id": "Gokul_Admin",
            "tags": "test,confidential"
        }
        res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        if res.status_code == 200:
            print("Document uploaded successfully.")
        else:
            print(f"Upload failed: {res.text}")

if __name__ == "__main__":
    seed_data()
