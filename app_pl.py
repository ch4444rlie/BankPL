import streamlit as st
import os
import base64
from datetime import datetime
from randomize import generate_statement_data
from classic_functions import create_citi_classic, create_chase_classic, create_wellsfargo_classic, create_pnc_classic
from dynamic import create_dynamic_statement
from reportlab.lib.units import inch

# Template functions dictionary
TEMPLATE_FUNCTIONS = {
    "Citi Format": create_citi_classic,
    "Chase Format": create_chase_classic,
    "Wells Fargo Format": create_wellsfargo_classic,
    "PNC Format": create_pnc_classic,
    "Dynamically Changing Formats": create_dynamic_statement
}

# Bank names
BANK_NAMES = ["Chase", "Wells Fargo", "PNC", "Citibank"]

# Streamlit app configuration
st.set_page_config(page_title="Lightweight Bank Statement Generator", page_icon="🏦", layout="wide")

# Initialize session state
if 'statement_data' not in st.session_state:
    st.session_state['statement_data'] = None
if 'pdf_path' not in st.session_state:
    st.session_state['pdf_path'] = None

# Sidebar for user input
st.sidebar.header("Statement Generation Options")
bank_name = st.sidebar.selectbox("Select Bank", BANK_NAMES)
template_name = st.sidebar.selectbox("Select Template", list(TEMPLATE_FUNCTIONS.keys()))
num_transactions = st.sidebar.slider("Number of Transactions to Display", 5, 50, 10)
generate_button = st.sidebar.button("Generate Statement")
randomize_button = st.sidebar.button("Randomize")

# Ensure output directory exists
output_dir = os.path.join(".", "synthetic_statements")
os.makedirs(output_dir, exist_ok=True)

# Function to encode PDF for preview
def get_pdf_base64(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Error reading PDF for preview: {str(e)}")
        return None

# Function to generate random statement
def generate_random_statement():
    bank = random.choice(BANK_NAMES)
    template = random.choice(list(TEMPLATE_FUNCTIONS.keys()))
    ctx = generate_statement_data(bank)
    template_func = TEMPLATE_FUNCTIONS[template]
    try:
        template_func(ctx, output_dir=output_dir)
        pdf_path = os.path.join(output_dir, f"{bank.lower()}_statement_{ctx['customer_account_number'][-4:]}.pdf")
        return ctx, pdf_path
    except Exception as e:
        st.error(f"Error generating random statement: {str(e)}")
        return None, None

# Main app logic
st.title("Lightweight Bank Statement Generator")
st.write("Generate synthetic bank statements for testing purposes.")

if generate_button:
    try:
        ctx = generate_statement_data(bank_name)
        # Slice transactions to user-specified number
        ctx['transactions'] = ctx['transactions'][:num_transactions]
        ctx['deposits'] = [t for t in ctx['transactions'] if t['credit']]  # Update deposits
        ctx['withdrawals'] = [t for t in ctx['transactions'] if t['debit']]  # Update withdrawals
        ctx['summary']['deposits_count'] = str(len(ctx['deposits']))
        ctx['summary']['withdrawals_count'] = str(len(ctx['withdrawals']))
        ctx['summary']['transactions_count'] = str(len(ctx['transactions']))
        template_func = TEMPLATE_FUNCTIONS[template_name]
        template_func(ctx, output_dir=output_dir)
        pdf_path = os.path.join(output_dir, f"{bank_name.lower()}_statement_{ctx['customer_account_number'][-4:]}.pdf")
        st.session_state['statement_data'] = ctx
        st.session_state['pdf_path'] = pdf_path
        st.success(f"Statement generated: {pdf_path}")
    except Exception as e:
        st.error(f"Error generating statement: {str(e)}")

if randomize_button:
    ctx, pdf_path = generate_random_statement()
    if ctx and pdf_path:
        st.session_state['statement_data'] = ctx
        st.session_state['pdf_path'] = pdf_path
        st.success(f"Random statement generated: {pdf_path}")

# Display statement data and PDF preview
if st.session_state['statement_data']:
    st.header("Generated Statement Data")
    st.json(st.session_state['statement_data'])

    if st.session_state['pdf_path'] and os.path.exists(st.session_state['pdf_path']):
        st.header("PDF Preview")
        pdf_base64 = get_pdf_base64(st.session_state['pdf_path'])
        if pdf_base64:
            pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="700" height="1000" type="application/pdf">'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error("Unable to display PDF preview.")
        
        # Download button
        with open(st.session_state['pdf_path'], "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f,
                file_name=os.path.basename(st.session_state['pdf_path']),
                mime="application/pdf"
            )
    else:
        st.error("PDF file not found.")

# Log generation details
if st.session_state['pdf_path']:
    with open("layout_debug.log", "a") as log_file:
        log_file.write(f"[{datetime.now()}] App: Generated statement for {bank_name} with template {template_name}, saved to {st.session_state['pdf_path']}\n")