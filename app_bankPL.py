import streamlit as st
import os
import base64
from gen_pl import (
    generate_statement_data,
    create_dynamic_statement,
    create_citi_classic,
    create_chase_classic,
    create_wellsfargo_classic,
    create_pnc_classic
)
from streamlit_pdf_viewer import pdf_viewer
from faker import Faker
import random

# Initialize Faker
fake = Faker()

# Streamlit page configuration
st.set_page_config(page_title="Synthetic Bank Statement Generator", page_icon="🏦", layout="wide")

# Custom CSS for buttons
st.markdown("""
<style>
.stButton > button {
    width: 100%;
    height: 40px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Bank and template configurations
BANK_DISPLAY_NAMES = {
    "Chase": "Chase",
    "Citibank": "Citibank",
    "Wells Fargo": "Wells Fargo",
    "PNC": "PNC"
}

TEMPLATE_DISPLAY_NAMES = {
    "chase_classic": "Classic Template 1 (Chase Style)",
    "citi_classic": "Classic Template 2 (Citibank Style)",
    "wellsfargo_classic": "Classic Template 3 (Wells Fargo Style)",
    "pnc_classic": "Classic Template 4 (PNC Style)"
}

# Map template keys to their respective functions
TEMPLATE_FUNCTIONS = {
    "chase_classic": create_chase_classic,
    "citi_classic": create_citi_classic,
    "wellsfargo_classic": create_wellsfargo_classic,
    "pnc_classic": create_pnc_classic
}

# Sidebar for user inputs
with st.sidebar:
    st.header("Statement Options")
    st.markdown("Configure your synthetic bank statement.")

    # Bank selection
    st.subheader("Select Bank")
    banks = list(BANK_DISPLAY_NAMES.keys())
    if "selected_bank_key" not in st.session_state:
        st.session_state["selected_bank_key"] = None

    cols = st.columns(2)
    for idx, bank_key in enumerate(banks):
        with cols[idx % 2]:
            if st.button(BANK_DISPLAY_NAMES[bank_key], key=f"bank_button_{bank_key}"):
                st.session_state["selected_bank_key"] = bank_key
                st.session_state["generated"] = False

    selected_bank_key = st.session_state["selected_bank_key"]
    selected_bank = BANK_DISPLAY_NAMES.get(selected_bank_key, "No Bank Selected")

    # Template selection
    st.subheader("Select Template")
    template_options = list(TEMPLATE_DISPLAY_NAMES.keys())
    selected_template = st.selectbox(
        "Choose Template Style",
        template_options,
        format_func=lambda x: TEMPLATE_DISPLAY_NAMES.get(x, x),
        disabled=not selected_bank_key
    )

    # Number of transactions
    st.subheader("Number of Transactions")
    num_transactions = st.slider("Number of Transactions", min_value=3, max_value=25, value=5, step=1)

    # Add spacing before buttons
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Generate and Randomize buttons
    col1, col2 = st.columns(2)
    with col1:
        generate_button = st.button("Generate Statement", key="generate_button", disabled=not selected_bank_key)
    with col2:
        randomize_button = st.button("Randomize", key="randomize_button")

# Main interface
st.title("Synthetic Bank Statement Generator")
st.markdown("""
- Create synthetic bank statements with customizable options.
- Select a bank to determine the data and a template style for the presentation.
- Use the **Generate** button to create a statement with your selections.
- Use the **Randomize** button to generate a statement with a random bank and template style.
- Preview and download the generated PDF!
""")

# Initialize session state
if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "pdf_content" not in st.session_state:
    st.session_state["pdf_content"] = None
if "pdf_filename" not in st.session_state:
    st.session_state["pdf_filename"] = None

# Function to generate statement
def generate_statement(bank_key, template_key, num_transactions):
    # Generate fresh bank_ctx using generate_statement_data
    bank_ctx = generate_statement_data(bank_key)
    # Adjust number of transactions
    bank_ctx["transactions"] = bank_ctx["transactions"][:num_transactions]
    bank_ctx["deposits"] = [t for t in bank_ctx["transactions"] if t["credit"]][:num_transactions]
    bank_ctx["withdrawals"] = [t for t in bank_ctx["transactions"] if t["debit"]][:num_transactions]
    bank_ctx["daily_balances"] = bank_ctx["daily_balances"][:num_transactions]
    bank_ctx["summary"]["deposits_count"] = str(len(bank_ctx["deposits"]))
    bank_ctx["summary"]["withdrawals_count"] = str(len(bank_ctx["withdrawals"]))
    bank_ctx["summary"]["transactions_count"] = str(len(bank_ctx["transactions"]))

    output_dir = "synthetic_statements"
    os.makedirs(output_dir, exist_ok=True)
    pdf_file = os.path.join(output_dir, f"{bank_key.lower().replace(' ', '_')}_statement_{bank_ctx['customer_account_number'][-4:]}.pdf")
    
    # Call the selected template function
    template_function = TEMPLATE_FUNCTIONS[template_key]
    template_function(bank_ctx, output_dir)
    
    with open(pdf_file, "rb") as f:
        pdf_content = f.read()
    
    return pdf_content, os.path.basename(pdf_file)

# Function to generate random statement using create_dynamic_statement
def generate_random_statement(num_transactions):
    random_bank_key = random.choice(list(BANK_DISPLAY_NAMES.keys()))
    bank_ctx = generate_statement_data(random_bank_key)
    # Adjust number of transactions
    bank_ctx["transactions"] = bank_ctx["transactions"][:num_transactions]
    bank_ctx["deposits"] = [t for t in bank_ctx["transactions"] if t["credit"]][:num_transactions]
    bank_ctx["withdrawals"] = [t for t in bank_ctx["transactions"] if t["debit"]][:num_transactions]
    bank_ctx["daily_balances"] = bank_ctx["daily_balances"][:num_transactions]
    bank_ctx["summary"]["deposits_count"] = str(len(bank_ctx["deposits"]))
    bank_ctx["summary"]["withdrawals_count"] = str(len(bank_ctx["withdrawals"]))
    bank_ctx["summary"]["transactions_count"] = str(len(bank_ctx["transactions"]))

    # Template variations for create_dynamic_statement
    template_variations = {
        "classic_1": {"font_size": 10, "margin": 0.5 * inch, "logo_scale": 1.0},
        "classic_2": {"font_size": 11, "margin": 0.6 * inch, "logo_scale": 1.2},
        "classic_3": {"font_size": 9, "margin": 0.4 * inch, "logo_scale": 0.8},
        "classic_4": {"font_size": 10, "margin": 0.55 * inch, "logo_scale": 1.1}
    }
    random_template_key = random.choice(list(template_variations.keys()))
    template_params = template_variations[random_template_key]

    output_dir = "synthetic_statements"
    os.makedirs(output_dir, exist_ok=True)
    pdf_file = os.path.join(output_dir, f"{random_bank_key.lower().replace(' ', '_')}_statement_{bank_ctx['customer_account_number'][-4:]}.pdf")
    
    # Modify create_dynamic_statement to use template parameters
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    original_create_dynamic_statement = create_dynamic_statement
    def modified_create_dynamic_statement(ctx, output_dir=output_dir):
        c = canvas.Canvas(os.path.join(output_dir, f"{ctx['bank_name'].lower().replace(' ', '_')}_statement_{ctx['customer_account_number'][-4:]}.pdf"), pagesize=letter)
        c.margin = template_params["margin"]
        c.font_size = template_params["font_size"]
        c.logo_scale = template_params["logo_scale"]
        result = original_create_dynamic_statement(ctx, output_dir)
        return result

    modified_create_dynamic_statement(bank_ctx, output_dir)
    
    with open(pdf_file, "rb") as f:
        pdf_content = f.read()
    
    return pdf_content, os.path.basename(pdf_file), random_bank_key, random_template_key

# Handle button actions
if generate_button and selected_bank_key and selected_template:
    with st.spinner(f"Generating {selected_bank} statement..."):
        try:
            pdf_content, pdf_filename = generate_statement(selected_bank_key, selected_template, num_transactions)
            st.session_state["generated"] = True
            st.session_state["pdf_content"] = pdf_content
            st.session_state["pdf_filename"] = pdf_filename
        except Exception as e:
            st.error(f"Error generating statement: {str(e)}")
            st.markdown("""
            **Troubleshooting**:
            - Ensure logo files exist in the sample_logos directory.
            - Verify that reportlab and Pillow are installed.
            - Check the synthetic_statements directory for write permissions.
            - Refresh or contact the administrator.
            """)
            st.session_state["generated"] = False
            st.session_state["pdf_content"] = None
            st.session_state["pdf_filename"] = None

if randomize_button:
    with st.spinner("Generating random statement..."):
        try:
            pdf_content, pdf_filename, random_bank_key, random_template_key = generate_random_statement(num_transactions)
            st.session_state["generated"] = True
            st.session_state["pdf_content"] = pdf_content
            st.session_state["pdf_filename"] = pdf_filename
            st.session_state["selected_bank_key"] = random_bank_key
            st.session_state["selected_template"] = random_template_key
        except Exception as e:
            st.error(f"Error generating random statement: {str(e)}")
            st.markdown("""
            **Troubleshooting**:
            - Ensure logo files exist in the sample_logos directory.
            - Verify that reportlab and Pillow are installed.
            - Check the synthetic_statements directory for write permissions.
            - Refresh or contact the administrator.
            """)
            st.session_state["generated"] = False
            st.session_state["pdf_content"] = None
            st.session_state["pdf_filename"] = None

# Display preview and download
if st.session_state["generated"] and st.session_state["pdf_content"]:
    st.download_button(
        label=f"Download {BANK_DISPLAY_NAMES.get(st.session_state['selected_bank_key'], 'Bank')} Statement PDF",
        data=st.session_state["pdf_content"],
        file_name=st.session_state["pdf_filename"],
        mime="application/pdf",
        key=f"pdf_download_{st.session_state['selected_bank_key']}"
    )

    st.subheader(f"Preview: {BANK_DISPLAY_NAMES.get(st.session_state['selected_bank_key'], 'Bank')} Statement")
    preview_placeholder = st.empty()
    pdf_viewer(
        input=st.session_state["pdf_content"],
        width=700,
        height=600,
        zoom_level=1.0,
        viewer_align="center",
        show_page_separator=True
    )
    preview_placeholder.markdown("""
    **Note**: If the PDF doesn't display, ensure JavaScript is enabled, disable ad blockers, or try Firefox/Edge. The PDF can still be downloaded using the button above.
    """)

    # Details expander
    with st.expander("View Details"):
        st.write(f"PDF saved: synthetic_statements/{st.session_state['pdf_filename']}")
        st.write(f"Bank: {BANK_DISPLAY_NAMES.get(st.session_state['selected_bank_key'], 'Unknown')}")
        st.write(f"Template: {TEMPLATE_DISPLAY_NAMES.get(st.session_state.get('selected_template', selected_template), 'Unknown')}")
        st.write(f"Number of Transactions: {num_transactions}")

# Default preview message
if not st.session_state["generated"]:
    st.subheader(f"Preview: {selected_bank} Statement")
    preview_placeholder = st.empty()
    preview_placeholder.markdown("Select a bank and template style in the sidebar, then click 'Generate Statement' or 'Randomize' to preview your synthetic bank statement.")