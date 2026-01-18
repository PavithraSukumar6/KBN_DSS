import unittest
from unittest.mock import MagicMock, patch
from PIL import Image, ImageStat
import os
import sys

# Add backend path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from utils import ocr

class TestConfidenceReason(unittest.TestCase):
    
    @patch('utils.ocr.pytesseract.image_to_data')
    @patch('utils.ocr.Image.open')
    def test_low_resolution(self, mock_open, mock_data):
        # Mock Image
        mock_img = MagicMock()
        mock_img.width = 1000 # < 1500
        mock_img.size = (1000, 1000)
        mock_open.return_value = mock_img
        
        # Mock OCR Data (Low confidence)
        mock_data.return_value = {
            'conf': [50, 50, 50],
            'text': ['hello', 'world', 'test']
        }
        
        text, conf, reason = ocr.extract_text("dummy.png")
        self.assertEqual(reason, 'Low Resolution')
        print(f"Low Resolution Test: Passed (Reason: {reason})")

    @patch('utils.ocr.pytesseract.image_to_data')
    @patch('utils.ocr.Image.open')
    def test_garbage_noise(self, mock_open, mock_data):
        # Mock Image (High Res)
        mock_img = MagicMock()
        mock_img.width = 2000
        mock_open.return_value = mock_img
        
        # Mock OCR Data (Garbage text)
        mock_data.return_value = {
            'conf': [50, 50, 50],
            'text': ['@#$%', '&*()', 'test'] # mostly garbage
        }
        
        text, conf, reason = ocr.extract_text("dummy.png")
        self.assertEqual(reason, 'Noise/Garbage Detected')
        print(f"Noise Test: Passed (Reason: {reason})")

    @patch('utils.ocr.pytesseract.image_to_data')
    @patch('utils.ocr.Image.open')
    @patch('utils.ocr.ImageStat.Stat')
    def test_poor_contrast(self, mock_stat, mock_open, mock_data):
        # Mock Image (High Res)
        mock_img = MagicMock()
        mock_img.width = 2000
        mock_open.return_value = mock_img
        
        # Mock Contrast (Low std dev)
        mock_stat_obj = MagicMock()
        mock_stat_obj.stddev = [10] # < 30
        mock_stat.return_value = mock_stat_obj
        
        # Mock OCR Data (Normal text)
        mock_data.return_value = {
            'conf': [50, 50, 50],
            'text': ['Normal', 'Text', 'Here']
        }
        
        text, conf, reason = ocr.extract_text("dummy.png")
        self.assertEqual(reason, 'Poor Contrast')
        print(f"Contrast Test: Passed (Reason: {reason})")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
