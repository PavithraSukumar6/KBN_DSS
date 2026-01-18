import sys
import os

# Add backend to path so we can import utils
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils.ocr import extract_text

def test_ocr():
    image_path = 'test_invoice.png'
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    # Clean up old debug file if exists
    if os.path.exists("debug_ocr.png"):
        os.remove("debug_ocr.png")

    print(f"Running OCR on {image_path}...")
    text, confidence = extract_text(image_path)
    
    print(f"Confidence Score: {confidence}")
    # print(f"Extracted Text (first 100 chars): {text[:100]}...")

    if os.path.exists("debug_ocr.png"):
        print("SUCCESS: debug_ocr.png was created.")
    else:
        print("FAILURE: debug_ocr.png was NOT created.")

    if confidence > 50:
         print("SUCCESS: Confidence score is reasonable (> 50).")
    elif confidence > 0:
         print(f"WARNING: Confidence score is low ({confidence}), but non-zero. The fix might be working partially or the image is poor quality.")
    else:
         print("FAILURE: Confidence score is 0.")

if __name__ == "__main__":
    test_ocr()
