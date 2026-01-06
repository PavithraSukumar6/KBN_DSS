
import sys
import os
import unittest
import sqlite3

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database.db import init_db, save_document, create_container, get_filtered_documents, get_db_connection

class TestQCVerification(unittest.TestCase):
    def setUp(self):
        # Initialize DB (safe to run on existing if using IF NOT EXISTS, 
        # but to test isolation we might want to check data carefully)
        # We will work with the live DB but use distinct IDs.
        pass

    def test_batch_filtering(self):
        print("\nTesting Batch Filtering...")
        
        # 1. Create a dummy batch ID directly (no need for table constraints for the filter check usually, 
        # but let's be proper)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Container
        cont_id = "TEST-CONT-VERIFY"
        try:
            cursor.execute("INSERT INTO containers (id, name) VALUES (?, ?)", (cont_id, "Test Verifier"))
        except sqlite3.IntegrityError:
            pass # Already exists
            
        # Create Batch
        cursor.execute("INSERT INTO batches (container_id, status) VALUES (?, 'Pending')", (cont_id,))
        batch_id_1 = cursor.lastrowid
        
        cursor.execute("INSERT INTO batches (container_id, status) VALUES (?, 'Pending')", (cont_id,))
        batch_id_2 = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # 2. Save Documents
        doc1_id = save_document("doc_b1_1.pdf", "Invoice", "90", "Content", batch_id=batch_id_1)
        doc2_id = save_document("doc_b1_2.pdf", "Invoice", "90", "Content", batch_id=batch_id_1)
        doc3_id = save_document("doc_b2_1.pdf", "Invoice", "90", "Content", batch_id=batch_id_2)
        
        print(f"Created Doc {doc1_id} (Batch {batch_id_1})")
        print(f"Created Doc {doc2_id} (Batch {batch_id_1})")
        print(f"Created Doc {doc3_id} (Batch {batch_id_2})")
        
        # 3. Verify Filters
        docs_b1 = get_filtered_documents(batch_id=batch_id_1)
        self.assertEqual(len(docs_b1), 2)
        self.assertTrue(all(d['batch_id'] == batch_id_1 for d in docs_b1))
        
        docs_b2 = get_filtered_documents(batch_id=batch_id_2)
        self.assertEqual(len(docs_b2), 1)
        self.assertEqual(docs_b2[0]['batch_id'], batch_id_2)
        
        print("SUCCESS: Batch ID filtering is working correctly.")

if __name__ == '__main__':
    unittest.main()
