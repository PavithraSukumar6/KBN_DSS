from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "This is a digital PDF test file.")
    c.drawString(100, 730, "It contains perfect text for OCR extraction.")
    c.drawString(100, 710, "Classification: Invoice")
    c.save()

if __name__ == "__main__":
    create_pdf("test_digital.pdf")
    print("Created test_digital.pdf")
