import fitz  # PyMuPDF
import os

def split_pdf(file_path, output_dir):
    """
    Converts a PDF file into individual image files (one per page).
    Returns a list of file paths to the generated images.
    """
    try:
        doc = fitz.open(file_path)
        output_files = []
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Zoom = 2.0 -> 144 DPI (approx) good for OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            
            output_filename = f"{base_name}_page_{i+1}.png"
            output_path = os.path.join(output_dir, output_filename)
            
            pix.save(output_path)
            output_files.append(output_path)
            
        doc.close()
        return output_files
        
    except Exception as e:
        print(f"Error splitting PDF {file_path}: {e}")
        return []

def detect_separators(file_path):
    """
    Placeholder for separator detection.
    Returns a list of page numbers where separators are found.
    """
    return []
