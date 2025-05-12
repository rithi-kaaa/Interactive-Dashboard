from fpdf import FPDF
from datetime import datetime
import traceback

class PDF(FPDF):
    def header(self):
        # Add a logo
        self.image('logo.png', 10, 8, 33)  # Adjust the path, position, and size as necessary
        self.set_font('Arial', 'B', 12)
        # Title
        self.cell(80)
        self.cell(30, 10, 'Carbon Emission Report', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        # Go to 1.5 cm from the bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def add_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(10)

    def add_subheading(self, text):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, text, 0, 1, 'L')
        self.ln(4)

    def add_paragraph(self, text):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, text)
        self.ln()

    def add_table(self, headers, data):
        # Set font for table headers
        self.set_font('Arial', 'B', 12)
        for header in headers:
            self.cell(40, 10, header, 1)
        self.ln()

        # Set font for table data
        self.set_font('Arial', '', 12)
        for row in data:
            for item in row:
                self.cell(40, 10, str(item), 1)
            self.ln()

def generate_pdf_report(data):
    try:
        pdf = PDF()
        pdf.add_page()

        # Add Title
        pdf.add_title("Carbon Emission Summary Report")

        # Add Date
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.add_subheading(f"Report Generated On: {report_date}")

        # Add Section Header
        pdf.add_subheading("Machine Resources Data")

        # Add Table with data from the database
        headers = ['Time Stamp', 'Air (Totalized)', 'Water (Totalized)', 'Energy (kWh)']
        formatted_data = [
            [data[0], data[2], data[3], data[4]],  # Assuming data structure matches the database schema
        ]
        pdf.add_table(headers, formatted_data)

        # Add a Paragraph for additional details
        pdf.add_paragraph("This report summarizes the carbon emissions based on machine resources data. "
                          "It includes information on air pressure, water usage, and energy consumption during the machine's operations.")

        # Save the PDF to a file
        pdf_file_path = 'carbon_emission_report.pdf'
        pdf.output(pdf_file_path)
        print("PDF report generated successfully at:", pdf_file_path)
        return pdf_file_path

    except Exception as e:
        print("Failed to generate PDF report:", str(e))
        traceback.print_exc()  # This will print the stack trace
        return None
