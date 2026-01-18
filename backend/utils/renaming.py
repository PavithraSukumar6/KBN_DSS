import os
import shutil
import uuid
from datetime import datetime
from database.db import get_db_connection, log_audit

def process_rename_and_move(doc_id, current_path, doc_type, base_folder, metadata=None):
    """
    Renames the file to [CompanyAddressedTo]_[InvoiceNumber]_[Date]_[IssuingCompany].ext 
    and moves it to processed/[IssuingCompany]/[Date]/ folder.
    Updates the database with the new path and filename.
    """
    try:
        if not os.path.exists(current_path):
            print(f"File not found for renaming: {current_path}")
            return False

        # 1. Prepare new name and path
        ext = os.path.splitext(current_path)[1]
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Default components
        company_to = "Unknown"
        invoice_num = f"{doc_id}" # Fallback
        doc_date = today_str
        issuing_company = "Unknown"

        if metadata and isinstance(metadata, dict):
            # Sanitize function
            def clean(s):
                if not s: return ""
                return "".join([c for c in s if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '')

            # Extract fields
            if metadata.get('addressed_company'):
                company_to = clean(metadata.get('addressed_company')) or "Unknown"
            
            if metadata.get('invoice_number'):
                invoice_num = clean(str(metadata.get('invoice_number')))
                
            if metadata.get('date'):
                # Try to normalize date to YYYY-MM-DD if possible, else just clean it
                d_raw = clean(metadata.get('date'))
                # formatting logic could go here, for now just clean
                doc_date = d_raw or today_str
            
            if metadata.get('issuing_company'):
                issuing_company = clean(metadata.get('issuing_company')) or "Unknown"

        # Construct Filename
        # Format: CompanyAddressedTo_InvoiceNumber_Date_IssuingCompany.pdf
        # If any are unknown to keep it clean? 
        # Request says: CompanyAddressedTo_InvoiceNumber_Date_IssuingCompany.pdf
        new_filename = f"{company_to}_{invoice_num}_{doc_date}_{issuing_company}{ext}"
        
        # Destination: processed/IssuingCompany/YYYY-MM-DD/ (Hierarchical Sorting)
        # If IssuingCompany is Unknown, maybe just processed/Unknown/YYYY-MM-DD/ or just processed/YYYY-MM-DD/
        # Let's use IssuingCompany folder
        processed_dir = os.path.join(base_folder, 'processed', issuing_company, today_str)
        os.makedirs(processed_dir, exist_ok=True)
        
        new_path = os.path.join(processed_dir, new_filename)
        
        # 2. Move File
        # Handle collision
        if os.path.exists(new_path):
            base, extension = os.path.splitext(new_filename)
            new_filename = f"{base}_{uuid.uuid4().hex[:4]}{extension}"
            new_path = os.path.join(processed_dir, new_filename)

        shutil.move(current_path, new_path)
        print(f"Renamed/Moved to {new_path}")
        
        # 3. Update Database
        # Relative path for DB (using forward slashes)
        relative_filename = f"processed/{issuing_company}/{today_str}/{new_filename}"
        
        conn = get_db_connection()
        conn.execute("UPDATE documents SET filename = ?, category = ? WHERE id = ?", 
                     (relative_filename, doc_type, doc_id))
        conn.commit()
        conn.close()
        
        # 4. Log Audit
        log_audit('document', doc_id, 'AUTO_ORGANIZE', f"Renamed to {new_filename} and moved to {issuing_company}/{today_str}", "System")
        
        return new_path
        
    except Exception as e:
        print(f"Error in renaming/moving: {e}")
        return False
        
    except Exception as e:
        print(f"Error in renaming/moving: {e}")
        return False
