import streamlit as st
from io import BytesIO
from datetime import datetime
try:
    from classic_functions import create_citi_classic, create_chase_classic, create_wellsfargo_classic, create_pnc_classic
    from dynamic import create_dynamic_statement
    from randomize import generate_random_context
except ImportError as e:
    st.error(f"Failed to import modules: {e}")
    st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] ImportError: {e}"]
    st.stop()

# Initialize session state
if 'pdf_buffer' not in st.session_state:
    st.session_state['pdf_buffer'] = None
if 'pdf_ready' not in st.session_state:
    st.session_state['pdf_ready'] = False
if 'logs' not in st.session_state:
    st.session_state['logs'] = []

st.title("Bank Statement Generator")

# Sidebar for inputs and buttons
with st.sidebar:
    st.header("Statement Options")
    bank = st.selectbox("Select Bank", ["Random", "Citibank", "Chase", "Wells Fargo", "PNC"], help="Choose a bank or Random for classic style statements")
    account_type = st.selectbox("Account Type", ["Checking", "Business Checking"], help="Select the account type")
    if st.button("Generate", help="Generate a classic-style statement for the selected bank"):
        try:
            # Handle Random bank selection
            selected_bank = random.choice(["Citibank", "Chase", "Wells Fargo", "PNC"]) if bank == "Random" else bank
            ctx = generate_random_context(selected_bank, account_type)
            output_buffer = BytesIO()
            if selected_bank == "Citibank":
                create_citi_classic(ctx, output_buffer)
            elif selected_bank == "Chase":
                create_chase_classic(ctx, output_buffer)
            elif selected_bank == "Wells Fargo":
                create_wellsfargo_classic(ctx, output_buffer)
            elif selected_bank == "PNC":
                create_pnc_classic(ctx, output_buffer)
            output_buffer.seek(0)
            st.session_state['pdf_buffer'] = output_buffer
            st.session_state['pdf_ready'] = True
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Generated classic statement for {selected_bank}"]
        except Exception as e:
            st.error(f"Error generating statement: {e}")
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error generating classic statement: {e}"]

    st.markdown("---")
    st.markdown("Want a dynamically generated style? Click the button below.")
    if st.button("Dynamic Style", help="Generate a statement with a dynamic layout"):
        try:
            ctx = generate_random_context("Dynamic", account_type)
            output_buffer = BytesIO()
            create_dynamic_statement(ctx, output_buffer)
            output_buffer.seek(0)
            st.session_state['pdf_buffer'] = output_buffer
            st.session_state['pdf_ready'] = True
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Generated dynamic statement"]
        except Exception as e:
            st.error(f"Error generating dynamic statement: {e}")
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error generating dynamic statement: {e}"]

# Display PDF and download button
if st.session_state.get('pdf_ready', False):
    st.subheader("Generated Statement")
    try:
        selected_bank = bank if bank != "Random" else ctx.get('bank_name', 'statement')
        st.download_button(
            label="Download PDF",
            data=st.session_state['pdf_buffer'],
            file_name=f"{selected_bank.lower() if selected_bank != 'Dynamic' else 'dynamic'}_statement.pdf",
            mime="application/pdf"
        )
        st_pdf_viewer(st.session_state['pdf_buffer'])
    except Exception as e:
        st.error(f"Error displaying PDF: {e}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error displaying PDF: {e}"]

# Display logs
with st.expander("View Logs"):
    for log in st.session_state.get('logs', []):
        st.write(log)