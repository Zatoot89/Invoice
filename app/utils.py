from flask import render_template
from weasyprint import HTML

def generate_invoice_pdf(invoice):
    """
    Generates a PDF for a given invoice object.
    """
    # Render the HTML template with the invoice data
    # The base_url is important for WeasyPrint to find static files like CSS
    html_string = render_template('invoice/pdf_template.html', invoice=invoice)

    # Use WeasyPrint to generate the PDF
    pdf = HTML(string=html_string).write_pdf()

    return pdf
