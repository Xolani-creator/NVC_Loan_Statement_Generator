import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
from datetime import datetime, timedelta
import os
import base64

# Initialize SQLite connection
conn = sqlite3.connect("loan_statements_v2.db", check_same_thread=False)
cursor = conn.cursor()

# Ensure that the new columns exist in the customers table
cursor.execute("PRAGMA table_info(customers)")
columns = [column[1] for column in cursor.fetchall()]

# Add missing columns if they don't exist
if 'email' not in columns:
    cursor.execute("ALTER TABLE customers ADD COLUMN email TEXT")
if 'address' not in columns:
    cursor.execute("ALTER TABLE customers ADD COLUMN address TEXT")
if 'company_registration' not in columns:
    cursor.execute("ALTER TABLE customers ADD COLUMN company_registration TEXT")

conn.commit()

# Create tables if they don't exist
cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        email TEXT,
        address TEXT,
        company_registration TEXT
    )
""")

cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        account_number TEXT NOT NULL,
        loan_amount REAL NOT NULL,
        loan_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        loan_status TEXT DEFAULT 'Active',  
        interest_rate REAL DEFAULT 0.23,  
        admin_fee REAL DEFAULT 500.00,
        payment_frequency TEXT,
        collateral TEXT,
        disbursement_method TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
""")

cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
    )
