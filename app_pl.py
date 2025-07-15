import streamlit as st
import base64
import random
from datetime import datetime
from io import BytesIO
from reportlab.lib.units import inch
from streamlit_pdf_viewer import pdf_viewer
from randomize import generate_statement_data
from classic_functions import create_citi_classic, create_chase_classic, create_wellsfargo_classic, create_pnc_classic
from dynamic import create_dynamic_statement

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

# Custom CSS for buttons (inspired by inspiration version)
st.markdown("""
<style>
.stButton > button {
    width: 100%;
    height: 40px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'statement_data' not in st.session_state:
    st.session_state['statement_data'] = None
if 'pdf_buffer' not in st.session_state:
    st.session_state['pdf_buffer'] = None
if 'pdf_filename' not in st.session_state:
    st.session_state['pdf_filename'] = None
if 'trigger_generate' not in st.session_state:
    st.session_state['trigger_generate'] = False
if 'logs' not in st.session_state:
    st.session_state['logs'] = []

# Sidebar for user input
with st.sidebar:
    st.header("Statement Generation Options")
    st.markdown("Configure your synthetic bank statement.")
    
    # Bank selection
    st.subheader("Select Bank")
    cols = st.columns(2)
    for idx, bank in enumerate(BANK_NAMES):
        with cols[idx % 2]:
            if st.button(bank, key=f"bank_button_{bank}"):
                st.session_state['selected_bank'] = bank
                st.session_state['trigger_generate'] = False
    
    selected_bank = st.session_state.get('selected_bank', None)
    
    # Account type selection
    st.subheader("Select Account Type")
    cols = st.columns(2)
    with cols[0]:
        if st.button("Personal", key="account_type_personal"):
            st.session_state['account_type'] = "personal"
    with cols[1]:
        if st.button("Business", key="account_type_business"):
            st.session_state['account_type'] = "business"
    
    account_type = st.session_state.get('account_type', "personal")

    # Number of transactions
    st.subheader("Number of Transactions")
    num_transactions = st.slider("Number of Transactions", min_value=3, max_value=25, value=5, step=1)

    # Template selection
    if selected_bank:
        selected_template = st.selectbox("Select Template Style", list(TEMPLATE_FUNCTIONS.keys()))
    else:
        selected_template = None
        st.markdown("Select a bank to choose a template style.")
    
    # Generate button
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Generate Statement", key="sidebar_generate_button"):
        if not (selected_bank and selected_template):
            st.error("Please select a bank and template style first.")
        else:
            st.session_state['trigger_generate'] = True

# Main app logic
st.title("Lightweight Synthetic Bank Statement Generator")
st.markdown("""  
- Create your synthetic bank statement with the sidebar options.  
- Select **Personal** or **Business** account type to customize transaction categories.  
- Choose a **Classic** template for a realistic statement or a **Custom** template for variations.  
- Download the generated PDF!
""")

# Display logs for debugging
with st.expander("View Logs"):
    st.write(st.session_state.get('logs', []))

# Handle generation
if st.session_state['trigger_generate']:
    if not (selected_bank and selected_template):
        st.error("Please select a bank and template style first.")
        st.session_state['trigger_generate'] = False
    else:
        with st.spinner(f"Generating {selected_bank} {account_type} statement..."):
            try:
                ctx = generate_statement_data(selected_bank, account_type=account_type)
                # Slice transactions to user-specified number
                ctx['transactions'] = ctx['transactions'][:num_transactions]
                ctx['deposits'] = [t for t in ctx['transactions'] if t['credit']]
                ctx['withdrawals'] = [t for t in ctx['transactions'] if t['debit']]
                ctx['summary']['deposits_count'] = str(len(ctx['deposits']))
                ctx['summary']['withdrawals_count'] = str(len(ctx['withdrawals']))
                ctx['summary']['transactions_count'] = str(len(ctx['transactions']))
                template_func = TEMPLATE_FUNCTIONS[selected_template]
                pdf_buffer = BytesIO()
                template_func(ctx, output_buffer=pdf_buffer)
                pdf_filename = f"{selected_bank.lower()}_statement_{ctx['customer_account_number'][-4:]}.pdf"
                st.session_state['statement_data'] = ctx
                st.session_state['pdf_buffer'] = pdf_buffer
                st.session_state['pdf_filename'] = pdf_filename
                st.session_state['trigger_generate'] = False
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Statement generated for {selected_bank} with {selected_template}"]
                st.success(f"Statement generated for {selected_bank} with {selected_template}")
            except Exception as e:
                st.error(f"Error generating statement: {str(e)}")
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error generating statement: {str(e)}"]
                st.markdown("""
                **Troubleshooting**:
                - Ensure transactions are between 3 and 25.
                - Verify logo files are accessible in the GitHub repository (sample_logos directory).
                - Check that reportlab, Pillow, and streamlit_pdf_viewer are installed.
                - If the PDF preview fails, try Firefox/Edge or disable ad blockers.
                - Refresh or contact the administrator.
                """)
                st.session_state['trigger_generate'] = False
                st.session_state['statement_data'] = None
                st.session_state['pdf_buffer'] = None
                st.session_state['pdf_filename'] = None

# Display statement data and PDF preview
if st.session_state['statement_data'] and st.session_state['pdf_buffer']:
    st.header("Generated Statement Data")
    with st.expander("View Details"):
        st.json(st.session_state['statement_data'])

    st.subheader(f"Preview: {selected_bank} {account_type.capitalize()} Statement")
    pdf_buffer = st.session_state['pdf_buffer']
    pdf_buffer.seek(0)
    pdf_content = pdf_buffer.read()
    pdf_viewer(
        input=pdf_content,
        width=700,
        height=600,
        zoom_level=1.0,
        viewer_align="center",
        show_page_separator=True
    )
    st.markdown("""
    **Note**: If the PDF doesn't display, ensure JavaScript is enabled, disable ad blockers, or try Firefox/Edge. The PDF can still be downloaded using the button below.
    """)

    # Download button
    st.download_button(
        label=f"Download {selected_bank} {account_type.capitalize()} PDF",
        data=pdf_content,
        file_name=st.session_state['pdf_filename'],
        mime="application/pdf",
        key=f"pdf_download_{selected_bank}_{account_type}"
    )

# Default preview message
else:
    st.subheader(f"Preview: {selected_bank or 'No Bank Selected'} {account_type.capitalize()} Statement")
    st.markdown("Select a bank, account type, and template style in the sidebar, then click 'Generate Statement' to preview your synthetic bank statement.")