import sqlite3
import datetime
import random
import uuid

DB_PATH = 'backend/documents.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    # Document Types
    doc_types = ['Invoice', 'Contract', 'Report', 'Application', 'Identification']

    # 1. Seed Active Documents for Library (Processed)
    print("\nSeeding Active Documents...")
    for i in range(15):
        filename = f"Demo_Doc_{i}_{random.randint(1000,9999)}.pdf"
        upload_date = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO documents (filename, upload_date, status, ocr_status, category, confidence, is_published, content, confidentiality_level)
            VALUES (?, ?, 'Active', 'Processed', ?, '0.95', 1, 'Dummy content', 'Internal')
        ''', (filename, upload_date, random.choice(doc_types)))

    # 2. Seed QC Queue Documents (Needs Review / Low Confidence)
    print("Seeding QC Queue Documents...")
    for i in range(5):
        filename = f"QC_Doc_{i}_{random.randint(1000,9999)}.png"
        upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO documents (filename, upload_date, status, ocr_status, category, confidence, is_published, content, confidentiality_level)
            VALUES (?, ?, 'Intake', 'Needs Review', ?, '0.65', 0, 'Unclear content', 'Internal')
        ''', (filename, upload_date, random.choice(doc_types)))

    # 3. Seed Analytics Data (Historical)
    print("Seeding Historical Data for Analytics...")
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    for i in range(50):
        filename = f"Hist_Doc_{i}_{random.randint(1000,9999)}.pdf"
        # Random date in last year
        random_days = random.randint(0, 365)
        upload_date = (start_date + datetime.timedelta(days=random_days)).strftime('%Y-%m-%d %H:%M:%S')
        
        status = 'Active'
        if random.random() < 0.2:
            status = 'Archived'
            
        cursor.execute('''
            INSERT INTO documents (filename, upload_date, status, ocr_status, category, confidence, is_published, content, confidentiality_level)
            VALUES (?, ?, ?, 'Processed', ?, '0.98', 1, 'History content', 'Internal')
        ''', (filename, upload_date, status, random.choice(doc_types)))

    conn.commit()
    conn.close()

    # 4. Seed a Batch for QC Queue
    print("Seeding QC Batch...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create Container
    container_id = "CONT-DEMO-QC"
    cursor.execute("INSERT OR IGNORE INTO containers (id, name, department, physical_page_count, barcode) VALUES (?, ?, 'Finance', 0, ?)", (container_id, "Demo Box", "BC-DEMO-001"))
    
    # Create Batch
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO batches (container_id, status, start_time, physical_page_count_expected) VALUES (?, 'Pending', ?, 5)", (container_id, start_time))
    batch_id = cursor.lastrowid
    
    # Link 5 documents to this batch
    for i in range(5):
        filename = f"Batch_Doc_{i}.pdf"
        cursor.execute("INSERT INTO documents (filename, container_id, batch_id, status, ocr_status, category, confidence, is_published, content) VALUES (?, ?, ?, 'Intake', 'Needs Review', 'Invoice', '0.70', 0, 'Batch Content')", (filename, container_id, batch_id))
        
    conn.commit()
    conn.close()
    print("Batch Seeding Complete.")

if __name__ == "__main__":
    seed_data()
