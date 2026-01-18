import unittest
import os
import shutil
import json
from utils.extraction import extract_invoice_metadata
from utils.renaming import process_rename_and_move

class TestWorkflowLogic(unittest.TestCase):
    
    def test_extraction_regex(self):
        text = """
        KBN Services
        123 Main St
        
        Bill To: Acme Corp
        
        Invoice #: INV-2025-001
        Date: 12-31-2025
        
        Total Amount: $500.00
        """
        
        data = extract_invoice_metadata(text)
        print("Extracted Data:", data)
        
        self.assertEqual(data.get('invoice_number'), 'INV-2025-001')
        self.assertEqual(data.get('date'), '12-31-2025')
        self.assertEqual(data.get('addressed_company'), 'Acme Corp')
        # Issuing company heuristic: First line
        self.assertEqual(data.get('issuing_company'), 'KBN Services')

    def test_renaming_logic(self):
        # Setup dummy file
        dummy_file = "test_doc.pdf"
        with open(dummy_file, 'w') as f:
            f.write("dummy content")
            
        base_folder = os.getcwd()
        # Create temp processed folder
        os.makedirs(os.path.join(base_folder, 'processed'), exist_ok=True)
        
        metadata = {
            'invoice_number': 'INV-2025-001',
            'date': '12-31-2025',
            'addressed_company': 'Acme Corp',
            'issuing_company': 'KBN Services'
        }
        
        # We need to mock DB connection in process_rename_and_move or handle the error
        # Since process_rename_and_move imports get_db_connection, it will fail if we don't mock it or validity of DB
        # However, for this test, we might just checking the string formatting and file move.
        # But the function writes to DB. I should probably skip DB part or mock it.
        # Let's import mock
        from unittest.mock import patch, MagicMock
        
        with patch('utils.renaming.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_db.return_value = mock_conn
            
            new_path = process_rename_and_move(123, dummy_file, 'Invoice', base_folder, metadata)
            
            print("New Path:", new_path)
            self.assertTrue(new_path)
            self.assertIn('AcmeCorp_INV-2025-001_12-31-2025_KBNServices.pdf', new_path)
            self.assertIn('KBNServices', new_path) # Check folder
            
            # clean up
            if os.path.exists(new_path):
                os.remove(new_path)
            # Remove nested dirs?
            # shutil.rmtree(os.path.join(base_folder, 'processed', 'KBNServices'))

if __name__ == '__main__':
    unittest.main()
