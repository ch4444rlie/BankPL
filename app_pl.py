import streamlit as st
import random
from datetime import datetime
from io import BytesIO
from streamlit_pdf_viewer import pdf_viewer
from randomize import generate_statement_data
from dynamic import generate_pdf_statement

# Bank names and options
BANK_NAMES = ["Chase", "Wells Fargo", "PNC", "Citibank"]
ACCOUNT_TYPES = ["personal", "business"]
TRANSACTION_RANGE = (3, 25)  # Min and max number of transactions

# Streamlit app configuration
st.set_page_config(page_title="Dynamic Bank Statement Generator", page_icon="🏦", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for centered elements, responsive 2-column sidebar, and simplified download button
st.markdown("""
<style>
.stButton > button {
    display: block;
    margin: 2vw auto;  /* Responsive margin */
    width: 20vw;  /* Responsive width */
    max-width: 200px;  /* Cap for large screens */
    min-width: 150px;  /* Minimum for small screens */
    height: 4vh;  /* Responsive height */
    font-size: 1.2rem;  /* Responsive font */
    font-weight: bold;
    background-color: #4CAF50;
    color: white;
    border-radius: 0.8rem;
}
.stButton > button:hover {
    background-color: #45a049;
}
.centered-title {
    text-align: center;
    font-size: 2rem;  /* Responsive font */
}
.centered-subheader {
    text-align: center;
    font-size: 1.5rem;
}
.centered-text {
    text-align: center;
    font-size: 1rem;
    margin-top: 0.5rem;  /* Tighter spacing */
}
.sidebar .stButton > button {
    width: 100%;
    height: 1.2rem;
    font-size: 0.6rem;
    margin: 0.1rem 0;
    padding: 0 0.2rem;
    background-color: #f0f0f0;
    color: black;
    border-radius: 0.2rem;
}
.sidebar .stButton > button:hover {
    background-color: #e0e0e0;
}
.sidebar .stSlider > div {
    padding: 0.1rem 0;
}
.sidebar .stMarkdown, .sidebar .stHeader {
    font-size: 0.7rem;
    margin-bottom: 0.1rem;
}
.sidebar .st-emotion-cache-1wmy9hl {
    width: 33.33vw !important;  /* Sidebar width = 1/3 page */
    min-width: 200px;
    max-width: 400px;
}
.download-button-container .stDownloadButton > button {
    display: block;
    margin: 0.5rem auto;  /* Minimal margin for tight placement below Generate */
    font-size: 1rem;  /* Match default Streamlit button style */
}
.download-button-container .stDownloadButton > button:hover {
    background-color: #e0e0e0;  /* Subtle hover effect */
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
if 'selected_bank' not in st.session_state:
    st.session_state['selected_bank'] = None
if 'account_type' not in st.session_state:
    st.session_state['account_type'] = None
if 'num_transactions' not in st.session_state:
    st.session_state['num_transactions'] = None
if 'sidebar_selection_made' not in st.session_state:
    st.session_state['sidebar_selection_made'] = False

# Sidebar for customization (hidden by default, 2-column compact layout)
with st.sidebar:
    st.header("Statement Options")
    st.markdown("Customize your statement.")
    
    st.subheader("Bank")
    cols = st.columns(2)
    for idx, bank in enumerate(BANK_NAMES):
        with cols[idx % 2]:
            if st.button(bank, key=f"bank_button_{bank}"):
                st.session_state['selected_bank'] = bank
                st.session_state['sidebar_selection_made'] = True
    
    st.subheader("Account Type")
    cols = st.columns(2)
    for idx, account_type in enumerate(ACCOUNT_TYPES):
        with cols[idx % 2]:
            if st.button(account_type.capitalize(), key=f"account_type_{account_type}"):
                st.session_state['account_type'] = account_type
                st.session_state['sidebar_selection_made'] = True
    
    st.subheader("Transactions")
    st.session_state['num_transactions'] = st.slider(
        "Number of Transactions", 
        min_value=TRANSACTION_RANGE[0], 
        max_value=TRANSACTION_RANGE[1], 
        value=st.session_state['num_transactions'] or 5, 
        step=1
    )
    if st.session_state['num_transactions'] != 5:
        st.session_state['sidebar_selection_made'] = True

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        if st.button("Generate Statement", key="sidebar_generate_button"):
            if not st.session_state['selected_bank']:
                st.error("Please select a bank first.")
            else:
                st.session_state['sidebar_selection_made'] = True
                st.session_state['trigger_generate'] = True

# Main app logic
st.markdown('<h1 class="centered-title">Dynamic Synthetic Bank Statement Generator</h1>', unsafe_allow_html=True)

# Centered generate button
if st.button("Generate", key="main_generate_button"):
    # Randomize if no sidebar selections are made
    if not st.session_state['sidebar_selection_made']:
        st.session_state['selected_bank'] = random.choice(BANK_NAMES)
        st.session_state['account_type'] = random.choice(ACCOUNT_TYPES)
        st.session_state['num_transactions'] = random.randint(TRANSACTION_RANGE[0], TRANSACTION_RANGE[1])
    st.session_state['trigger_generate'] = True

# Handle generation
if 'trigger_generate' in st.session_state and st.session_state.get('trigger_generate', False):
    with st.spinner(f"Generating {st.session_state['selected_bank']} {st.session_state['account_type']} statement..."):
        try:
            ctx = generate_statement_data(
                st.session_state['selected_bank'],
                account_type=st.session_state['account_type'],
                num_transactions=st.session_state['num_transactions']
            )
            ctx['transactions'] = ctx['transactions'][:st.session_state['num_transactions']]
            ctx['deposits'] = [t for t in ctx['transactions'] if t['credit']]
            ctx['withdrawals'] = [t for t in ctx['transactions'] if t['debit']]
            ctx['summary']['deposits_count'] = str(len(ctx['deposits']))
            ctx['summary']['withdrawals_count'] = str(len(ctx['withdrawals']))
            ctx['summary']['transactions_count'] = str(len(ctx['transactions']))
            
            pdf_buffer = BytesIO()
            generate_pdf_statement(ctx, output_buffer=pdf_buffer)
            pdf_filename = f"{st.session_state['selected_bank'].lower()}_statement_{ctx['customer_account_number'][-4:]}.pdf"
            st.session_state['statement_data'] = ctx
            st.session_state['pdf_buffer'] = pdf_buffer
            st.session_state['pdf_filename'] = pdf_filename
            st.session_state['trigger_generate'] = False
        except Exception as e:
            st.error(f"Error generating statement: {str(e)}")
            st.markdown("""
            **Troubleshooting**:
            - Ensure logo files are accessible in the sample_logos directory.
            - Check that reportlab, Pillow, and streamlit_pdf_viewer are installed.
            - If the PDF preview fails, try Firefox/Edge or disable ad blockers.
            - Refresh or contact the administrator.
            """)
            st.session_state['trigger_generate'] = False
            st.session_state['statement_data'] = None
            st.session_state['pdf_buffer'] = None
            st.session_state['pdf_filename'] = None

# Display PDF preview
st.markdown('<h2 class="centered-subheader">Preview</h2>', unsafe_allow_html=True)
if st.session_state['statement_data'] and st.session_state['pdf_buffer']:
    pdf_buffer = st.session_state['pdf_buffer']
    pdf_buffer.seek(0)
    pdf_content = pdf_buffer.read()
    # Wrap download button in a div to ensure centering
    st.markdown('<div class="download-button-container">', unsafe_allow_html=True)
    st.download_button(
        label="Download as PDF",  # Updated label
        data=pdf_content,
        file_name=st.session_state['pdf_filename'],
        mime="application/pdf",
        key=f"pdf_download_{st.session_state['selected_bank']}_{st.session_state['account_type']}"
    )
    st.markdown('<div class="centered-text">Want to customize the statement? Check out the sidebar options!</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    pdf_viewer(
        input=pdf_content,
        width=700,
        height=600,
        zoom_level=1.0,
        viewer_align="center",
        show_page_separator=True
    )
else:
    st.markdown('<div class="centered-text">Click "Generate" to create a random bank statement.</div>', unsafe_allow_html=True)