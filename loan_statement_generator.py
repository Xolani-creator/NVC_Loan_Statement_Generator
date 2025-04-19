import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

def generate_pdf(customer_name, transactions, company_name, logo_path, initial_balance, loan_date):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if logo_path:
        try:
            pdf.image(logo_path, x=10, y=8, w=30)
        except:
            st.warning("Invalid logo file format or missing file.")
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, company_name, ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"Statement of Account - {customer_name}", ln=True, align='C')
    pdf.ln(10)
    
    # Add the initial balance in the first row
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Loan Amount: {initial_balance:.2f} on {loan_date.strftime('%Y-%m-%d')}", ln=True, align='L')
    pdf.ln(5)
    
    # Table headers
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Date", border=1, align='C')
    pdf.cell(80, 10, "Description", border=1, align='C')
    pdf.cell(40, 10, "Amount", border=1, align='C')
    pdf.cell(40, 10, "Balance", border=1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", size=12)
    balance = initial_balance  # Set the initial balance
    for _, row in transactions.iterrows():
        # Amount can be from 'Debit' or 'Credit'
        amount = row['Amount']
        balance += amount
        
        pdf.cell(40, 10, row['Date'].strftime("%Y-%m-%d"), border=1)
        pdf.cell(80, 10, row['Description'], border=1)
        pdf.cell(40, 10, f"{amount:.2f}", border=1, align='R')
        pdf.cell(40, 10, f"{balance:.2f}", border=1, align='R')
        pdf.ln()
    
    pdf_filename = f"Statement_{customer_name}.pdf"
    pdf.output(pdf_filename)
    return pdf_filename

def generate_excel(customer_name, transactions):
    excel_filename = f"Statement_{customer_name}.xlsx"
    transactions.to_excel(excel_filename, index=False)
    return excel_filename

# Title of the web page
st.title("Loan Statement Generator")

# Get Customer Name upfront
customer_name = st.text_input("Enter Customer Name:")

# Define Company Name (Fixed)
company_name = "Ntirhisano Venture Capital"

if customer_name:
    # Now allow the user to upload data
    st.write("Upload an Excel or CSV file containing loan transactions.")
    uploaded_file = st.file_uploader("Upload File", type=["xls", "xlsx", "csv"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Standardize columns
        if 'Company' not in df.columns:
            st.error("Error: The uploaded file must contain a 'Company' column.")
        else:
            # Assuming 'Debit' and 'Credit' columns exist, combine them into 'Amount'
            if 'Debit' in df.columns and 'Credit' in df.columns:
                df['Amount'] = df['Debit'].fillna(0) - df['Credit'].fillna(0)  # Debits as negative, Credits as positive
            elif 'Debit' in df.columns:
                df['Amount'] = df['Debit'].fillna(0)  # Only Debit column
            elif 'Credit' in df.columns:
                df['Amount'] = df['Credit'].fillna(0)  # Only Credit column
            else:
                st.error("Error: The uploaded file must contain either 'Debit' or 'Credit' columns.")
                df = pd.DataFrame()  # Clear the dataframe if no valid columns exist
        
        if not df.empty:
            # Make sure we have the required columns
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert 'Date' to datetime
            if df['Date'].isnull().any():
                st.error("Error: Some dates are invalid or missing.")
                df = pd.DataFrame()  # Clear the dataframe if dates are invalid
            
            st.write("### Preview of Uploaded Data")
            st.dataframe(df.head())
            
            # Filter the dataframe by company name from the "Company" column
            filtered_df = df[df['Company'] == customer_name]
            filtered_df = filtered_df.sort_values(by = "Date")
            
            if not filtered_df.empty:
                st.write("### Filtered Data for Company Name:")
                st.dataframe(filtered_df)
            
            logo_file = st.file_uploader("Upload Company Logo (Optional)", type=["png", "jpg", "jpeg"])
            logo_path = None
            if logo_file:
                logo_path = "uploaded_logo.png"
                with open(logo_path, "wb") as f:
                    f.write(logo_file.read())
            
            # Automatically extract loan amount, interest rate, and fees from the data
            loan_amount = df[df['Description'].str.contains("Loan Amount", case=False)]['Amount'].sum()
            
            # Extract interest rate from the column labeled 'rate'
            if 'rate' in df.columns:
                interest_rate = df['rate'].iloc[0]  # Assuming rate is the same for the entire period
            else:
                interest_rate = 0  # Default to 0 if no 'rate' column is found
            
            # Extract fees from the column labeled 'fees'
            if 'fees' in df.columns:
                fees = df['fees'].sum()  # Sum of all fees
            else:
                fees = 0  # Default to 0 if no 'fees' column is found
            
            # Calculate the initial balance
            initial_balance = loan_amount + (loan_amount * interest_rate / 100) + fees
            
            # Get the date corresponding to the loan amount (first row with loan description)
            loan_date = df[df['Description'].str.contains("Loan Amount", case=False)].iloc[0]['Date'] if not df[df['Description'].str.contains("Loan Amount", case=False)].empty else df['Date'].min()
            
            # Filter data within date range
            start_date = st.date_input("Start Date", df['Date'].min())
            end_date = st.date_input("End Date", df['Date'].max())
            
            # Apply the date filters
            filtered_df = filtered_df[(filtered_df['Date'] >= pd.to_datetime(start_date)) & (filtered_df['Date'] <= pd.to_datetime(end_date))]
            
            if st.button("Generate Statement"):
                if customer_name:
                    pdf_file = generate_pdf(customer_name, filtered_df, company_name, logo_path, initial_balance, loan_date)
                    with open(pdf_file, "rb") as f:
                        st.download_button("Download Statement PDF", f, file_name=pdf_file, mime="application/pdf")
                    
                    excel_file = generate_excel(customer_name, filtered_df)
                    with open(excel_file, "rb") as f:
                        st.download_button("Download Statement Excel", f, file_name=excel_file, mime="application/vnd.ms-excel")
                else:
                    st.error("Please enter a customer name before generating a statement.")
