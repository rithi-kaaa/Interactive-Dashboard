import PDFReport
from fpdf import FPDF
from datetime import datetime
import traceback
import pandas as pd
from statistics import mean
from statistics import median
from typing import IO

def detect_outliers(dataframe, column):
    if column in dataframe.columns and not dataframe[column].empty:
        q1 = dataframe[column].quantile(0.25)
        q3 = dataframe[column].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return dataframe[(dataframe[column] < lower_bound) | (dataframe[column] > upper_bound)]
    return pd.DataFrame()  # Return empty DataFrame if column doesn't exist or is empty


def generate_charts(df, param):
    pass


def generate_pdf_report(data):
    # Convert data to pandas DataFrame
    df = pd.DataFrame(data)

    # Set default values for potential missing columns
    kWh_actual_with_sim = df.get('kWh_actual_with_sim', pd.Series([0]))
    Comp_Air_Totalized = df.get('Comp_Air_Totalized', pd.Series([0]))
    Water_Totalized = df.get('Water_Totalized', pd.Series([0]))

    # Create a PDF object
    pdf = PDFReport()
    pdf.add_page()

    # Executive Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)

    total_energy = kWh_actual_with_sim.sum()
    total_air = Comp_Air_Totalized.sum()
    total_water = Water_Totalized.sum()

    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f'Total Energy Consumed: {total_energy:.2f} kWh\n'
                          f'Total Compressed Air Used: {total_air:.2f} m³\n'
                          f'Total Water Used: {total_water:.2f} liters\n\n')

    # Aggregated Statistics
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Aggregated Statistics', 0, 1)
    pdf.set_font('Arial', '', 12)

    if not kWh_actual_with_sim.empty:
        pdf.multi_cell(0, 10, f'Energy Consumption (kWh)\n'
                              f'- Average: {mean(kWh_actual_with_sim):.2f}\n'
                              f'- Median: {median(kWh_actual_with_sim):.2f}\n'
                              f'- Maximum: {kWh_actual_with_sim.max():.2f}\n'
                              f'- Minimum: {kWh_actual_with_sim.min():.2f}\n\n')

    if not Comp_Air_Totalized.empty:
        pdf.multi_cell(0, 10, f'Compressed Air (m³)\n'
                              f'- Average: {mean(Comp_Air_Totalized):.2f}\n'
                              f'- Median: {median(Comp_Air_Totalized):.2f}\n'
                              f'- Maximum: {Comp_Air_Totalized.max():.2f}\n'
                              f'- Minimum: {Comp_Air_Totalized.min():.2f}\n\n')

    if not Water_Totalized.empty:
        pdf.multi_cell(0, 10, f'Water Usage (liters)\n'
                              f'- Average: {mean(Water_Totalized):.2f}\n'
                              f'- Median: {median(Water_Totalized):.2f}\n'
                              f'- Maximum: {Water_Totalized.max():.2f}\n'
                              f'- Minimum: {Water_Totalized.min():.2f}\n\n')

    # Detecting Outliers
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Anomalies Detected', 0, 1)
    outliers = detect_outliers(df, 'kWh_actual_with_sim')
    pdf.set_font('Arial', '', 12)
    if not outliers.empty:
        for index, row in outliers.iterrows():
            pdf.multi_cell(0, 10, f"Outlier Detected at {row.get('Time_Stamp', 'N/A')}\n"
                                  f"- Energy Consumption: {row['kWh_actual_with_sim']:.2f} kWh\n")
    else:
        pdf.multi_cell(0, 10, 'No anomalies detected in the energy consumption data.\n\n')

    # Top N highlights
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Top 5 Highest Energy Consumptions', 0, 1)
    if not df.empty:
        top_5_energy = df.nlargest(5, 'kWh_actual_with_sim')
        pdf.set_font('Arial', '', 12)
        for index, row in top_5_energy.iterrows():
            pdf.multi_cell(0, 10, f"Time: {row.get('Time_Stamp', 'N/A')}, Energy: {row['kWh_actual_with_sim']:.2f} kWh\n")

    # Visual Summaries - Charts
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Visual Summaries', 0, 1)

    # Add chart for energy consumption if the column exists
    if 'kWh_actual_with_sim' in df.columns:
        energy_chart = generate_charts(df, 'kWh_actual_with_sim')
        pdf.image(energy_chart, x=10, y=None, w=100)

    # Save PDF
    pdf_output = IO.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return pdf_output  # Return the PDF in binary format