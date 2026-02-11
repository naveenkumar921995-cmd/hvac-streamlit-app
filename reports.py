from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table
from database import get_connection
import pandas as pd

def generate_pdf():
    conn = get_connection()
    assets = pd.read_sql("SELECT * FROM assets", conn)
    conn.close()

    file_name = "Monthly_Report.pdf"
    doc = SimpleDocTemplate(file_name)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("DLF Cyber Park - Monthly Report", styles['Title']))
    elements.append(Spacer(1, 0.5 * inch))

    data = [assets.columns.tolist()] + assets.values.tolist()
    table = Table(data)
    elements.append(table)

    doc.build(elements)
    return file_name
