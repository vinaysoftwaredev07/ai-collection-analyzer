from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PIL import Image, ImageDraw, ImageFont
import os

# Create media/samples directory if it doesn't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, 'media', 'samples')
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Data for PDF (Formal Collection Notice)
pdf_text = [
    "--- COLLECTION NOTICE ---",
    "Date: October 15, 2026",
    "",
    "Borrower Name: Jane Doe",
    "Account Status: Delinquent",
    "Days Past Due: 45",
    "Amount Owed: 1250.75",
    "Prior Payment Behavior: Frequent late payments, usually resolved within 30 days.",
    "Hardship Indicator: True (Medical leave reported last month)",
    "Preferred Communication Channel: Email",
    "",
    "Please contact us immediately to discuss repayment options."
]

# Generate PDF
pdf_path = os.path.join(SAMPLES_DIR, "sample_borrower_notice.pdf")
c = canvas.Canvas(pdf_path, pagesize=letter)
c.setFont("Helvetica-Bold", 14)
c.drawString(1 * inch, 10 * inch, "Biz2X Collections Department")
c.setFont("Helvetica", 12)
y = 9 * inch
for line in pdf_text:
    c.drawString(1 * inch, y, line)
    y -= 0.25 * inch
c.save()
print(f"Generated PDF: {pdf_path}")

# Data for Image (Internal Profile Screenshot)
img_text = [
    "INTERNAL BORROWER PROFILE",
    "-------------------------",
    "Name: John Smith",
    "DPD (Days Past Due): 90",
    "Amount Owed: 4500.00",
    "Prior Behavior: Never missed a payment until 3 months ago.",
    "Hardship Indicator: False",
    "Preferred Channel: SMS",
    "-------------------------",
    "Action Required: High Risk Escalation"
]

# Generate Image
img_path = os.path.join(SAMPLES_DIR, "sample_borrower_profile.jpg")
# Create a white image
img = Image.new('RGB', (600, 400), color='white')
draw = ImageDraw.Draw(img)

# Fallback font in case standard fonts are not available
try:
    font = ImageFont.truetype("arial.ttf", 20)
except IOError:
    font = ImageFont.load_default()

y = 20
for line in img_text:
    draw.text((20, y), line, font=font, fill='black')
    y += 30

img.save(img_path)
print(f"Generated Image: {img_path}")
