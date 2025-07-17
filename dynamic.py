from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import random
from PIL import Image
from io import BytesIO
import streamlit as st
from classic_functions import wrap_text, check_page_break, create_citi_classic, create_chase_classic, create_wellsfargo_classic, create_pnc_classic

def generate_pdf_statement(ctx, output_buffer):
    """
    Generate a PDF bank statement, choosing between dynamic or classic templates.
    
    Args:
        ctx (dict): Context dictionary with statement data.
        output_buffer (BytesIO): Buffer to write the PDF to.
    
    Raises:
        ValueError: If required context keys are missing or bank_name is unsupported.
    """
    bank_name = ctx.get('bank_name', 'Unknown')
    
    if ctx.get('use_classic_template', False):
        print(f"Using classic template for {bank_name}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Using classic template for {bank_name}"]
        
        classic_templates = {
            "Citibank": create_citi_classic,
            "Chase": create_chase_classic,
            "Wells Fargo": create_wellsfargo_classic,
            "PNC": create_pnc_classic
        }
        
        if bank_name not in classic_templates:
            raise ValueError(f"No classic template available for bank: {bank_name}")
        
        classic_templates[bank_name](ctx, output_buffer)
    else:
        print(f"Using dynamic template for {bank_name}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Using dynamic template for {bank_name}"]
        create_dynamic_statement(ctx, output_buffer)

