import pytesseract
from PIL import Image, ImageStat
import os

# NOTE: If Tesseract is not in your PATH, uncomment and set the path below:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

def extract_text(image_path):
    """
    Extracts text and average confidence score from an image file using OCR.
    Returns: (text, confidence_score, confidence_reason)
    """
    try:
        # 1. Handle PDFs First
        if image_path.lower().endswith('.pdf'):
            if not PyPDF2:
                # Fallback or Error if lib missing
                return "", 0.0, "OCR Error: PyPDF2 library not installed on server"
            
            try:
                # Try Digital PDF Extraction
                text = ""
                with open(image_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + " "
                
                if text.strip():
                     return text.strip(), 100.0, "Digital PDF (Perfect)"
                else:
                     return "", 0.0, "Scanned PDF - OCR requires hosting update"
            except Exception as e:
                 print(f"PDF Error: {e}")
                 return "", 0.0, f"PDF Process Failed: {str(e)}"

        # 2. Handle Images
        # Open the image file
        img = Image.open(image_path)
        
        # Save debug image
        img.save("debug_ocr.png")

        # Perform OCR with data (for confidence)
        # Using PSM 3 (Auto) as requested
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config='--psm 3')
        
        # Calculate average confidence
        
        # Calculate average confidence
        # 'conf' is a list of confidence scores (-1 for no text)
        valid_confs = []
        for i, conf in enumerate(data['conf']):
            # conf can be int or string depending on tesseract version/wrapper
            try:
                conf_val = int(conf)
            except ValueError:
                conf_val = -1
                
            text_val = data['text'][i]
            
            # Filter out background (conf -1) and empty text
            if conf_val != -1 and text_val.strip():
                valid_confs.append(conf_val)
                
        avg_confidence = sum(valid_confs) / len(valid_confs) if valid_confs else 0
        final_conf = round(avg_confidence, 2)
        
        # Reconstruct text
        text = " ".join([word for word in data['text'] if word.strip()])
        
        # Basic Quality Check
        if not text.strip():
            # Bug 3 Fix: Explicitly flag 0-conf inputs as valid but requiring review
            return "", 0.0, "Requires Review (No Text)"
            
        reason = None
        # FR-32: Confidence Reason Logic
        if final_conf < 70:
            # Bug 3 Fix: Ensure reasons trigger QC in frontend
            if final_conf == 0:
                 reason = "Requires Review (Confidence 0%)"
            # 1. Low Resolution Check
            elif img.width < 1500:
                reason = 'Low Resolution'
            else:
                # 2. Noise/Garbage Check (Ratio of special chars)
                import re
                alphanumeric = len(re.sub(r'[^a-zA-Z0-9]', '', text))
                total_chars = len(text.replace(" ", ""))
                if total_chars > 0 and (alphanumeric / total_chars) < 0.5:
                     reason = 'Noise/Garbage Detected'
                else:
                    # 3. Poor Contrast Check
                    # Simple heuristic: Standard Deviation of pixel intensity
                    # Low std dev means flat/grey image.
                    stat = ImageStat.Stat(img.convert('L'))
                    std_dev = stat.stddev[0]
                    # Threshold logic: < 30 is usually very low contrast
                    if std_dev < 30:
                        reason = 'Poor Contrast'
                    else:
                        # 4. Default
                        reason = 'Complex Layout/Handwriting'
            
        return text, final_conf, reason

    except pytesseract.TesseractNotFoundError:
        print("Tesseract not found. Skipping OCR.")
        return "OCR_SKIPPED", 0.0, "Tesseract Missing"
    except Exception as e:
        if "tesseract is not installed" in str(e).lower() or "not in your path" in str(e).lower():
            print("Tesseract not found (generic error). Skipping OCR.")
            return "OCR_SKIPPED", 0.0, "Tesseract Missing"
        print(f"Error during OCR: {e}")
        return f"[Error: OCR Failed - {str(e)}]", 0.0, f"Error: {str(e)}"
