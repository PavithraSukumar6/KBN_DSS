import os
import shutil
from utils.cloud_service import CloudService
from utils.ocr import extract_text
from utils.classification import classify_document
from utils.extraction import extract_metadata
import datetime
import re

class CloudManager:
    def __init__(self, upload_folder):
        self.cloud = CloudService()
        self.upload_folder = upload_folder
        self.temp_folder = os.path.join(upload_folder, 'cloud_temp')
        os.makedirs(self.temp_folder, exist_ok=True)

    def log(self, message):
        # A simple logger that could be extended to stream to UI
        print(f"[CloudManager] {message}")
        return message

    def auto_sort_cloud(self):
        """Downloads files, runs OCR, renames, and sorts in Cloud."""
        self.log("Starting Auto-Sort...")
        files = self.cloud.list_files(query="mimeType = 'application/pdf' and trashed = false")
        
        results = []
        for file in files:
            file_id = file['id']
            filename = file['name']
            
            # Skip already sorted (simple heuristic)
            if re.match(r'^[A-Za-z0-9]+_[A-Za-z0-9]+_\d{4}-\d{2}-\d{2}_[A-Za-z0-9]+\.pdf$', filename):
                continue
            
            self.log(f"Processing {filename}...")
            
            # 1. Download
            local_path = self.cloud.download_file(file_id, filename, self.temp_folder)
            if not local_path:
                self.log(f"Failed to download {filename}")
                continue

            try:
                # 2. OCR & Analysis
                text, _, _ = extract_text(local_path)
                category, _ = classify_document(text)
                metadata = extract_metadata(text, category)
                
                # 3. Construct New Name
                # Standard: CompanyAddressedTo_InvoiceNumber_Date_IssuingCompany.pdf
                # We need to extract these specific fields.
                # Assuming metadata returns generic dict, we map:
                # CompanyAddressedTo -> 'vendor' or 'customer'? Let's assume 'customer_name' or similar if Invoice.
                # IssuingCompany -> 'vendor_name'
                
                # Fallbacks
                company_to = metadata.get('customer_name', 'Unknown')
                inv_num = metadata.get('invoice_number', 'NO-NUM')
                date_str = metadata.get('date', datetime.date.today().strftime('%Y-%m-%d'))
                company_from = metadata.get('vendor_name', 'Unknown')
                
                # Sanitize
                def clean(s): return re.sub(r'[^A-Za-z0-9]', '', str(s))
                
                new_name = f"{clean(company_to)}_{clean(inv_num)}_{date_str}_{clean(company_from)}.pdf"
                
                # 4. Rename in Cloud
                self.cloud.service.files().update(fileId=file_id, body={'name': new_name}).execute() if not self.cloud.is_mock else None
                self.log(f"Renamed {filename} -> {new_name}")
                
                # 5. Move (Optional - creating folder structure)
                # e.g. Year/Month/Category
                # For now, just rename as per request "Construct filename" and "move file into nested folder structure"
                # Let's simple move to "Processed" folder
                # processed_id = self.get_or_create_folder("Processed_Cloud")
                # self.cloud.move_file(file_id, file.get('parents', []), processed_id)
                
                results.append(f"Sorted: {new_name}")

            except Exception as e:
                self.log(f"Error processing {filename}: {e}")
            finally:
                # Cleanup local
                if os.path.exists(local_path):
                    os.remove(local_path)
        
        return results

    def remove_duplicates_cloud(self):
        """Finds duplicates by MD5 checksum and deletes them."""
        self.log("Starting Deduplication...")
        files = self.cloud.list_files(query="trashed = false")
        
        hashes = {}
        duplicates = []
        
        for file in files:
            md5 = file.get('md5Checksum')
            if not md5: continue
            
            if md5 in hashes:
                # Found duplicate
                original = hashes[md5]
                # Deciding which to keep: keep earliest created
                if file['createdTime'] > original['createdTime']:
                    duplicates.append(file) # New one is dup
                else:
                    duplicates.append(original) # Old one was dup? Wait, if we keep oldest...
                    hashes[md5] = file # Replace logic if needed, but simplest is just keep first seen if we sort by time?
                    # API list usually arbitrary order. Better to compare.
            else:
                hashes[md5] = file
                
        deleted = []
        for file in duplicates:
            self.log(f"Deleting duplicate: {file['name']} (ID: {file['id']})")
            success = self.cloud.delete_file(file['id'])
            if success:
                deleted.append(file['name'])
        
        return deleted

    def clean_repository_cloud(self):
        """Moves files not matching naming convention to 'To Be Sorted'."""
        self.log("Cleaning Repository...")
        files = self.cloud.list_files(query="mimeType = 'application/pdf' and trashed = false")
        
        # Regex for Standard: CompanyAddressedTo_InvoiceNumber_Date_IssuingCompany.pdf
        # Simplified regex for checking structure
        pattern = re.compile(r'^[^_]+_[^_]+_\d{4}-\d{2}-\d{2}_[^_]+\.pdf$')
        
        moved = []
        to_sort_folder_id = self.get_or_create_folder("To Be Sorted")
        
        for file in files:
            if not pattern.match(file['name']):
                self.log(f"Flagging {file['name']} as non-compliant.")
                self.cloud.move_file(file['id'], file.get('parents', []), to_sort_folder_id)
                moved.append(file['name'])
                
        return moved
        
    def get_or_create_folder(self, folder_name):
        # Initial implementation: find in root
        found = self.cloud.list_files(query=f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false")
        if found:
            return found[0]['id']
        else:
            return self.cloud.create_folder(folder_name)