""")

conn.commit()

# PDF generation function
class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(200, 10, "Loan Statement", ln=True, align='C')
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def generate_pdf(customer_name, account_number, transactions, company_name, loan_date, loan_amount, finance_charge, admin_fee):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=10)

    try:
        pdf.image("logo.png", x=10, y=8, w=50, h=15)
    except:
        st.warning("Logo not found.")
    
    statement_date = datetime.now().strftime("%Y/%m/%d")
    pdf.cell(0, 5, f"Account Number: {account_number}", ln=True, align='R')
    pdf.cell(0, 5, f"Statement Date: {statement_date}", ln=True, align='R')
    pdf.ln(12)

    pdf.cell(0, 6, "98 Spaanriet Street, The Reeds Ext 45, 0156", ln=True)
    pdf.cell(0, 6, "(012) 006 0019", ln=True)
    pdf.cell(0, 6, "info@ntirhisano.com", ln=True)
    pdf.ln(10)

    if os.path.exists("transparent_watermark.png"):
        try:
            pdf.image("transparent_watermark.png", x=30, y=60, w=150, h=150, type="PNG")
        except:
            st.warning("Watermark unreadable.")
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 12, "STATEMENT OF ACCOUNT", ln=True, align='C')
    pdf.set_draw_color(204, 85, 0)
    pdf.set_line_width(1.0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, customer_name, ln=True, align='C')
    pdf.ln(10)

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

    pdf.set_font("Helvetica", size=10)
    balance = 0
    fmt = lambda x: f"{x:,.2f}R".replace(",", " ").replace(".", ",")
    
    for idx, row in transactions.iterrows():
        date = pd.to_datetime(row['date']).strftime('%Y/%m/%d')
        desc = str(row['description'])
        amount = row['amount']
        charge = amount if amount > 0 else 0
        credit = -amount if amount < 0 else 0
        balance += amount

        pdf.cell(30, 8, date, border=1)
        pdf.cell(65, 8, desc[:32], border=1)
        pdf.cell(30, 8, fmt(charge) if charge else "", border=1, align='R')
        pdf.cell(30, 8, fmt(credit) if credit else "", border=1, align='R')
        pdf.cell(35, 8, fmt(balance), border=1, align='R')
        pdf.ln()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(155, 8, "Outstanding Balance", border=1, align='R', fill=True)
    pdf.cell(35, 8, fmt(balance), border=1, align='R', fill=True)
    pdf.ln(10)

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

    pdf_filename = f"Statement_{customer_name.replace(' ', '_')}_{account_number}.pdf"
    pdf.output(pdf_filename)
    return pdf_filename

# Streamlit App UI
st.title("Loan Statement Generator (Multi-Loan DB Version)")

# Add Customer Form
with st.expander("➕ Add New Customer"):
    name = st.text_input("Customer Name")
    email = st.text_input("Email Address")
    address = st.text_area("Address")
    company_registration = st.text_input("Company Registration (Format: yyyy/######/##)")

    if st.button("Save Customer"):
        cursor.execute(""" 
            INSERT INTO customers (customer_name, email, address, company_registration) 
            VALUES (?, ?, ?, ?) 
        """, (name, email, address, company_registration))
        conn.commit()
        st.success("Customer added.")

# Fetch customers
customers_df = pd.read_sql("SELECT * FROM customers ORDER BY customer_name", conn)
selected_customer = st.selectbox("Select Customer:", customers_df['customer_name'].tolist())

if selected_customer:
    cust_id = customers_df[customers_df['customer_name'] == selected_customer]['customer_id'].values[0]
    st.markdown("---")

    # Add Loan Form
    with st.expander("➕ Add New Loan"):
        account_number = st.text_input("Account Number")
        loan_amount = st.number_input("Loan Amount", min_value=0.01)
        loan_date = st.date_input("Loan Date", datetime.today())
        due_date = loan_date + timedelta(days=45)
        st.markdown(f"📅 **Due Date (auto-calculated):** `{due_date.strftime('%Y-%m-%d')}`")
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=0.23)
        admin_fee = st.number_input("Admin Fee", min_value=0.0, value=500.00)
        payment_frequency = st.selectbox("Payment Frequency", ["Monthly", "Quarterly", "Annually"])
        collateral = st.text_input("Collateral (if any)")
        disbursement_method = st.selectbox("Disbursement Method", ["Bank Transfer", "Cash", "Cheque"])

        # After loan creation
    if st.button("Save Loan"):
        cursor.execute("""
            INSERT INTO loans (account_number, customer_id, loan_amount, interest_rate, admin_fee, loan_date, due_date, payment_frequency, collateral, disbursement_method, loan_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_number, cust_id, loan_amount, interest_rate, admin_fee,
            loan_date.strftime('%Y-%m-%d'), due_date,
            payment_frequency, collateral, disbursement_method, "Active"
        ))
        conn.commit()

        # Get the inserted loan ID
        loan_id = cursor.lastrowid

        # Prepare transactions
        finance_charge = loan_amount * (interest_rate / 100)
        disbursal_date = loan_date.strftime('%Y-%m-%d')

        transactions = [
            (loan_id, disbursal_date, "Loan Disbursed", loan_amount, "disbursal", "bank transfer"),
            (loan_id, disbursal_date, "Finance Charge", finance_charge, "finance charge", "bank transfer"),
            (loan_id, disbursal_date, "Admin Fee", admin_fee, "fees", "bank transfer")
        ]

        cursor.executemany("""
            INSERT INTO transactions (loan_id, date, description, amount, transaction_type, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, transactions)
        conn.commit()

        st.success("Loan and standard transactions recorded successfully!")


    # Display Loan Information
    loans_df = pd.read_sql(""" 
        SELECT * FROM loans WHERE customer_id = ? 
    """, conn, params=(cust_id,))
    st.dataframe(loans_df)

    # Add Transactions
    loan_id = st.selectbox("Select Loan for Transaction", loans_df['loan_id'].tolist())
    transactions_df = pd.read_sql("""
        SELECT * FROM transactions WHERE loan_id = ?
    """, conn, params=(loan_id,))
    st.dataframe(transactions_df)

    if loan_id:
        transaction_date = st.date_input("Transaction Date", datetime.today())
        description = st.text_input("Transaction Description")
        amount = st.number_input("Amount (negative for payment)")
        transaction_type = st.selectbox("Transaction Type", ["Repayment", "Interest", "Penalty"])
        payment_method = st.selectbox("Payment Method", ["Bank Transfer", "Cash", "Cheque"])

        if st.button("Add Transaction"):
            cursor.execute("""
                INSERT INTO transactions (loan_id, date, description, amount, transaction_type, payment_method)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (loan_id, transaction_date.strftime("%Y-%m-%d"), description, amount, transaction_type, payment_method))
            conn.commit()
            st.success("Transaction added.")

        # Display Transactions
        transactions_df = pd.read_sql("""
            SELECT * FROM transactions WHERE loan_id = ?
        """, conn, params=(loan_id,))
        st.dataframe(transactions_df)

    # 🔍 Search & Manage Transactions
    st.markdown("### 🔍 Search & Manage Transactions")

    search_term = st.text_input("Search transactions by description...")
    txn_df = pd.read_sql("SELECT * FROM transactions WHERE loan_id = ? ORDER BY date", conn, params=(loan_id,))
    txn_filtered = txn_df[txn_df['description'].str.contains(search_term, case=False, na=False)] if search_term else txn_df

    st.dataframe(txn_filtered)

    if not txn_filtered.empty:
        txn_choices = txn_filtered.apply(lambda row: f"{row['transaction_id']} - {row['date']} | {row['description']} | {row['amount']}", axis=1).tolist()
        selected_txn = st.selectbox("Select a transaction to edit or delete:", txn_choices)

        if selected_txn:
            txn_id = int(selected_txn.split(" - ")[0])
            txn_row = txn_filtered[txn_filtered["transaction_id"] == txn_id].iloc[0]

            with st.expander("✏️ Edit Transaction"):
                with st.form("edit_transaction_form"):
                    new_date = st.date_input("Date", pd.to_datetime(txn_row['date']))
                    new_desc = st.text_input("Description", txn_row['description'])
                    new_amount = st.number_input("Amount", value=txn_row['amount'], step=0.01)
                    new_type = st.text_input("Transaction Type", txn_row.get('transaction_type', ''))
                    new_method = st.text_input("Payment Method", txn_row.get('payment_method', ''))

                    update = st.form_submit_button("Update Transaction")
                    if update:
                        cursor.execute("""
                            UPDATE transactions 
                            SET date = ?, description = ?, amount = ?, transaction_type = ?, payment_method = ?
                            WHERE transaction_id = ?
                        """, (new_date.strftime("%Y-%m-%d"), new_desc, new_amount, new_type, new_method, txn_id))
                        conn.commit()
                        st.success("Transaction updated.")

            if st.button("❌ Delete Selected Transaction"):
                cursor.execute("DELETE FROM transactions WHERE transaction_id = ?", (txn_id,))
                conn.commit()
                st.warning("Transaction deleted.")

    # Generate Loan Statement
    if st.button("Generate Statement"):
        loan_info = loans_df[loans_df['loan_id'] == loan_id].iloc[0]
        transactions = pd.read_sql("""
            SELECT * FROM transactions WHERE loan_id = ? ORDER BY date
        """, conn, params=(loan_id,))
        pdf_filename = generate_pdf(
            selected_customer, 
            loan_info['account_number'], 
            transactions, 
            selected_customer, 
            loan_info['loan_date'], 
            loan_info['loan_amount'], 
            loan_info['loan_amount'] * loan_info['interest_rate'], 
            loan_info['admin_fee']
        )
        st.success(f"Statement generated: {pdf_filename}")

        # Open the generated PDF file automatically in pdf application
        with open(pdf_filename, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        
            st.download_button("Download Statement PDF", f, file_name=pdf_filename, mime="application/pdf")
