from PIL import Image, ImageDraw, ImageFont
import os

def create_test_invoice():
    # Create white image
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()
    
    # Draw Text
    d.text((50, 50), "INVOICE #INV-2025-001", fill=(0,0,0), font=header_font)
    d.text((50, 120), "Date: 2025-01-06", fill=(0,0,0), font=font)
    d.text((50, 150), "To: KBN Group - Finance Dept", fill=(0,0,0), font=font)
    d.text((50, 180), "Department: FINANCE", fill=(0,0,0), font=font)
    
    d.text((50, 250), "Description              Amount", fill=(0,0,0), font=font)
    d.line((50, 280, 750, 280), fill=(0,0,0), width=2)
    
    d.text((50, 300), "Consulting Services      $5,000.00", fill=(0,0,0), font=font)
    d.text((50, 330), "Software License         $1,200.00", fill=(0,0,0), font=font)
    
    d.line((50, 400, 750, 400), fill=(0,0,0), width=2)
    d.text((50, 420), "Total:                   $6,200.00", fill=(0,0,0), font=header_font)
    
    # Save
    path = os.path.join(os.getcwd(), 'test_invoice.png')
    img.save(path)
    print(f"Created {path}")

if __name__ == "__main__":
    create_test_invoice()
