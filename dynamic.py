from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import random
from PIL import Image
from io import BytesIO
import streamlit as st
from classic_functions import wrap_text, check_page_break

# Professional fonts and colors
PROFESSIONAL_FONTS = ["Helvetica", "Times-Roman", "Courier"]
PROFESSIONAL_COLORS = [colors.black, colors.HexColor("#333333"), colors.HexColor("#000066")]

def get_random_text_style(is_heading=False):
    """Return a randomized but professional font, size, and color."""
    font = random.choice(PROFESSIONAL_FONTS)
    size = random.randint(12, 16) if is_heading else random.randint(8, 12)
    color = random.choice(PROFESSIONAL_COLORS)
    return {"font": font, "size": size, "color": color}

def calculate_dynamic_col_widths(data, usable_width, col_widths_proportions):
    """Calculate dynamic column widths based on content length with randomization."""
    if not data or not col_widths_proportions:
        return [usable_width / len(data[0])] * len(data[0]) if data else [usable_width]
    
    col_lengths = [0] * len(data[0])
    for row in data:
        for i, cell in enumerate(row):
            cell = str(cell)
            col_lengths[i] = max(col_lengths[i], len(cell))
    
    total_length = sum(col_lengths) or 1
    random_factor = random.uniform(0.9, 1.1)
    col_widths = [
        min(max(usable_width * prop * (col_lengths[i] / total_length) * random_factor, 0.5 * inch), usable_width * prop)
        for i, prop in enumerate(col_widths_proportions)
    ]
    total_width = sum(col_widths)
    if total_width > 0:
        col_widths = [w * usable_width / total_width for w in col_widths]
    return col_widths

