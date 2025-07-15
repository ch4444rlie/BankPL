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

# Bank-to-template mapping
BANK_TEMPLATE_FUNCTIONS = {
    "Chase": create_chase_classic,
    "Wells Fargo": create_wellsfargo_classic,
    "PNC": create_pnc_classic,
    "Citibank": create_citi_classic
}

# Bank names
BANK_NAMES = ["Chase", "Wells Fargo", "PNC", "Citibank"]

# Streamlit app configuration
st.set_page_config(page_title="Lightweight Bank Statement Generator", page_icon="🏦", layout="wide")

# Custom CSS for buttons (normalized size, single-line text, professional look)
st.markdown("""
<style>
.stButton > button {
    width: 120px;
    height: 30px;
    font-size: 14px;
    line-height: 30px;
    padding: 0 10px;
    margin: 5px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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

    # Generate and Randomize buttons
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        if st.button("Generate Statement", key="sidebar_generate_button"):
            if not selected_bank:
                st.error("Please select a bank first.")
            else:
                st.session_state['trigger_generate'] = True
                st.session_state['is_random'] = False
    with cols[1]:
        if st.button("Randomize", key="sidebar_randomize_button"):
            st.session_state['trigger_generate'] = True
            st.session_state['is_random'] = True

# Main app logic
st.title("Lightweight Synthetic Bank Statement Generator")
st.markdown("""  
- Create your synthetic bank statement with the sidebar options.  
- Select **Personal** or **Business** account type to customize transaction categories.  
- Use **Generate Statement** for a bank-specific statement or **Randomize** for a dynamic layout.  
- Download the generated PDF!
""")

# Display logs for debugging
with st.expander("View Logs"):
    st.write(st.session_state.get('logs', []))

# Handle generation
if st.session_state['trigger_generate']:
    if not (selected_bank or st.session_state.get('is_random', False)):
        st.error("Please select a bank or click Randomize.")
        st.session_state['trigger_generate'] = False
    else:
        with st.spinner(f"Generating {'random' if st.session_state.get('is_random', False) else selected_bank} {account_type} statement..."):
            try:
                if st.session_state.get('is_random', False):
                    selected_bank = random.choice(BANK_NAMES)
                    template_func = create_dynamic_statement
                    template_name = "Dynamic Layout"
                else:
                    template_func = BANK_TEMPLATE_FUNCTIONS[selected_bank]
                    template_name = f"{selected_bank} Classic"
                
                ctx = generate_statement_data(selected_bank, account_type=account_type)
                # Slice transactions to user-specified number
                ctx['transactions'] = ctx['transactions'][:num_transactions]
                ctx['deposits'] = [t for t in ctx['transactions'] if t['credit']]
                ctx['withdrawals'] = [t for t in ctx['transactions'] if t['debit']]
                ctx['summary']['deposits_count'] = str(len(ctx['deposits']))
                ctx['summary']['withdrawals_count'] = str(len(ctx['withdrawals']))
                ctx['summary']['transactions_count'] = str(len(ctx['transactions']))
                
                pdf_buffer = BytesIO()
                template_func(ctx, output_buffer=pdf_buffer)
                pdf_filename = f"{selected_bank.lower()}_statement_{ctx['customer_account_number'][-4:]}.pdf"
                st.session_state['statement_data'] = ctx
                st.session_state['pdf_buffer'] = pdf_buffer
                st.session_state['pdf_filename'] = pdf_filename
                st.session_state['trigger_generate'] = False
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Statement generated for {selected_bank} with {template_name}"]
                st.success(f"Statement generated for {selected_bank} with {template_name}")
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
    st.markdown("Select a bank, account type, and number of transactions in the sidebar, then click 'Generate Statement' or 'Randomize' to preview your synthetic bank statement.")