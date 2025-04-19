import streamlit as st
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import os

class PDF(FPDF):
    pass

def generate_pdf(customer_name, transactions, company_name, loan_date):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Set default font
    pdf.set_font("Helvetica", size=10)

    # Static logo
    logo_path = "logo.png"
    try:
        pdf.image(logo_path, x=10, y=8, w=50, h=15)
    except:
        st.warning("Static logo file not found or unreadable.")

    # Account Info
    account_number = "843222126"
    statement_date = datetime.now().strftime("%Y/%m/%d")

    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, f"Account Number: {account_number}", ln=True, align='R')
    pdf.cell(0, 5, f"Statement Date: {statement_date}", ln=True, align='R')

    pdf.ln(12)  # Increased space below logo

    # Icons path
    icon_address = "icon_address.png"
    icon_phone = "icon_phone.png"
    icon_email = "icon_email.png"

    # Uniform icon height and vertical spacing
    icon_w = 5
    line_h = 6
    label_x = 20
    icon_x = 10

    # Contact details with icons
    y = pdf.get_y()
    try: pdf.image(icon_address, x=icon_x, y=y, w=icon_w)
    except: pass
    pdf.set_xy(label_x, y)
    pdf.cell(0, line_h, "98 Spaanriet Street, The Reeds Ext 45, 0156", ln=True)

    y = pdf.get_y()
    try: pdf.image(icon_phone, x=icon_x, y=y, w=icon_w)
    except: pass
    pdf.set_xy(label_x, y)
    pdf.cell(0, line_h, "(012) 006 0019", ln=True)

    y = pdf.get_y()
    try: pdf.image(icon_email, x=icon_x, y=y, w=icon_w)
    except: pass
    pdf.set_xy(label_x, y)
    pdf.cell(0, line_h, "info@ntirhisano.com", ln=True)

    pdf.ln(10)

    # Watermark
    watermark_path = "transparent_watermark.png"
    if os.path.exists(watermark_path):
        try:
            # Add transparent watermark using alpha support (only with PNG transparency)
            pdf.image(watermark_path, x=30, y=60, w=150, h=150, type="PNG")
        except:
            st.warning("Watermark image file not found or unreadable.")

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 12, "STATEMENT OF ACCOUNT", ln=True, align='C')

    # Orange separator line
    pdf.set_draw_color(204, 85, 0)
    pdf.set_line_width(1.0)
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, customer_name, ln=True, align='C')
    pdf.ln(10)

    # Table headers
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.25)
    pdf.cell(30, 10, "Date", border=1, align='C', fill=True)
    pdf.cell(65, 10, "Description", border=1, align='C', fill=True)
    pdf.cell(30, 10, "Charges", border=1, align='C', fill=True)
    pdf.cell(30, 10, "Credits", border=1, align='C', fill=True)
    pdf.cell(35, 10, "Balance", border=1, align='C', fill=True)
    pdf.ln()

    # Transactions
    pdf.set_font("Helvetica", size=10)
    balance = 0
    def fmt(x): return f"{x:,.2f}R".replace(",", " ").replace(".", ",")

    for idx, row in transactions.iterrows():
        date = row['Date'].strftime('%Y/%m/%d')
        desc = str(row['Description'])
        amount = row['Amount']
        charge = amount if amount > 0 else 0
        credit = -amount if amount < 0 else 0
        balance += amount

        # Transparent background: set fill to white and do not use fill=True
        pdf.cell(30, 8, date, border=1)
        pdf.cell(65, 8, desc[:32], border=1)
        pdf.cell(30, 8, fmt(charge) if charge else "", border=1, align='R')
        pdf.cell(30, 8, fmt(credit) if credit else "", border=1, align='R')
        pdf.cell(35, 8, fmt(balance), border=1, align='R')
        pdf.ln()

    # Summary row
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(155, 8, "Outstanding Balance", border=1, align='R', fill=True)
    pdf.cell(35, 8, fmt(balance), border=1, align='R', fill=True)
    pdf.ln(10)

    # Notes and instructions
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "*Penalty fee charged at 10% per month of the total outstanding")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", size=10)
    pdf.cell(0, 8, "Payment Instruction", ln=True)

    pdf.set_font("Helvetica", size=10)
    pdf.set_x(15)
    pdf.cell(0, 8, "Bank: First National Bank", ln=True)
    pdf.set_x(15)
    pdf.cell(0, 8, "Account number: 62875263221", ln=True)
    pdf.set_x(15)
    pdf.cell(0, 8, "Branch number: 255355", ln=True)

    pdf_filename = f"Statement_{customer_name.replace(' ', '_')}.pdf"
    pdf.output(pdf_filename)
    return pdf_filename

def generate_excel(customer_name, transactions):
    excel_filename = f"Statement_{customer_name}.xlsx"
    transactions.to_excel(excel_filename, index=False)
    return excel_filename


# Streamlit UI
st.title("Loan Statement Generator")

customer_name = st.text_input("Enter Customer Name:")
company_name = "Ntirhisano Venture Capital"

if customer_name:
    st.write("Upload an Excel or CSV file containing loan transactions.")
    uploaded_file = st.file_uploader("Upload File", type=["xls", "xlsx", "csv"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # File validation
        required_columns = ['Company', 'Date', 'Amount', 'Description']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Error: The uploaded file must contain the following columns: {', '.join(required_columns)}.")
            df = pd.DataFrame()

        # Handling missing data
        df = df.dropna(subset=['Date', 'Company'])
        if df.empty:
            st.error("Error: The uploaded file contains missing or invalid data.")
            df = pd.DataFrame()

        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            if df['Date'].isnull().any():
                st.error("Error: Some dates are invalid or missing.")
                df = pd.DataFrame()

            st.write("### Preview of Uploaded Data")
            st.dataframe(df.head())

            filtered_df = df[df['Company'] == customer_name]
            filtered_df = filtered_df.sort_values(by="Date")

            # Date range validation
            loan_date = df['Date'].min()
            start_date = st.date_input("Start Date", loan_date)
            end_date = st.date_input("End Date", df['Date'].max())
            
            if start_date > end_date:
                st.error("Start Date cannot be later than End Date.")
            else:
                filtered_df = filtered_df[
                    (filtered_df['Date'] >= pd.to_datetime(start_date)) &
                    (filtered_df['Date'] <= pd.to_datetime(end_date))
                ]

            if not filtered_df.empty:
                st.write("### Filtered Data for Company Name:")
                st.dataframe(filtered_df)

            if st.button("Generate Statement"):
                if customer_name:
                    pdf_file = generate_pdf(customer_name, filtered_df, company_name, loan_date)
                    with open(pdf_file, "rb") as f:
                        st.download_button("Download Statement PDF", f, file_name=pdf_file, mime="application/pdf")

                    excel_file = generate_excel(customer_name, filtered_df)
                    with open(excel_file, "rb") as f:
                        st.download_button("Download Statement Excel", f, file_name=excel_file, mime="application/vnd.ms-excel")
                else:
                    st.error("Please enter a customer name before generating a statement.")
