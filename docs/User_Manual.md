# KBN Document Sorting System - User Manual

## 1. Scan / Upload
To add documents to the system:
1. Navigate to the **Upload** tab.
2. **Drag & Drop** files (PDF, JPG, PNG) into the drop zone, or click to select them.
3. (Optional) Provide manual metadata overrides (Document Type, Department, Tags).
4. Click **Upload**.
   - Result: Documents enter the "Processing" state. The standard OCR engine extracts text automatically.
   - **Fast Track**: Enable "Fast Track" for priority processing.

**Direct Scan**:
- To use a physical scanner, ensure it is connected and recognized by Windows.
- Click "Direct Scan" (if available) to pull an image directly from the device.

## 2. Search
To find documents:
1. Use the **Global Search Bar** at the top.
   - Enter keywords (e.g., "Invoice 2024").
   - Results appear instantly in the main dashboard.
2. **Filters**:
   - Filter by **Category** (ID, Invoice, HR).
   - Filter by **Status** (Processing, Completed, Review).

**Tip**: The system uses Full-Text Search (FTS), so you can search for content *inside* the documents, not just filenames.

## 3. Audit & Security
The **Audit Center** tracks all actions for compliance.

### Viewing Logs
- Navigate to the **Audit Center** tab.
- View a chronological list of actions:
  - **VIEW**: Who opened a document.
  - **UPLOAD**: Who added a file.
  - **UPDATE**: Metadata changes.
  - **SECURITY**: Restricted access attempts.

### Security Features
- **Least Privilege**: Only authorized users can see restricted documents.
- **Audit Lock**: Log entries cannot be deleted or modified, even by Admins.
- **Legal Hold**: If enabled by Admin, no documents can be deleted system-wide.

## 4. Taxonomy & Governance
- **Governance Tab**: Manage Document Types and Departments.
- **Versioning**: Edit an existing term to create a new version (e.g., v1 -> v2) while preserving history.
- **Retention**: Set how many years a document type is kept before auto-archiving.