def create_dynamic_statement(ctx, output_buffer):
    """
    Generate a dynamic PDF bank statement with a single-column or two-column layout based on ctx['layout_style'].
    
    Args:
        ctx (dict): Context dictionary with statement data.
        output_buffer (BytesIO): Buffer to write the PDF to.
    
    Raises:
        ValueError: If required context keys are missing.
    """
    try:
        bank_name = ctx.get('bank_name', 'Unknown')

        # Validate ctx
        required_keys = ['bank_name', 'account_holder', 'account_holder_address', 'bank_address_lines', 
                        'account_type', 'summary', 'transactions', 'website', 'contact', 'customer_account_number', 'logo_position']
        for key in required_keys:
            if key not in ctx:
                raise ValueError(f"Missing required context key: {key}")
        
        # Validate and calculate consistent summary from transactions
        transactions = ctx.get('transactions', [])
        currency = ctx.get('currency', '$')
        beginning_balance = float(ctx['summary'].get('beginning_balance', '0.00').replace(currency, '').replace(',', ''))
        deposits_total = sum(float(t.get('deposits_credits', '0.00').replace(currency, '').replace(',', '')) for t in transactions if t.get('deposits_credits'))
        withdrawals_total = sum(float(t.get('withdrawals_debits', '0.00').replace(currency, '').replace(',', '')) for t in transactions if t.get('withdrawals_debits'))
        running_balance = beginning_balance
        for t in transactions:
            if t.get('deposits_credits'):
                running_balance += float(t['deposits_credits'].replace(currency, '').replace(',', ''))
            if t.get('withdrawals_debits'):
                running_balance -= float(t['withdrawals_debits'].replace(currency, '').replace(',', ''))
        ending_balance = running_balance

        ctx['summary'] = {
            'beginning_balance': f"{currency}{beginning_balance:,.2f}",
            'deposits_total': f"{currency}{deposits_total:,.2f}",
            'withdrawals_total': f"{currency}{withdrawals_total:,.2f}",
            'ending_balance': f"{currency}{ending_balance:,.2f}",
            'checks_written': ctx['summary'].get('checks_written', '0'),
            'pos_transactions': ctx['summary'].get('pos_transactions', '0'),
            'pos_pin_transactions': ctx['summary'].get('pos_pin_transactions', '0'),
            'total_atm_transactions': ctx['summary'].get('total_atm_transactions', '0'),
            'pnc_atm_transactions': ctx['summary'].get('pnc_atm_transactions', '0'),
            'other_atm_transactions': ctx['summary'].get('other_atm_transactions', '0'),
            'apy_earned': ctx['summary'].get('apy_earned', '0.00%'),
            'days_in_period': ctx['summary'].get('days_in_period', '30'),
            'average_collected_balance': ctx['summary'].get('average_collected_balance', f"{currency}0.00"),
            'interest_paid_period': ctx['summary'].get('interest_paid_period', f"{currency}0.00"),
            'interest_paid_ytd': ctx['summary'].get('interest_paid_ytd', f"{currency}0.00")
        }

        transaction_keys = ['date', 'description', 'deposits_credits', 'withdrawals_debits', 'balance']
        for tx in transactions:
            for key in transaction_keys:
                if key not in tx:
                    print(f"Warning: Missing transaction key '{key}' for {bank_name}, using empty string")
                    st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Missing transaction key '{key}' for {bank_name}"]
                    tx[key] = ""

        c = canvas.Canvas(output_buffer, pagesize=letter)
        PAGE_WIDTH, PAGE_HEIGHT = letter
        margin = 0.5 * inch
        usable_width = PAGE_WIDTH - 2 * margin
        y_position = PAGE_HEIGHT - margin

        header_style = {"font": "Helvetica", "size": 12, "color": colors.black}
        doc_style = {"font": "Helvetica", "size": 10, "color": colors.black}
        footer_style = {"font": "Helvetica", "size": 9, "color": colors.black}

        def format_text(value, ctx):
            if isinstance(value, str):
                try:
                    return value.format(**{k: v for k, v in ctx.items() if isinstance(v, str)})
                except (KeyError, ValueError) as e:
                    print(f"Warning: Formatting failed for value '{value}': {e}")
                    st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Formatting failed for value '{value}' in {bank_name}: {e}"]
                    return value
            return str(value)

        logo_position = ctx.get('logo_position', 'left')
        logo_path = ctx.get('logo_path', '')
        logo_width = 1.5 * inch
        logo_x_position = margin
        if logo_position == 'right':
            logo_x_position = PAGE_WIDTH - margin - logo_width
        elif logo_position == 'center':
            logo_x_position = (PAGE_WIDTH - logo_width) / 2

        if logo_path:
            try:
                img_data = open(logo_path, 'rb').read()
                img = Image.open(BytesIO(img_data))
                img_width, img_height = img.size
                target_width = logo_width
                aspect_ratio = img_width / img_height if img_height > 0 else 1
                target_height = target_width / aspect_ratio
                y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, target_height + 10, doc_style["font"], doc_style["size"])
                c.drawImage(logo_path, logo_x_position, y_position - target_height - 10, width=target_width, height=target_height, mask='auto')
                y_position -= target_height + 10
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Logo rendered for {bank_name} at {logo_position}"]
            except Exception as e:
                print(f"Warning: Failed to render logo for {bank_name}: {e}")
                st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Warning: Failed to render logo for {bank_name}: {e}"]
                y_position -= 20
        else:
            y_position -= 20

        y_position -= (doc_style["size"] + 12) / 2

        bank_x_position = margin
        customer_x_position = PAGE_WIDTH - margin
        if logo_position == 'right':
            bank_x_position = PAGE_WIDTH - margin
            customer_x_position = margin
        elif logo_position == 'center':
            if random.randint(0, 1) == 0:
                bank_x_position = margin
                customer_x_position = PAGE_WIDTH - margin
            else:
                bank_x_position = PAGE_WIDTH - margin
                customer_x_position = margin

        c.setFont(doc_style["font"], doc_style["size"])
        c.setFillColor(doc_style["color"])
        address_lines = format_text("{account_holder_address}", ctx).split(',')
        customer_address_lines = [
            format_text("{account_holder}", ctx),
            address_lines[0].strip() if address_lines else "",
            ", ".join(address_lines[1:]).strip() if len(address_lines) > 1 else ""
        ]

        for i in range(3):
            if y_position - 10 < margin:
                c.showPage()
                y_position = PAGE_HEIGHT - margin
                c.setFont(doc_style["font"], doc_style["size"])
            bank_line = ctx.get('bank_address_lines', [''] * 3)[i]
            if bank_x_position > PAGE_WIDTH / 2:
                c.drawRightString(bank_x_position, y_position, format_text(bank_line, ctx))
            else:
                c.drawString(bank_x_position, y_position, format_text(bank_line, ctx))
            customer_line = customer_address_lines[i] if i < len(customer_address_lines) else ""
            if customer_x_position > PAGE_WIDTH / 2:
                c.drawRightString(customer_x_position, y_position, customer_line)
            else:
                c.drawString(customer_x_position, y_position, customer_line)
            y_position -= doc_style["size"] + 4

        y_position -= 2 * (doc_style["size"] + 4)

        layout_style = ctx.get('layout_style', 'sequential')
        if layout_style == 'two-column':
            column_width = usable_width / 2 - 0.25 * inch
            column_margin_left = margin
            column_margin_right = margin + usable_width / 2 + 0.25 * inch
            left_y_position = y_position
            right_y_position = y_position
            current_column = 'left'
        else:
            column_width = usable_width
            column_margin_left = margin
            column_margin_right = margin
            left_y_position = y_position
            right_y_position = y_position
            current_column = 'left'

        for section in ctx.get('sections', []):
            if section["title"] == "Bank Address":
                continue
            if layout_style == 'two-column':
                x_position = column_margin_left if current_column == 'left' else column_margin_right
                y_position = left_y_position if current_column == 'left' else right_y_position
            else:
                x_position = margin
                y_position = left_y_position

            y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 16, header_style["font"], header_style["size"])
            
            box_height = 0
            if section["title"] in ["Customer Service", "Account Summary"]:
                box_height += header_style["size"] + 4
                for content in section["content"]:
                    if content["type"] == "text":
                        lines = wrap_text(c, format_text(content["value"], ctx), doc_style["font"], doc_style["size"], column_width)
                        box_height += len(lines) * (doc_style["size"] + 4)
                    elif content["type"] == "table":
                        data = content.get("data", [])
                        box_height += len(data) * (doc_style["size"] + 4) + 12
                box_height += 8

            if section["title"] == "Customer Service":
                c.setFillColor(colors.lightblue if bank_name in ["Chase", "Citibank"] else 
                              colors.lightcoral if bank_name == "Wells Fargo" else 
                              colors.lightsalmon)
                col_widths = [column_width * w for w in [0.375, 0.625]] if layout_style == 'two-column' else [column_width * w for w in [0.375, 0.125]]
                c.rect(x_position - 4, y_position - box_height + 24, sum(col_widths) + 8, box_height - 6, fill=1)
                c.setFillColor(header_style["color"])

            account_summary_decoration = None
            if section["title"] == "Account Summary":
                account_summary_decoration = random.choice(["box", "colored_box", "gridline"])

            if section["title"] == "Account Summary" and account_summary_decoration in ["box", "colored_box"]:
                col_widths = [column_width * w for w in [0.375, 0.625]] if layout_style == 'two-column' else [column_width * w for w in [0.375, 0.125]]
                if account_summary_decoration == "colored_box":
                    c.setFillColor(colors.lightblue if bank_name in ["Chase", "Citibank"] else 
                                  colors.lightcoral if bank_name == "Wells Fargo" else 
                                  colors.lightsalmon)
                    c.rect(x_position - 4, y_position - box_height - 30, sum(col_widths) + 8, box_height + 42, fill=1)
                    c.setFillColor(header_style["color"])
                else:
                    c.setStrokeColor(colors.black)
                    c.rect(x_position - 4, y_position - box_height - 30, sum(col_widths) + 8, box_height + 42, fill=0)

            c.setFont(header_style["font"], header_style["size"])
            c.setFillColor(header_style["color"])
            if section["title"] == "Transaction History":
                c.drawString(x_position, y_position, section["title"])
                date_range = format_text("{statement_period}", ctx)
                c.setFont(header_style["font"], 10)
                date_width = c.stringWidth(date_range, header_style["font"], 10)
                c.drawString(x_position + column_width - date_width - 2, y_position, date_range)
                c.setFont(header_style["font"], header_style["size"])
            else:
                c.drawString(x_position, y_position, section["title"])
            y_position -= header_style["size"] + 4

            for content in section["content"]:
                c.setFont(doc_style["font"], doc_style["size"])
                c.setFillColor(doc_style["color"])
                if content["type"] == "text":
                    lines = wrap_text(c, format_text(content["value"], ctx), doc_style["font"], doc_style["size"], column_width)
                    for line in lines:
                        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 10, doc_style["font"], doc_style["size"])
                        c.drawString(x_position, y_position, line)
                        y_position -= doc_style["size"] + 4
                elif content["type"] == "table":
                    data = content.get("data", [])
                    if content.get("data_key") == "transactions":
                        data = [
                            [
                                t.get("date", ""),
                                t.get("description", "")[:20] + "..." if layout_style == "two-column" and len(t.get("description", "")) > 20 else t.get("description", ""),
                                t.get("deposits_credits", "") or f"-{t.get('withdrawals_debits', '')}",
                                t.get("balance", "")
                            ] for t in ctx.get("transactions", [])
                        ]
                    elif content.get("data_key") == "daily_balances":
                        data = [[b.get("date", ""), b.get("amount", "")] for b in ctx.get("daily_balances", [])]
                    elif content.get("data_key") == "transaction_and_interest_summary":
                        data = [
                            ["Transaction Summary", "", "", ""],
                            ["Checks paid/written", ctx.get('summary', {}).get('checks_written', "0"), "", ""],
                            ["Check-card POS transactions", ctx.get('summary', {}).get('pos_transactions', "0"), "", ""],
                            ["Check-card/virtual POS PIN txn", ctx.get('summary', {}).get('pos_pin_transactions', "0"), "", ""],
                            ["Total ATM transactions", ctx.get('summary', {}).get('total_atm_transactions', "0"), "", ""],
                            ["PNC Bank ATM transactions", ctx.get('summary', {}).get('pnc_atm_transactions', "0"), "", ""],
                            ["Other Bank ATM transactions", ctx.get('summary', {}).get('other_atm_transactions', "0"), "", ""],
                            ["", "", "", ""],
                            ["Interest Summary", "", "", ""],
                            ["APY earned", ctx.get('summary', {}).get('apy_earned', "0.00%"), "", ""],
                            ["Days in period", ctx.get('summary', {}).get('days_in_period', "30"), "", ""],
                            ["Avg collected balance", ctx.get('summary', {}).get('average_collected_balance', "$0.00"), "", ""],
                            ["Interest paid this period", ctx.get('summary', {}).get('interest_paid_period', "$0.00"), "", ""],
                            ["YTD interest paid", ctx.get('summary', {}).get('interest_paid_ytd', "$0.00"), "", ""]
                        ]
                    elif content.get("data_key") == "account_summary":
                        data = [
                            ["Beginning Balance", ctx.get('summary', {}).get('beginning_balance', "$0.00")],
                            ["Deposits or Credits", ctx.get('summary', {}).get('deposits_total', "$0.00")],
                            ["Withdrawals or Debits", ctx.get('summary', {}).get('withdrawals_total', "$0.00")],
                            ["Ending Balance", ctx.get('summary', {}).get('ending_balance', "$0.00")]
                        ]

                    if not data and content.get("data_key"):
                        data = [["No data available", ""]]

                    col_widths = content.get("col_widths", [1/max(1, len(data[0]))]*len(data[0]))
                    if layout_style == 'two-column' and section["title"] in ["Customer Service", "Account Summary", "Daily Ending Balance"]:
                        col_widths = [0.375, 0.625]
                    elif layout_style == 'two-column' and section["title"] == "Transaction and Interest Summary":
                        col_widths = [0.375, 0.625, 0.375, 0.625]
                    col_widths = [column_width * w for w in col_widths]

                    headers = content.get("headers", [])
                    if headers:
                        if content.get("data_key") == "transactions":
                            c.setFillColor(colors.lightgrey)
                            c.rect(x_position - 2, y_position - header_style["size"] + (doc_style["size"] + 5) / 2, sum(col_widths) + 4, header_style["size"] + 5, fill=1)
                            c.setFillColor(header_style["color"])
                        c.setFont(header_style["font"], header_style["size"])
                        for i, header in enumerate(headers):
                            if i < len(col_widths):
                                x_pos = x_position + sum(col_widths[:i])
                                if content.get("data_key") == "transactions" and i > 1:
                                    header_width = c.stringWidth(header, header_style["font"], header_style["size"])
                                    adjusted_x_pos = x_pos + col_widths[i] - header_width - 2
                                    c.drawString(adjusted_x_pos, y_position, header)
                                else:
                                    c.drawString(x_pos, y_position, header)
                        y_position -= header_style["size"] + 4

                    c.setFont(doc_style["font"], doc_style["size"])
                    c.setFillColor(doc_style["color"])
                    row_y_positions = []
                    for row_idx, row in enumerate(data):
                        y_position = check_page_break(c, y_position, margin, PAGE_HEIGHT, 10, doc_style["font"], doc_style["size"], is_table=True, headers=headers, col_widths=col_widths)
                        row_y_positions.append(y_position)
                        for i, cell in enumerate(row):
                            if i < len(col_widths):
                                x_pos = x_position + sum(col_widths[:i])
                                cell = format_text(str(cell), ctx)
                                if (content.get("data_key") == "transactions" and i > 1) or \
                                   (section["title"] in ["Customer Service", "Account Summary", "Daily Ending Balance"] and i > 0) or \
                                   (section["title"] == "Transaction and Interest Summary" and i in [1, 3]):
                                    cell_width = c.stringWidth(cell, doc_style["font"], doc_style["size"])
                                    adjusted_x_pos = x_pos + col_widths[i] - cell_width - 2
                                    c.drawString(adjusted_x_pos, y_position, cell)
                                else:
                                    c.drawString(x_pos, y_position, cell)
                        y_position -= doc_style["size"] + 4
                    y_position -= 12

                    if section["title"] == "Account Summary" and account_summary_decoration == "gridline":
                        c.setStrokeColor(colors.black)
                        for y in row_y_positions + [row_y_positions[0] + doc_style["size"] + 4]:
                            c.line(x_position, y - 3.5, x_position + sum(col_widths), y - 3.5)
                        c.line(x_position + sum(col_widths) / 2, row_y_positions[-1] - 3.5, x_position + sum(col_widths) / 2, row_y_positions[0] + doc_style["size"] + 4 - 3.5)

                    if content.get("data_key") == "transactions":
                        c.setStrokeColor(colors.black)
                        c.line(x_position, y_position + 16, x_position + sum(col_widths), y_position + 16)

            y_position -= 12
            if section["title"] == "Important Account Information":
                y_position -= doc_style["size"] + 4

            if layout_style == 'two-column':
                if current_column == 'left':
                    left_y_position = y_position
                    current_column = 'right'
                else:
                    right_y_position = y_position
                    current_column = 'left'
                    if right_y_position < left_y_position:
                        left_y_position = right_y_position
            else:
                left_y_position = y_position
                right_y_position = y_position

        if min(left_y_position, right_y_position) - 60 < margin:
            c.showPage()
            left_y_position = PAGE_HEIGHT - margin
            right_y_position = PAGE_HEIGHT - margin
            c.setFont(doc_style["font"], doc_style["size"])
        c.setStrokeColor(colors.black)
        c.line(margin, min(left_y_position, right_y_position) + 20, margin + usable_width, min(left_y_position, right_y_position) + 20)
        c.setFont(footer_style["font"], footer_style["size"])
        c.setFillColor(footer_style["color"])
        lines = wrap_text(c, format_text(
            "All account transactions are subject to the {bank_name} Deposit Account Agreement, available at {website}. "
            "For details, call {contact}. © 2025 {bank_name} Bank, N.A. Member FDIC.",
            ctx
        ), footer_style["font"], footer_style["size"], usable_width)
        for line in lines:
            if min(left_y_position, right_y_position) - 10 < margin:
                c.showPage()
                left_y_position = PAGE_HEIGHT - margin
                right_y_position = PAGE_HEIGHT - margin
                c.setFont(footer_style["font"], footer_style["size"])
            c.drawString(margin, min(left_y_position, right_y_position), line)
            left_y_position -= footer_style["size"] + 2
            right_y_position -= footer_style["size"] + 2
        left_y_position -= 12
        right_y_position -= 12

        c.save()
        print(f"PDF generated for {bank_name} with {layout_style} layout and logo at {ctx.get('logo_position', 'left')}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] PDF generated for {bank_name} with {layout_style} layout and logo at {ctx.get('logo_position', 'left')}"]
    
    except ValueError as e:
        print(f"Error in create_dynamic_statement for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error in create_dynamic_statement for {bank_name}: {str(e)}"]
        raise
    except Exception as e:
        print(f"Unexpected error in create_dynamic_statement for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Unexpected error in create_dynamic_statement for {bank_name}: {str(e)}"]
        raise