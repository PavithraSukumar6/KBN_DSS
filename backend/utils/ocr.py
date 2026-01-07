import pytesseract
from PIL import Image
import os

# NOTE: If Tesseract is not in your PATH, uncomment and set the path below:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(image_path):
    """
    Extracts text and average confidence score from an image file using OCR.
    Returns: (text, confidence_score)
    """
    try:
        # Open the image file
        img = Image.open(image_path)
        
        # Perform OCR with data (for confidence)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        # 'conf' is a list of confidence scores (-1 for no text)
        confidences = [int(c) for c in data['conf'] if c != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Reconstruct text
        text = " ".join([word for word in data['text'] if word.strip()])
        
        # Basic Quality Check
        if not text.strip():
            # Don't raise, just return empty with 0 confidence
            return "", 0.0
            
        return text, round(avg_confidence, 2)
    except pytesseract.TesseractNotFoundError:
        print("Tesseract not found. Skipping OCR.")
        return "OCR_SKIPPED", 0.0
    except Exception as e:
        if "tesseract is not installed" in str(e).lower() or "not in your path" in str(e).lower():
            print("Tesseract not found (generic error). Skipping OCR.")
            return "OCR_SKIPPED", 0.0
        print(f"Error during OCR: {e}")
        return f"[Error: OCR Failed - {str(e)}]", 0.0