def create_dynamic_statement(ctx, output_buffer):
    """
    Generate a dynamic PDF bank statement with a layout that varies by bank.
    
    Args:
        ctx (dict): Context dictionary with statement data and sections.
        output_buffer (BytesIO): Buffer to write the PDF to.
    
    Raises:
        ValueError: If required context keys are missing.
    """
    try:
        # Validate ctx
        required_keys = ['bank_name', 'account_holder', 'account_holder_address', 'account_type', 
                         'summary', 'transactions', 'website', 'contact', 'customer_account_number', 'sections']
        for key in required_keys:
            if key not in ctx:
                raise ValueError(f"Missing required context key: {key}")
        
        # Validate summary subkeys
        summary_keys = ['beginning_balance', 'deposits_total', 'withdrawals_total', 'ending_balance']
        for key in summary_keys:
            if key not in ctx['summary']:
                print(f"Warning: Missing summary key '{key}' for {ctx['bank_name']}, using default value")
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Missing summary key '{key}' for {ctx['bank_name']}"]
                ctx['summary'][key] = "$0.00"

        # Validate transaction data
        transaction_keys = ['date', 'description', 'deposits_credits', 'withdrawals_debits', 'ending_balance']
        for tx in ctx.get('transactions', []):
            for key in transaction_keys:
                if key not in tx:
                    print(f"Warning: Missing transaction key '{key}' for {ctx['bank_name']}, using empty string")
                    st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Missing transaction key '{key}' for {ctx['bank_name']}"]
                    tx[key] = ""

        bank_name = ctx['bank_name']
        c = canvas.Canvas(output_buffer, pagesize=letter)
        PAGE_WIDTH, PAGE_HEIGHT = letter
        margin = 0.5 * inch
        usable_width = PAGE_WIDTH - 2 * margin
        y_position = PAGE_HEIGHT - margin

        # Local helper function for text formatting
        def format_text(value, ctx):
            if isinstance(value, str):
                try:
                    return value.format(**{k: v for k, v in ctx.items() if isinstance(v, str)})
                except (KeyError, ValueError) as e:
                    print(f"Warning: Formatting failed for value '{value}': {e}")
                    st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Formatting failed for value '{value}' in {bank_name}: {e}"]
                    return value
            return str(value)

        # Render Header with logo
        logo_path = ctx.get('logo_path', '')
        logo_align = random.choice(['left', 'center', 'right'])
        if logo_path:
            try:
                img_data = open(logo_path, 'rb').read()
                img = Image.open(BytesIO(img_data))
                img_width, img_height = img.size
                target_width = 1.0 * inch if bank_name.lower() == 'wells fargo' else 1.5 * inch
                aspect_ratio = img_width / img_height if img_height > 0 else 1
                target_height = target_width / aspect_ratio
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, target_height + 40, "Helvetica", 12)
                x_logo = (margin if logo_align == 'left' else 
                          PAGE_WIDTH / 2 - target_width / 2 if logo_align == 'center' else 
                          PAGE_WIDTH - margin - target_width)
                c.drawImage(logo_path, x_logo, y_position - target_height - 10, 
                            width=target_width, height=target_height, mask='auto')
                y_position -= target_height + 40
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Logo rendered for {bank_name} at y={y_position + target_height + 40}, height={target_height}, extra whitespace=40pt"]
            except Exception as e:
                print(f"Warning: Failed to render logo for {bank_name}: {e}")
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Failed to render logo for {bank_name}: {e}"]
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 14, "Helvetica", 12)
                c.setFont("Helvetica", 12)
                c.drawString(margin, y_position, f"[Logo: {bank_name}]")
                y_position -= 14
        else:
            print(f"Warning: Logo path not provided for {bank_name}")
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Logo path not provided for {bank_name}"]
            y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 14, "Helvetica", 12)
            c.setFont("Helvetica", 12)
            c.drawString(margin, y_position, f"[Logo: {bank_name}]")
            y_position -= 14

        # Single-column header
        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 28, "Helvetica", 12)
        header_style = get_random_text_style(is_heading=True)
        c.setFont(header_style["font"], header_style["size"])
        c.setFillColor(header_style["color"])
        c.drawString(margin, y_position, format_text("{account_holder}", ctx))
        y_position -= header_style["size"] + 4
        address_lines = format_text("{account_holder_address}", ctx).split(',')
        body_style = get_random_text_style(is_heading=False)
        c.setFont(body_style["font"], body_style["size"])
        c.setFillColor(body_style["color"])
        for line in address_lines:
            line = line.strip()
            if line:
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, body_style["size"] + 4, body_style["font"], body_style["size"])
                c.drawString(margin, y_position, line)
                y_position -= body_style["size"] + 4
        title_style = get_random_text_style(is_heading=True)
        c.setFont(title_style["font"], title_style["size"])
        c.setFillColor(title_style["color"])
        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, title_style["size"] + 4, title_style["font"], title_style["size"])
        c.drawCentredString(PAGE_WIDTH / 2, y_position, format_text("{account_type} Statement", ctx))
        y_position -= title_style["size"] + 12

        # Get layout style from ctx or randomize
        layout_style = ctx.get('layout_style', 'sequential' if random.randint(0, 1) == 0 else 'two-column')
        print(f"Layout for {bank_name}: {layout_style}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Layout for {bank_name}: {layout_style}"]

        # Use user-defined sections
        middle_sections = ctx.get('sections', [])
        if not middle_sections:
            print(f"Warning: No sections provided for {bank_name}, using default sections")
            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: No sections provided for {bank_name}, using default sections"]
            middle_sections = [
                {
                    "title": "Important Account Information",
                    "content": [{
                        "type": "text",
                        "value": (
                            "Effective July 1, 2025, the monthly service fee for {account_type} accounts will increase to $15 unless you maintain a minimum daily balance of $1,500, have $500 in qualifying direct deposits, or maintain a linked savings account with a balance of $5,000 or more. "
                            "For questions, visit {website} or call {contact}."
                        ),
                        "font": "Helvetica",
                        "size": 10,
                        "wrap": True
                    }]
                },
                {
                    "title": "Account Summary",
                    "content": [{
                        "type": "table",
                        "data": [
                            ["Beginning Balance", ctx['summary']['beginning_balance']],
                            ["Deposits and Credits", ctx['summary']['deposits_total']],
                            ["Withdrawals and Debits", ctx['summary']['withdrawals_total']],
                            ["Ending Balance", ctx['summary']['ending_balance']]
                        ],
                        "col_widths": [0.75, 0.25],
                        "font": "Helvetica",
                        "size": 10,
                        "style": "none"
                    }]
                },
                {
                    "title": "Transaction History",
                    "content": [{
                        "type": "table",
                        "data_key": "transactions",
                        "headers": ["Date", "Description", "Amount", "Balance"],
                        "col_widths": [0.15, 0.45, 0.20, 0.20],
                        "font": "Helvetica",
                        "size": 10,
                        "style": "none"
                    }]
                }
            ]

        # Define section order
        def get_section_order(title):
            order = {
                "Welcome Message": 1,
                "Important Account Information": 2,
                "Account Summary": 3,
                "Transaction and Interest Summary": 4,
                "Transaction History": 5,
                "Daily Ending Balance": 6
            }
            return order.get(title, 10)

        # Sort sections
        middle_sections.sort(key=lambda x: get_section_order(x["title"]))

        # Render middle sections
        if layout_style == 'sequential':
            for section in middle_sections:
                section_style = get_random_text_style(is_heading=True)
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, section_style["size"] + 4, section_style["font"], section_style["size"])
                c.setFont(section_style["font"], section_style["size"])
                c.setFillColor(section_style["color"])
                if section["title"] == "Account Summary":
                    col_widths = calculate_dynamic_col_widths(
                        section["content"][0].get("data", []), 
                        usable_width, 
                        section["content"][0].get("col_widths", [0.75, 0.25])
                    )
                    table_width = sum(col_widths)
                    box_height = (len(section["content"][0]["data"]) * (section["content"][0]["size"] + 4) + 20 + 12)
                    c.setFillColor(colors.HexColor("#D3D3D3"))
                    c.setStrokeColor(colors.black)
                    c.rect(margin - 8, y_position - 20 + 8 - 4.5 * (section["content"][0]["size"] + 4), table_width + 16, box_height, fill=1, stroke=1)
                    c.setFillColor(section_style["color"])
                    c.setStrokeColor(colors.black)
                    c.drawString(margin + 8, y_position, section["title"])
                else:
                    c.drawString(margin + 8, y_position, section["title"])
                y_position -= section_style["size"] + 4

                for content in section["content"]:
                    content_style = get_random_text_style(is_heading=False)
                    c.setFont(content_style["font"], content_style["size"])
                    c.setFillColor(content_style["color"])
                    if content["type"] == "text":
                        lines = wrap_text(c, format_text(content["value"], ctx), content_style["font"], content_style["size"], usable_width)
                        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, len(lines) * (content_style["size"] + 4), content_style["font"], content_style["size"])
                        for line in lines:
                            c.drawString(margin + 8, y_position, line)
                            y_position -= content_style["size"] + 4
                    elif content["type"] == "table":
                        data = content.get("data", [])
                        if content.get("data_key") == "transactions":
                            data = []
                            for t in ctx.get("transactions", []):
                                amount = t.get("deposits_credits", "") or f"-{t.get('withdrawals_debits', '')}"
                                data.append([
                                    t.get("date", ""),
                                    t.get("description", ""),
                                    amount,
                                    t.get("ending_balance", "")
                                ])
                        elif content.get("data_key") == "daily_balances":
                            data = [[b.get("date", ""), b.get("amount", "")] for b in ctx.get("daily_balances", [])]
                            print(f"Daily balances table data for {bank_name}: {len(data)} rows")
                            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Daily balances table data for {bank_name}: {len(data)} rows"]
                        elif content.get("data_key") == "transaction_and_interest_summary":
                            data = [
                                ["Transaction Summary", ""],
                                ["Checks paid/written", ctx.get('summary', {}).get('checks_written', "0")],
                                ["Check-card POS transactions", ctx.get('summary', {}).get('pos_transactions', "0")],
                                ["Check-card/virtual POS PIN txn", ctx.get('summary', {}).get('pos_pin_transactions', "0")],
                                ["Total ATM transactions", ctx.get('summary', {}).get('total_atm_transactions', "0")],
                                ["PNC Bank ATM transactions", ctx.get('summary', {}).get('pnc_atm_transactions', "0")],
                                ["Other Bank ATM transactions", ctx.get('summary', {}).get('other_atm_transactions', "0")],
                                ["", ""],
                                ["Interest Summary", ""],
                                ["APY earned", ctx.get('summary', {}).get('apy_earned', "0.00%")],
                                ["Days in period", ctx.get('summary', {}).get('days_in_period', "30")],
                                ["Avg collected balance", ctx.get('summary', {}).get('average_collected_balance', "$0.00")],
                                ["Interest paid this period", ctx.get('summary', {}).get('interest_paid_period', "$0.00")],
                                ["YTD interest paid", ctx.get('summary', {}).get('interest_paid_ytd', "$0.00")]
                            ]
                        
                        if not data:
                            print(f"Warning: No data for table '{section['title']}' for {bank_name}")
                            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: No data for table '{section['title']}' for {bank_name}"]
                            data = [["No data available"] * len(content.get("headers", []))]

                        col_widths = calculate_dynamic_col_widths(data, usable_width, content.get("col_widths", [1/len(data[0])]*len(data[0])))
                        headers = content.get("headers", [])
                        row_height = content_style["size"] + 4
                        header_height = content_style["size"] + 4 if headers else 0

                        if headers and y_position - (header_height + row_height) >= margin:
                            for i, header in enumerate(headers):
                                x_pos = margin + sum(col_widths[:i])
                                if i in [2, 3] and section["title"] in ["Transaction History", "Daily Ending Balance"]:
                                    c.drawRightString(x_pos + col_widths[i] - 8, y_position, header)
                                else:
                                    c.drawString(x_pos + 8, y_position, header)
                            y_position -= content_style["size"] + 4
                        
                        for row in data:
                            y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, row_height, content_style["font"], content_style["size"], 
                                                         is_table=(section["title"] in ["Transaction History", "Daily Ending Balance"]), 
                                                         headers=headers, col_widths=col_widths)
                            for i, cell in enumerate(row):
                                x_pos = margin + sum(col_widths[:i])
                                cell = format_text(str(cell), ctx)
                                if isinstance(cell, str) and len(cell) > 50:
                                    cell = cell[:47] + "..."
                                if section["title"] == "Account Summary" and i == 1:
                                    c.drawCentredString(x_pos + col_widths[i] / 2, y_position, cell)
                                elif section["title"] in ["Transaction History", "Daily Ending Balance"] and i in [2, 3]:
                                    c.drawRightString(x_pos + col_widths[i] - 8, y_position, cell)
                                else:
                                    c.drawString(x_pos + 8, y_position, cell)
                            y_position -= content_style["size"] + 4
                        
                        if content.get("data_key") in ["transactions", "daily_balances", "transaction_and_interest_summary"] and data:
                            c.setStrokeColor(colors.black)
                            c.line(margin, y_position, margin + sum(col_widths), y_position)
                        y_position -= 12
                    y_position -= 12
        else:
            # Two-column layout
            col_width = usable_width / 2 - 10
            for section in middle_sections:
                section_style = get_random_text_style(is_heading=True)
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, section_style["size"] + 4, section_style["font"], section_style["size"])
                c.setFont(section_style["font"], section_style["size"])
                c.setFillColor(section_style["color"])
                c.drawString(margin + 8, y_position, section["title"])
                y_position -= section_style["size"] + 4

                for content in section["content"]:
                    content_style = get_random_text_style(is_heading=False)
                    c.setFont(content_style["font"], content_style["size"])
                    c.setFillColor(content_style["color"])
                    if content["type"] == "text":
                        lines = wrap_text(c, format_text(content["value"], ctx), content_style["font"], content_style["size"], col_width)
                        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, len(lines) * (content_style["size"] + 4), content_style["font"], content_style["size"])
                        for line in lines:
                            c.drawString(margin + 8, y_position, line)
                            y_position -= content_style["size"] + 4
                    elif content["type"] == "table":
                        data = content.get("data", [])
                        if content.get("data_key") == "transactions":
                            data = []
                            for t in ctx.get("transactions", []):
                                amount = t.get("deposits_credits", "") or f"-{t.get('withdrawals_debits', '')}"
                                data.append([
                                    t.get("date", ""),
                                    t.get("description", ""),
                                    amount,
                                    t.get("ending_balance", "")
                                ])
                        elif content.get("data_key") == "daily_balances":
                            data = [[b.get("date", ""), b.get("amount", "")] for b in ctx.get("daily_balances", [])]
                        elif content.get("data_key") == "transaction_and_interest_summary":
                            data = [
                                ["Transaction Summary", ""],
                                ["Checks paid/written", ctx.get('summary', {}).get('checks_written', "0")],
                                ["Check-card POS transactions", ctx.get('summary', {}).get('pos_transactions', "0")],
                                ["Check-card/virtual POS PIN txn", ctx.get('summary', {}).get('pos_pin_transactions', "0")],
                                ["Total ATM transactions", ctx.get('summary', {}).get('total_atm_transactions', "0")],
                                ["PNC Bank ATM transactions", ctx.get('summary', {}).get('pnc_atm_transactions', "0")],
                                ["Other Bank ATM transactions", ctx.get('summary', {}).get('other_atm_transactions', "0")],
                                ["", ""],
                                ["Interest Summary", ""],
                                ["APY earned", ctx.get('summary', {}).get('apy_earned', "0.00%")],
                                ["Days in period", ctx.get('summary', {}).get('days_in_period', "30")],
                                ["Avg collected balance", ctx.get('summary', {}).get('average_collected_balance', "$0.00")],
                                ["Interest paid this period", ctx.get('summary', {}).get('interest_paid_period', "$0.00")],
                                ["YTD interest paid", ctx.get('summary', {}).get('interest_paid_ytd', "$0.00")]
                            ]
                        
                        if not data:
                            print(f"Warning: No data for table '{section['title']}' for {bank_name}")
                            st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: No data for table '{section['title']}' for {bank_name}"]
                            data = [["No data available"] * len(content.get("headers", []))]

                        col_widths = calculate_dynamic_col_widths(data, col_width, content.get("col_widths", [1/len(data[0])]*len(data[0])))
                        headers = content.get("headers", [])
                        row_height = content_style["size"] + 4
                        header_height = content_style["size"] + 4 if headers else 0
                        
                        if headers and y_position - (header_height + row_height) >= margin:
                            for i, header in enumerate(headers):
                                x_pos = margin + sum(col_widths[:i])
                                if i in [2, 3] and section["title"] in ["Transaction History", "Daily Ending Balance"]:
                                    c.drawRightString(x_pos + col_widths[i] - 8, y_position, header)
                                else:
                                    c.drawString(x_pos + 8, y_position, header)
                            y_position -= content_style["size"] + 4
                        
                        for row in data:
                            y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, row_height, content_style["font"], content_style["size"], 
                                                         is_table=True, headers=headers, col_widths=col_widths)
                            for i, cell in enumerate(row):
                                x_pos = margin + sum(col_widths[:i])
                                cell = format_text(str(cell), ctx)
                                if isinstance(cell, str) and len(cell) > 50:
                                    cell = cell[:47] + "..."
                                if section["title"] == "Account Summary" and i == 1:
                                    c.drawCentredString(x_pos + col_widths[i] / 2, y_position, cell)
                                elif section["title"] in ["Transaction History", "Daily Ending Balance"] and i in [2, 3]:
                                    c.drawRightString(x_pos + col_widths[i] - 8, y_position, cell)
                                else:
                                    c.drawString(x_pos + 8, y_position, cell)
                            y_position -= content_style["size"] + 4
                        
                        if content.get("data_key") in ["transactions", "daily_balances", "transaction_and_interest_summary"] and data:
                            c.setStrokeColor(colors.black)
                            c.line(margin, y_position, margin + sum(col_widths), y_position)
                        y_position -= 12
                    y_position -= 12

        # Render Footer
        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 60, "Helvetica", 8)
        c.setStrokeColor(colors.black)
        c.line(margin, y_position + 20, margin + usable_width, y_position + 20)
        footer_style = get_random_text_style(is_heading=False)
        c.setFont(footer_style["font"], footer_style["size"])
        c.setFillColor(footer_style["color"])
        lines = wrap_text(
            c,
            format_text(
                "All account transactions are subject to the {bank_name} Deposit Account Agreement, available at {website}. "
                "Interest rates and Annual Percentage Yields (APYs) may change without notice. "
                "For details on overdraft policies and fees, visit {website}/overdraft or call {contact}. "
                f"© 2025 {bank_name} Bank, N.A. All rights reserved. Member FDIC.",
                ctx
            ),
            footer_style["font"],
            footer_style["size"],
            usable_width
        )
        for line in lines:
            y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, footer_style["size"] + 2, footer_style["font"], footer_style["size"])
            c.drawString(margin + 8, y_position, line)
            y_position -= footer_style["size"] + 2
        y_position -= 12

        c.save()
        print(f"PDF generated for {bank_name}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] PDF generated for {bank_name}"]
    
    except ValueError as e:
        print(f"Error in create_dynamic_statement for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error in create_dynamic_statement for {bank_name}: {str(e)}"]
        raise
    except Exception as e:
        print(f"Unexpected error in create_dynamic_statement for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Unexpected error in create_dynamic_statement for {bank_name}: {str(e)}"]
        raise