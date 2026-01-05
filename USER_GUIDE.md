# 📖 User Guide: Document Sorting System

Welcome to your new Document Sorting System! Here is how to use it.

## 1. Uploading Documents
*   Click the **Upload Document** section at the top.
*   Select a PDF or Image (JPG/PNG) from your computer.
*   Click **Upload & Process**.
*   **What happens next?**
    *   The system reads the text (OCR).
    *   It looks for keywords to decide if it's an *Invoice*, *Contract*, *ID*, etc.
    *   It saves the file and the data.

## 2. The Dashboard
*   Below the upload area, you will see the **Document Library**.
*   This list shows all your processed files.
*   **Columns**:
    *   *Filename*: Name of the file.
    *   *Category*: What the system thinks it is (e.g., Invoice).
    *   *Confidence*: How sure the system is (High/Medium/Low).
    *   *Status*: "Processed" means it's ready.

## 3. Searching
*   Use the **Search Bar** at the top of the library.
*   Type anything! You can search for:
    *   A filename (e.g., "receipt").
    *   A category (e.g., "Invoice").
    *   **Text inside the document** (e.g., if you uploaded a receipt for "Coffee", searching "Coffee" will find it!).

## 4. Troubleshooting
*   **"OCR Failed"**: The image might be too blurry or blank.
*   **"Upload Failed"**: Make sure the backend server (Python black window) is running.
