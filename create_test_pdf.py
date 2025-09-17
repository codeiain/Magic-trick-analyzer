#!/usr/bin/env python3
"""Create a simple test PDF with readable text."""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

def create_test_pdf():
    filename = "test_text.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Add some text that OCR can easily read
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Magic Trick Test Document")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "This is a test PDF file for the OCR service.")
    c.drawString(100, 680, "The quick brown fox jumps over the lazy dog.")
    c.drawString(100, 660, "Magic tricks require practice and dedication.")
    c.drawString(100, 640, "Card tricks are among the most popular illusions.")
    
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_test_pdf()