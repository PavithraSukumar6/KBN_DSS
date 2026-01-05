# KBN Industrial Archives - Digitization Station

A comprehensive full-stack application for digitizing, classifying, and managing physical documents.

## Features

### 1. Digitization Pipeline
- **Drag & Drop Upload**: Support for PDF and Image uploads.
- **Automated splitting**: Large PDFs are automatically split into individual documents.
- **Background Processing**: OCR (Optical Character Recognition) runs asynchronously to keep the UI responsive.
- **Triage System**:
    - **Green**: High Confidence (>85%)
    - **Yellow**: Review Needed (70-85%)
    - **Red**: Low Confidence / Failed (<70%)

### 2. Quality Control (QC)
- **Batch Management**: Documents are grouped by batches.
- **QC Queue**: Dedicated interface for QA Specialists to review batch completeness and quality.
- **Audit Trail**: All approvals and rejections are logged.

### 3. Smart Classification & Data Extraction
- **Auto-tagging**: Invoices, Contracts, IDs, and Reports are automatically classified.
- **Metadata Extraction**:
    - **Invoices**: Extracts Vendor, Date, Total Amount.
    - **IDs**: Extracts ID Numbers.
    - **Contracts**: Extracts Party Names and Dates.
- **Reclassification**: Users can manually correct categories, which triggers automatic data re-extraction.

### 4. Search & Analytics
- **Advanced Search**: Filter by Category and Date Range.
- **CSV Export**: Download complete datasets including extracted metadata.
- **Analytics Dashboard**: Visual charts for Throughput, Category Distribution, and Success Rates.

---

## Setup Instructions

### Prerequisites
1.  **Node.js** (v16+)
2.  **Python** (v3.8+)
3.  **Tesseract OCR** (Must be installed on the system and accessible in path)

### Backend Setup
1.  Navigate to the backend folder:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install flask flask-cors pytesseract
    ```
3.  Run the server:
    ```bash
    python app.py
    ```
    *The server runs on http://localhost:5000*

### Frontend Setup
1.  Navigate to the frontend folder:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    npm install recharts
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    *The UI will be accessible at http://localhost:5173 (or similar)*

---

## Usage Guide

1.  **Intake**: Go to the "Admin / Intake" tab to create new Storage Containers (Boxes).
2.  **Operation**: In the "Operation" dashboard, select a container and drag files to upload.
3.  **Review**: Watch the status change from "Processing" to "Completed".
4.  **QC**: Go to "QC Queue" to approve batches.
5.  **Analytics**: Check the "Analytics" tab for daily progress.
