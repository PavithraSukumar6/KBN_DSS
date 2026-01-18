import requests
import time
import os
import shutil
import datetime

BASE_URL = "http://localhost:5000"

def test_autonaming():
    print("--- Starting Auto-Naming Test ---")
    
    # 1. Create dummy PNG with "Invoice" text (High Res)
    from PIL import Image, ImageDraw, ImageFont
    filename = "test_autonaming.png"
    # A4 size roughly at 200 DPI
    img = Image.new('RGB', (1600, 2200), color=(255, 255, 255))
    
    try:
        d = ImageDraw.Draw(img)
        # Draw large text manually by drawing simple shapes or larger scaling
        # We simulate "INVOICE" by drawing it multiple times to fake "bold/large"
        # Or better, just write "INVOICE" many times in a grid
        text = "INVOICE 12345"
        for y in range(100, 1000, 100):
            d.text((100, y), text, fill=(0,0,0))
            d.text((101, y), text, fill=(0,0,0)) # Fake bold
             
        # Add keywords and unique timestamp to avoid duplicate hash
        d.text((100, 1200), "TOTAL AMOUNT DUE: $500.00", fill=(0,0,0))
        d.text((100, 1300), f"DATE: 2026-01-15 {datetime.datetime.now()}", fill=(0,0,0))
    except Exception as e:
        print(f"Failed to draw text: {e}")
        
    img.save(filename)
    
    # 2. Upload
    print("Uploading file (PNG)...")
    files = {'file': open(filename, 'rb')}
    data = {'uploader_id': 'Tester'}
    res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    assert res.status_code == 200, f"Upload failed: {res.text}"
    doc = res.json()['documents'][0]
    doc_id = doc['id']
    print(f"File uploaded. ID: {doc_id}")
    
    # Wait for background processing (OCR + Auto-Rename)
    print("Waiting for background processing (15s)...")
    time.sleep(15)
    
    # 3. Verify
    # Fetch details
    res = requests.get(f"{BASE_URL}/documents/{doc_id}/details")
    data = res.json()
    
    # Expected: Category = Invoice (from content), Filename = Invoice_ID_Date.png
    expected_cat = "Invoice"
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    # Updated expectation: Relative path
    expected_name = f"processed/{today_str}/Invoice_{doc_id}_{today_str}.png"
    
    print(f"Details: Category={data.get('category')}, NAME={data.get('filename')}")
    
    # Check Category
    if data.get('category') != expected_cat:
        print(f"FAIL: Category mistmatch. Got {data.get('category')}, Expected {expected_cat}")
    else:
        print("SUCCESS: Category classified as Invoice.")
        
    # Check Filename
    if data.get('filename') != expected_name:
        print(f"FAIL: Filename mismatch. Got {data.get('filename')}, Expected {expected_name}")
    else:
        print("SUCCESS: Filename renamed correctly.")
        
    # Cleanup
    try:
        os.remove(filename)
    except: pass

if __name__ == "__main__":
    test_autonaming()
