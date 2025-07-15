
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from faker import Faker
import os
import random
from datetime import datetime, timedelta


def generate_statement_data(bank_name, base_dir="."):
    fake = Faker()
    Faker.seed(random.randint(0, 1000000))
    output_dir = os.path.join(base_dir, "synthetic_statements")
    logo_dir = os.path.join(base_dir, "sample_logos")

    # Bank-specific configurations
    bank_configs = {
        "Chase": {
            "full_name": "JPMorgan Chase Bank, N.A.",
            "address": "PO Box 659754, San Antonio, TX 78265-9754",
            "logo": os.path.join(logo_dir, "chase_bank_logo.png"),
            "contact": "1-800-242-7338",
            "website": "chase.com",
            "currency": "$"
        },
        "Wells Fargo": {
            "full_name": "Wells Fargo Bank, N.A.",
            "address": "420 Montgomery Street, San Francisco, CA 94104",
            "logo": os.path.join(logo_dir, "wellsfargo_logo.png"),
            "contact": "1-800-225-5935",
            "website": "wellsfargo.com",
            "currency": "$"
        },
        "PNC": {
            "full_name": "PNC Bank, National Association",
            "address": "249 Fifth Avenue, Pittsburgh, PA 15222",
            "logo": os.path.join(logo_dir, "pnc_logo.png"),
            "contact": "1-888-PNC-BANK",
            "website": "pnc.com",
            "currency": "$"
        },
        "Citibank": {
            "full_name": "Citibank, N.A.",
            "address": "388 Greenwich Street, New York, NY 10013",
            "logo": os.path.join(logo_dir, "citibank_logo.png"),
            "contact": "1-800-374-9700",
            "website": "citibank.com",
            "currency": "£"
        }
    }

    # Validate bank_name
    if bank_name not in bank_configs:
        raise ValueError(f"Unsupported bank: {bank_name}")

    config = bank_configs[bank_name]
    
    # Verify logo path
    if not os.path.exists(config["logo"]):
        print(f"Warning: Logo file {config['logo']} not found for {bank_name}.")
        config["logo"] = None
    
    # Generate synthetic account data
    account_holder = fake.name()
    account_holder_address = fake.address().replace('\n', ', ')
    account_number = fake.bban()
    account_type = random.choice(["Chase Total Checking", "Chase Business Complete Checking"]) if bank_name == "Chase" else \
                   random.choice(["Everyday Checking", "Business Checking"]) if bank_name == "Wells Fargo" else \
                   random.choice(["Standard Checking", "Business Checking"]) if bank_name == "PNC" else \
                   random.choice(["Citi Checking", "Citi Business Checking"])
    
    # Statement period
    end_date = fake.date_between(start_date='-30d', end_date='today')
    start_date = end_date - timedelta(days=30)
    statement_period = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
    statement_date = end_date.strftime('%B %d, %Y')

    # Generate transactions with realistic descriptions
    transactions = []
    balance = round(random.uniform(1000, 10000), 2)
    beginning_balance = balance
    deposits_count = 0
    withdrawals_count = 0
    deposits_total = 0.0
    withdrawals_total = 0.0
    daily_balances = []

    # Realistic transaction descriptions
    deposit_descriptions = [
        "Direct Deposit", "ATM Deposit", "Mobile Deposit", "Payroll Credit",
        "Refund", "Transfer from Savings", "Cash Deposit"
    ]
    withdrawal_descriptions = [
        "ATM Withdrawal", "Debit Card Purchase", "Online Bill Pay",
        "Check Payment", "Transfer to Savings", "Merchant Payment"
    ]

    for _ in range(random.randint(10, 20)):
        trans_date = fake.date_between(start_date=start_date, end_date=end_date).strftime('%m/%d')
        trans_type = random.choice(["credit", "debit"])
        amount = round(random.uniform(10, 1000), 2)
        
        if trans_type == "credit":
            description = random.choice(deposit_descriptions)
            credit = f"{config['currency']}{amount:.2f}"
            debit = ""
            balance += amount
            deposits_count += 1
            deposits_total += amount
        else:
            description = random.choice(withdrawal_descriptions)
            credit = ""
            debit = f"{config['currency']}{amount:.2f}"
            balance -= amount
            withdrawals_count += 1
            withdrawals_total += amount
        
        transaction = {
            "date": trans_date,
            "description": description,
            "credit": credit,
            "debit": debit,
            "balance": f"{config['currency']}{balance:.2f}",
            "deposits_credits": credit,
            "withdrawals_debits": debit,
            "ending_balance": f"{config['currency']}{balance:.2f}"
        }
        transactions.append(transaction)

    # Validate deposits and withdrawals
    deposits = [t for t in transactions if t['credit']]
    withdrawals = [t for t in transactions if t['debit']]

    # Generate daily balances
    current_balance = beginning_balance
    for n in range((end_date - start_date).days + 1):
        current_date = (start_date + timedelta(days=n)).strftime('%m/%d')
        daily_transactions = [t for t in transactions if t['date'] == current_date]
        for t in daily_transactions:
            if t['credit']:
                current_balance += float(t['credit'].replace(config['currency'], ''))
            if t['debit']:
                current_balance -= float(t['debit'].replace(config['currency'], ''))
        daily_balances.append({
            "date": current_date,
            "amount": f"{config['currency']}{current_balance:.2f}"
        })

    # Context dictionary
    ctx = {
        "bank_name": bank_name,
        "customer_bank_name": config["full_name"],
        "account_holder": account_holder,
        "account_holder_address": account_holder_address,
        "customer_account_number": account_number,
        "account_type": account_type,
        "statement_period": statement_period,
        "statement_date": statement_date,
        "logo_path": config["logo"],
        "currency": config["currency"],
        "website": config["website"],  # Added to top-level ctx
        "contact": config["contact"],  # Added to top-level ctx
        "summary": {
            "beginning_balance": f"{config['currency']}{beginning_balance:.2f}",
            "deposits_count": str(deposits_count),
            "deposits_total": f"{config['currency']}{deposits_total:.2f}",
            "withdrawals_count": str(withdrawals_count),
            "withdrawals_total": f"{config['currency']}{withdrawals_total:.2f}",
            "ending_balance": f"{config['currency']}{balance:.2f}",
            "transactions_count": str(len(transactions)),
            "overdraft_protection1": "None",
            "overdraft_status": "opted out",
            "average_balance": f"{config['currency']}{round(random.uniform(1000, 10000), 2):.2f}",
            "fees": f"{config['currency']}{round(random.uniform(0, 50), 2):.2f}",
            "checks_written": str(random.randint(0, 5)),
            "pos_transactions": str(random.randint(0, 10)),
            "pos_pin_transactions": str(random.randint(0, 5)),
            "total_atm_transactions": str(random.randint(0, 5)),
            "pnc_atm_transactions": str(random.randint(0, 3)),
            "other_atm_transactions": str(random.randint(0, 2)),
            "apy_earned": f"{random.uniform(0.01, 0.05):.2%}",
            "days_in_period": "30",
            "average_collected_balance": f"{config['currency']}{round(random.uniform(1000, 10000), 2):.2f}",
            "interest_paid_period": f"{config['currency']}{round(random.uniform(0, 10), 2):.2f}",
            "interest_paid_ytd": f"{config['currency']}{round(random.uniform(0, 50), 2):.2f}"
        },
        "transactions": transactions,
        "deposits": deposits,
        "withdrawals": withdrawals,
        "daily_balances": daily_balances,
        "show_fee_waiver": random.choice([True, False]),
        "customer_iban": fake.iban() if bank_name == "Citibank" else "",
        "client_number": fake.uuid4() if bank_name == "Citibank" else "",
        "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%m/%d/%Y') if bank_name == "Citibank" else "",
        "total_pages": 1
    }

    return ctx

# Generate bank-specific data
pnc_ctx = generate_statement_data("PNC")
citi_ctx = generate_statement_data("Citibank")
chase_ctx = generate_statement_data("Chase")
wellsfargo_ctx = generate_statement_data("Wells Fargo")


# Cell 3a: Citibank Classic

def create_citi_classic(ctx, output_dir="out"):
    output_file = os.path.join(output_dir, f"citibank_statement_{ctx['customer_account_number'][-4:]}.pdf")
    c = canvas.Canvas(output_file, pagesize=letter)
    PAGE_WIDTH, PAGE_HEIGHT = letter
    margin = 0.5 * inch
    usable_width = PAGE_WIDTH - 2 * margin
    y_position = PAGE_HEIGHT - margin

    # Helper function to wrap text
    def wrap_text(text, font_size, max_width):
        c.setFont("Helvetica", font_size)
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        for word in words:
            word_width = c.stringWidth(word + " ", "Helvetica", font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    # Header
    if os.path.exists(ctx['logo_path']):
        c.drawImage(ctx['logo_path'], PAGE_WIDTH - margin - 150, y_position - 50, width=1.91*inch, height=0.64*inch, mask='auto')
    else:
        print(f"Warning: Logo file {ctx['logo_path']} not found.")
    
    c.setFillColor(colors.HexColor("#003e7e"))
    c.rect(margin, y_position - 60, usable_width, 4, fill=1)
    y_position -= 72  # Adjust for logo and line

    # Bank and Customer Information (Two-Column Layout)
    left_x = margin
    right_x = margin + usable_width / 2
    y_position_left = y_position
    y_position_right = y_position

    # Bank Information (Left Column)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left_x, y_position_left, "Bank information")
    y_position_left -= 12
    c.setFont("Helvetica", 9)
    c.drawString(left_x, y_position_left, f"Account Provider Name: {ctx['customer_bank_name']}")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, f"Account Name: {ctx['account_type']}")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, f"IBAN: {ctx.get('customer_iban', 'GB29CITI' + ctx['customer_account_number'])}")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, "Country code: GB")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, f"Check Digits: {ctx.get('customer_iban', 'GB29')[2:4]}")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, "Bank code: CITI")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, f"British bank code (sort code): {ctx.get('customer_iban', 'GB29CITI123456')[8:14]}")
    y_position_left -= 12
    c.drawString(left_x, y_position_left, f"Bank account number: {ctx['customer_account_number']}")

    # Customer Information (Right Column)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(right_x, y_position_right, "Customer information")
    y_position_right -= 12
    c.setFont("Helvetica", 9)
    c.drawString(right_x, y_position_right, f"Client Name: {ctx['account_holder']}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, f"Client number ID: {ctx.get('client_number', fake.uuid4())}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, f"Date of birth: {ctx.get('date_of_birth', fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'))}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, f"Account number: {ctx['customer_account_number']}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, f"IBAN Bank: {ctx.get('customer_iban', 'GB29CITI' + ctx['customer_account_number'])}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, f"Bank name: {ctx['customer_bank_name']}")
    
    y_position = min(y_position_left, y_position_right) - 24  # Space after both columns

    # Important Account Information
    c.setFont("Helvetica", 12)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, "Important Account Information")
    y_position -= 18
    if ctx['account_type'] == "Citi Access Checking":
        info_text = (
            "Effective July 1, 2025, the monthly account fee for Citi Access Checking accounts will increase to £10 unless you maintain a minimum daily balance of £1,500 or have qualifying direct deposits of £500 or more per month. "
            "Starting June 30, 2025, Citibank will introduce real-time transaction alerts for Citi Access Checking accounts via the Citi Mobile UK app. Enable alerts at citibank.co.uk/alerts. "
            "Effective July 15, 2025, Citibank will waive overdraft fees for transactions of £5 or less and cap daily overdraft fees at two per day for Citi Access Checking accounts. "
            "For questions, visit citibank.co.uk or contact our Client Contact Centre at 0800 005 555 (or +44 20 7500 5500 from abroad), available 24/7."
        )
    else:
        info_text = (
            "Effective July 1, 2025, the monthly account fee for CitiBusiness Checking accounts will increase to £15 unless you maintain a minimum daily balance of £5,000 or have £2,000 in net purchases on a Citi Business Debit Card per month. "
            "Starting June 30, 2025, Citibank will offer enhanced cash flow tools for CitiBusiness Checking accounts via Citi Online Banking, including automated invoice tracking and payment scheduling. "
            "Effective July 15, 2025, Citibank will reduce domestic BACS transfer fees to £20 for CitiBusiness Checking accounts, down from £25. "
            "For questions, visit citibank.co.uk or contact our Client Contact Centre at 0800 005 555 (or +44 20 7500 5500 from abroad), available 24/7."
        )
    c.setFont("Helvetica", 9)
    wrapped_text = wrap_text(info_text.replace("\n", " "), 9, usable_width)
    for line in wrapped_text:
        y_position -= 12
        if y_position < margin:
            c.showPage()
            y_position = PAGE_HEIGHT - margin
        c.drawString(margin, y_position, line)
    y_position -= 24  # Add gap before Account Transactions

    # Account Transactions
    c.setFont("Helvetica", 12)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, "Account Transactions")
    y_position -= 18
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['statement_period'])
    y_position -= 12
    c.drawRightString(PAGE_WIDTH - margin, y_position, f"Created on {ctx['statement_date']}")
    y_position -= 12

    # Transactions Table
    col_widths = [0.15 * usable_width, 0.36 * usable_width, 0.12 * usable_width, 0.12 * usable_width, 0.12 * usable_width]
    header_y = y_position

    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, header_y, "Date")
    c.drawString(margin + col_widths[0], header_y, "Information")
    c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2], header_y, "Debit")
    c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], header_y, "Credit")
    c.drawRightString(PAGE_WIDTH - margin, header_y, "Balance")
    y_position -= 12
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)  # Header line

    y_position -= 12
    c.setFont("Helvetica", 9)
    c.drawString(margin, y_position, "")
    c.drawString(margin + col_widths[0], y_position, "Opening balance")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['beginning_balance'])
    y_position -= 12
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)  # Separator line

    for transaction in ctx['transactions']:
        desc = transaction["description"]
        if len(desc) > 25:
            desc = desc[:25] + "..."
        y_position -= 12
        if y_position < margin:
            c.showPage()
            y_position = PAGE_HEIGHT - margin
            c.setFont("Helvetica", 9)
        c.drawString(margin, y_position, transaction["date"])
        c.drawString(margin + col_widths[0], y_position, desc)
        c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2], y_position, transaction["debit"])
        c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y_position, transaction["credit"])
        c.drawRightString(PAGE_WIDTH - margin, y_position, transaction["balance"])

    y_position -= 12
    if y_position < margin:
        c.showPage()
        y_position = PAGE_HEIGHT - margin
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y_position, "")
    c.drawString(margin + col_widths[0], y_position, "Total")
    c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2], y_position, ctx['summary']['withdrawals_total'])
    c.drawRightString(margin + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y_position, ctx['summary']['deposits_total'])
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['ending_balance'])
    y_position -= 12
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)  # Total line

    # Notice
    y_position -= 24
    if y_position < margin:
        c.showPage()
        y_position = PAGE_HEIGHT - margin
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, "This printout is for information purposes only. Your regular account statement of assets takes precedence.")
    y_position -= 24

    # Footer
    footer_height = 4 + 3 * 9 + 12 + 8  # Rectangle (4pt) + 3 lines (9pt each) + final spacing (12pt) + initial gap (8pt)
    if y_position < margin + footer_height:  # Check if enough space for footer
        c.showPage()
        y_position = PAGE_HEIGHT - margin

    c.setFillColor(colors.HexColor("#003e7e"))
    c.rect(margin, y_position, usable_width, 4, fill=1)
    y_position -= 8

    c.setFont("Helvetica", 7)
    c.drawString(margin, y_position, "Citigroup UK Limited is authorised by the Prudential Regulation Authority and regulated by the Financial Conduct Authority and the Prudential Regulation Authority.")
    y_position -= 8  # Reduced from 9 to save space
    c.drawString(margin, y_position, "Our firm’s Financial Services Register number is 805574. Citibank UK Limited is a company limited by shares registered in England and Wales with registered address at Citigroup Centre, Canada Square, Canary Wharf, London E14 5LB.")
    y_position -= 8  # Reduced from 9 to save space
    c.drawString(margin, y_position, "© All rights reserved Citibank UK Limited 2021. CITI, the Arc Design & Citibank are registered service marks of Citigroup Inc. Calls may be monitored or recorded for training and service quality purposes. PNB FBD 132019.")
    y_position -= 10  # Reduced from 12 to save space
    c.drawRightString(PAGE_WIDTH - margin, y_position, "Citibank")

    c.save()
    print(f"PDF generated: {output_file}")




# Cell 3b: Chase Classic 


def create_chase_classic(ctx, output_dir="out"):
    output_file = os.path.join(output_dir, f"chase_classic_statement_{ctx['customer_account_number'][-4:]}.pdf")
    c = canvas.Canvas(output_file, pagesize=letter)
    PAGE_WIDTH, PAGE_HEIGHT = letter
    MARGIN = 30  # 40px ≈ 30pt
    usable_width = PAGE_WIDTH - 2 * MARGIN
    y_position = PAGE_HEIGHT - MARGIN

    # Helper function to wrap text
    def wrap_text(text, font_size, max_width):
        c.setFont("Helvetica", font_size)
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        for word in words:
            word_width = c.stringWidth(word + " ", "Helvetica", font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    # Header
    c.setFont("Helvetica", 10.5)
    if os.path.exists(ctx['logo_path']):
        c.drawImage(ctx['logo_path'], MARGIN, y_position - 36, width=90, height=36, mask='auto')
        y_position -= 45
    else:
        print(f"Warning: Logo file {ctx['logo_path']} not found.")
    c.drawString(MARGIN, y_position, "JPMorgan Chase Bank, N.A.")
    y_position -= 13.5
    c.drawString(MARGIN, y_position, "PO Box 659754")
    y_position -= 13.5
    c.drawString(MARGIN, y_position, "San Antonio, TX 78265-9754")
    
    # Customer Service (right side)
    right_x = PAGE_WIDTH - MARGIN - 270  # 360px ≈ 270pt table width
    y_position_right = PAGE_HEIGHT - MARGIN
    c.setFont("Helvetica-Bold", 9)
    c.drawString(right_x, y_position_right, ctx['statement_period'])
    y_position_right -= 13.5
    c.drawString(right_x, y_position_right, f"Account Number: {ctx['customer_account_number']}")
    y_position_right -= 13.5
    c.setFont("Helvetica-Bold", 9)
    c.drawString(right_x, y_position_right, "CUSTOMER SERVICE INFORMATION")
    c.setLineWidth(3)
    c.line(right_x, y_position_right + 9.5, right_x + 270, y_position_right + 9.5)  # Top border
    c.line(right_x, y_position_right - 4, right_x + 270, y_position_right - 4)  # Bottom border
    y_position_right -= 13.5
    c.setFont("Helvetica", 9)
    cs_data = [
        ("Web site:", "chase.com"),
        ("Service Center:", "1-800-242-7338"),
        ("Hearing Impaired:", "1-800-242-7383"),
        ("Para Español:", "1-888-622-4273"),
        ("International Calls:", "1-713-262-1679")
    ]
    cs_col_x = [right_x, right_x + 135]  # Two columns: 180px ≈ 135pt each
    for label, value in cs_data:
        c.drawString(cs_col_x[0], y_position_right, label)
        c.drawRightString(cs_col_x[1] + 135, y_position_right, value)
        y_position_right -= 12  # 4px padding ≈ 3pt
        if y_position_right < MARGIN:
            c.showPage()
            y_position_right = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    y_position = min(y_position, y_position_right) - 30

    # Payee Info
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, y_position, ctx['account_holder'])
    y_position -= 13.5
    address_lines = wrap_text(ctx['account_holder_address'], 9, usable_width / 2)
    for line in address_lines:
        c.drawString(MARGIN, y_position, line)
        y_position -= 13.5
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica-Bold", 9)

    # Section Divider Helper
    def draw_section_divider(title):
        nonlocal y_position
        if y_position < MARGIN + 30:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
        c.setFont("Helvetica-Bold", 10.5)
        title_width = c.stringWidth(title, "Helvetica-Bold", 10.5)
        title_width = max(title_width + 12, 112.5)  # Min width 150px ≈ 112.5pt
        c.setFillColor(colors.white)
        c.setLineWidth(2)  # Set stroke width for rectangle to 2pt
        c.rect(MARGIN - 6, y_position - 12, title_width, 15, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.drawString(MARGIN, y_position - 9, title)
        c.setLineWidth(2)
        c.line((MARGIN - 6) + title_width, y_position - 2, PAGE_WIDTH - MARGIN, y_position - 2)  # Line touches box
        y_position -= 30

    # Important Account Information
    draw_section_divider("Important Account Information")
    c.setFont("Helvetica", 9)
    if ctx['account_type'] == "Chase Total Checking":
        info_text = (
            "Effective July 1, 2025, the monthly service fee for Chase Total Checking accounts will increase to $15 unless you maintain a minimum daily balance of $1,500, have $500 in qualifying direct deposits, or maintain a linked Chase savings account with a balance of $5,000 or more. "
            "Starting June 30, 2025, Chase will introduce real-time transaction alerts for Chase Total Checking accounts via the Chase Mobile app to enhance account monitoring. Enable alerts at chase.com/alerts. "
            "Effective July 15, 2025, Chase will waive overdraft fees for transactions of $5 or less and cap daily overdraft fees at two per day for Chase Total Checking accounts. "
            "For questions about your account or these changes, please visit chase.com or contact our Customer Service team at 1-800-242-7338, available 24/7."
        )
    else:
        info_text = (
            "Effective July 1, 2025, the monthly service fee for Chase Business Complete Checking accounts will increase to $20 unless you maintain a minimum daily balance of $2,000, have $2,000 in net purchases on a Chase Business Debit Card, or maintain linked Chase business accounts with a combined balance of $10,000. "
            "Starting June 30, 2025, Chase will offer enhanced cash flow tools for Chase Business Complete Checking accounts via Chase Online, including automated invoice tracking and payment scheduling. "
            "Effective July 15, 2025, Chase will reduce wire transfer fees to $25 for domestic transfers for Chase Business Complete Checking accounts, down from $30. "
            "For questions about your account or these changes, please visit chase.com or contact our Customer Service team at 1-800-242-7338, available 24/7."
        )
    wrapped_text = wrap_text(info_text, 9, usable_width)
    for line in wrapped_text:
        c.drawString(MARGIN, y_position, line)
        y_position -= 13.5
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    y_position -= 30

    # Checking Summary
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, ctx['account_type'])
    y_position -= 13.5
    draw_section_divider("Checking Summary")
    col_widths = [2.4 * inch, 1.8 * inch, 1.8 * inch]
    col_x = [MARGIN, MARGIN + col_widths[0], MARGIN + col_widths[0] + col_widths[1]]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "")
    c.drawString(col_x[1], y_position, "Instances")
    c.drawString(col_x[2], y_position, "Amount")
    y_position -= 13.5
    c.setFont("Helvetica", 9)
    summary_rows = [
        ("Beginning Balance", "–", ctx['summary']['beginning_balance']),
        ("Deposits and Additions", str(ctx['summary']['deposits_count']), ctx['summary']['deposits_total']),
        ("Electronic Withdrawals", str(ctx['summary']['withdrawals_count']), ctx['summary']['withdrawals_total']),
        ("Ending Balance", str(ctx['summary']['transactions_count']), ctx['summary']['ending_balance']),
    ]
    for label, instances, amount in summary_rows:
        c.drawString(col_x[0], y_position, label)
        c.drawString(col_x[1], y_position, instances)
        c.drawString(col_x[2], y_position, amount)
        y_position -= 13.5
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    if ctx.get('show_fee_waiver'):
        fee_text = (
            "Your monthly service fee was waived because you maintained an average checking balance of $1,500 or had qualifying direct deposits totaling $500 or more during the statement period."
            if ctx['account_type'] == "Chase Total Checking"
            else "Your monthly service fee was waived because you maintained an average checking balance of $10,000 or had $2,500 in qualifying direct deposits during the statement period."
        )
        wrapped_fee = wrap_text(fee_text, 9, usable_width)
        for line in wrapped_fee:
            c.drawString(MARGIN, y_position, line)
            y_position -= 13.5
            if y_position < MARGIN:
                c.showPage()
                y_position = PAGE_HEIGHT - MARGIN
                c.setFont("Helvetica", 9)
    y_position -= 30

    # Deposits and Additions
    draw_section_divider("Deposits and Additions")
    col_widths = [0.9 * inch, 4.2 * inch, 0.9 * inch]
    col_x = [MARGIN, MARGIN + col_widths[0], MARGIN + col_widths[0] + col_widths[1]]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "Date")
    c.drawString(col_x[1], y_position, "Description")
    c.drawRightString(col_x[2] + col_widths[2], y_position, "Amount")
    y_position -= 13.5
    c.setFont("Helvetica", 9)
    for deposit in ctx.get('deposits', []):
        c.drawString(col_x[0], y_position, deposit.get('date', ''))
        desc = deposit['description'][:50] + "…" if len(deposit['description']) > 50 else deposit['description']
        c.drawString(col_x[1], y_position, desc)
        c.drawRightString(col_x[2] + col_widths[2], y_position, deposit.get('credit', ''))
        if not deposit.get('credit'):
            print(f"Warning: Deposit missing 'credit' field: {deposit}")
        y_position -= 13.5
        c.setLineWidth(2)
        c.line(MARGIN, y_position + 10, MARGIN + sum(col_widths), y_position + 10)
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    if not ctx.get('deposits', []):
        c.drawString(col_x[0], y_position, "No deposits for this period.")
        y_position -= 13.5
        c.setLineWidth(2)
        c.line(MARGIN, y_position + 10, MARGIN + sum(col_widths), y_position + 10)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "Total Deposits and Additions")
    c.drawRightString(col_x[2] + col_widths[2], y_position, ctx['summary']['deposits_total'])
    y_position -= 30
    c.setFont("Helvetica-Bold", 10.5)

    # Withdrawals
    draw_section_divider("Withdrawals")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "Date")
    c.drawString(col_x[1], y_position, "Description")
    c.drawRightString(col_x[2] + col_widths[2], y_position, "Amount")
    y_position -= 13.5
    c.setFont("Helvetica", 9)
    for withdrawal in ctx.get('withdrawals', []):
        c.drawString(col_x[0], y_position, withdrawal.get('date', ''))
        desc = withdrawal['description'][:50] + "…" if len(withdrawal['description']) > 50 else withdrawal['description']
        c.drawString(col_x[1], y_position, desc)
        c.drawRightString(col_x[2] + col_widths[2], y_position, withdrawal.get('debit', ''))
        if not withdrawal.get('debit'):
            print(f"Warning: Withdrawal missing 'debit' field: {withdrawal}")
        y_position -= 13.5
        c.setLineWidth(2)
        c.line(MARGIN, y_position + 10, MARGIN + sum(col_widths), y_position + 10)
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    if not ctx.get('withdrawals', []):
        c.drawString(col_x[0], y_position, "No withdrawals for this period.")
        y_position -= 13.5
        c.setLineWidth(2)
        c.line(MARGIN, y_position + 10, MARGIN + sum(col_widths), y_position + 10)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "Total Electronic Withdrawals")
    c.drawRightString(col_x[2] + col_widths[2], y_position, ctx['summary']['withdrawals_total'])
    y_position -= 30
    c.setFont("Helvetica-Bold", 10.5)

    # Daily Ending Balance
    draw_section_divider("Daily Ending Balance")
    col_widths = [3 * inch, 3 * inch]
    col_x = [MARGIN, MARGIN + col_widths[0]]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_x[0], y_position, "Date")
    c.drawString(col_x[1], y_position, "Amount")
    y_position -= 13.5
    c.setFont("Helvetica", 9)
    for balance in ctx.get('daily_balances', []):
        c.drawString(col_x[0], y_position, balance.get('date', ''))
        c.drawString(col_x[1], y_position, balance.get('amount', ''))
        y_position -= 13.5
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
    y_position -= 30

    # Footnotes
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, y_position, "Disclosures")
    y_position -= 11.25
    disclosures_text = (
        "All account transactions are subject to the Chase Deposit Account Agreement, available at chase.com. "
        "Interest rates and Annual Percentage Yields (APYs) may change without notice. For overdraft policies and fees, visit chase.com/overdraft or call 1-800-242-7338. "
        "JPMorgan Chase Bank, N.A. is a Member FDIC. Equal Housing Lender."
    )
    wrapped_disclosures = wrap_text(disclosures_text, 7.5, usable_width)
    for line in wrapped_disclosures:
        c.drawString(MARGIN, y_position, line)
        y_position -= 11.25
        if y_position < MARGIN:
            c.showPage()
            y_position = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 7.5)

    c.save()
    print(f"PDF generated: {output_file}")




    
# Cell 3c: Wells Fargo Classic


def create_wellsfargo_classic(ctx):
    output_file = os.path.join(output_dir, f"wells_fargo_statement_{ctx['customer_account_number'][-4:]}.pdf")
    c = canvas.Canvas(output_file, pagesize=letter)
    
    # Page dimensions
    PAGE_WIDTH, PAGE_HEIGHT = letter  # 612 x 792 points
    MARGIN = 0.06 * PAGE_WIDTH  # 6% margin (~36 points)
    RULE_THICKNESS = 1
    USABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN
    
    # Helper function to wrap text
    def wrap_text(text, font_name, font_size, max_width):
        lines = []
        words = text.split()
        current_line = []
        current_width = 0
        c.setFont(font_name, font_size)
        for word in words:
            word_width = c.stringWidth(word + " ", font_name, font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        return lines
    
    # Helper function for horizontal rule
    def hrule(ypos, x_start, x_end):
        c.setLineWidth(RULE_THICKNESS)
        c.line(x_start, ypos, x_end, ypos)
    
    y = PAGE_HEIGHT - MARGIN
    
    # ── (1) HEADER ───────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN, y - 20, ctx['account_type'])
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN, y - 20 - 5 - 11, f"Account number: {ctx['customer_account_number']} | {ctx['statement_period']}")
    y -= 20 + 5 + 11
    address_lines = wrap_text(ctx['account_holder_address'], "Helvetica", 11, USABLE_WIDTH * 0.55)
    for line in address_lines:
        c.drawString(MARGIN, y - 11 * 1.3, line)
        y -= 11 * 1.3
    if os.path.exists(ctx['logo_path']):
        c.drawImage(ctx['logo_path'], PAGE_WIDTH - MARGIN - 48, PAGE_HEIGHT - MARGIN - 48, width=48, height=48, mask='auto')
    else:
        print(f"Warning: Logo file {ctx['logo_path']} not found.")
    y -= (30 + 15 + 4 * 11 * 1.3)  # Add space equivalent to 4 line breaks (11pt font, 1.3 line height)
    
    # ── (2) QUESTIONS SECTION ────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.drawString(PAGE_WIDTH - MARGIN - (USABLE_WIDTH * 0.4), y, "Questions?")
    c.setFont("Helvetica", 9)
    y -= 9 * 1.3
    help_text = [
        "Available by phone 24 hours a day, 7 days a week:",
        "1-800-CALL-WELLS (1-800-225-5935)",
        "",
        "TTY: 1-800-877-4833",
        "En español: 1-877-337-7454",
        "",
        "Online: wellsfargo.com",
        "",
        "Write:",
        "Wells Fargo Bank,",
        "420 Montgomery Street",
        "San Francisco, CA 94104"
    ]
    help_y_start = y
    for line in help_text:
        wrapped_line = wrap_text(line, "Helvetica", 9, USABLE_WIDTH * 0.4 - 24)
        for subline in wrapped_line:
            if y < MARGIN:
                c.showPage()
                y = PAGE_HEIGHT - MARGIN
                c.setFont("Helvetica", 9)
            c.drawString(PAGE_WIDTH - MARGIN - (USABLE_WIDTH * 0.4), y, subline)
            y -= 9 * 1.3
    c.line(PAGE_WIDTH - MARGIN - (USABLE_WIDTH * 0.4) - 24, help_y_start + 9 * 1.3, PAGE_WIDTH - MARGIN - (USABLE_WIDTH * 0.4) - 24, y + 9 * 1.3)
    y -= 15
    hrule(y + 10, MARGIN, PAGE_WIDTH - MARGIN)
    y -= 10
    
    # ── (3) INTRO BLURB ──────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "Your Wells Fargo")
    y -= 14 + 5
    c.setFont("Helvetica", 10)
    intro_text = (
        "It’s a great time to talk with a banker about how Wells Fargo’s accounts "
        "and services can help you stay competitive by saving you time and money. "
        "To find out how we can help, stop by any Wells Fargo location or call us at "
        "the number at the top of your statement."
    )
    intro_lines = wrap_text(intro_text, "Helvetica", 10, USABLE_WIDTH)
    for line in intro_lines:
        if y < MARGIN:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, line)
        y -= 10 * 1.3
    y -= 20
    
    # ── (4) IMPORTANT INFORMATION ────────────────────────────────────
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "Important Account Information")
    y -= 14 + 5
    c.setFont("Helvetica", 10)
    if ctx['account_type'] == "Everyday Checking":
        info_text = (
            "Effective July 1, 2025, the monthly service fee for Everyday Checking accounts will increase to $12 unless you maintain a minimum daily balance of $500, have $500 in qualifying direct deposits, or maintain a linked Wells Fargo savings account with a balance of $300 or more. "
            "Starting June 30, 2025, Wells Fargo will introduce real-time transaction alerts for Everyday Checking accounts via the Wells Fargo Mobile app. Enable alerts at wellsfargo.com/alerts. "
            "Effective July 15, 2025, Wells Fargo will waive overdraft fees for transactions of $5 or less and cap daily overdraft fees at two per day for Everyday Checking accounts."
        )
    else:
        info_text = (
            "Effective July 1, 2025, the monthly service fee for Business Checking accounts will increase to $14 unless you maintain a minimum daily balance of $2,500 or have $1,000 in net purchases on a Wells Fargo Business Debit Card per month. "
            "Starting June 30, 2025, Wells Fargo will offer enhanced cash flow tools for Business Checking accounts via Wells Fargo Online Banking, including automated invoice tracking and payment scheduling. "
            "Effective July 15, 2025, Wells Fargo will reduce domestic wire transfer fees to $25 for Business Checking accounts, down from $30."
        )
    info_text += " For questions, visit wellsfargo.com or contact our Customer Service at 1-800-225-5935, available 24/7."
    info_lines = wrap_text(info_text, "Helvetica", 10, USABLE_WIDTH)
    for line in info_lines:
        if y < MARGIN:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, line)
        y -= 10 * 1.3
    
    # ── (5) ACTIVITY & ROUTING SUMMARIES ─────────────────────────────
    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, y, "Activity summary")
    c.drawString(MARGIN + (USABLE_WIDTH * 0.48) + 20, y, "")
    y -= 13 + 3
    c.setFont("Helvetica", 10)
    activity_lines = [
        (f"Beginning balance on", ctx['summary']['beginning_balance']),
        (f"Deposits / Credits", ctx['summary']['deposits_total']),
        (f"Withdrawals / Debits", ctx['summary']['withdrawals_total']),
        (f"Ending balance on", ctx['summary']['ending_balance'], "Helvetica-Bold")
    ]
    activity_y_start = y
    for label, value, *font in activity_lines:
        font_name = font[0] if font else "Helvetica"
        c.setFont(font_name, 10)
        c.drawString(MARGIN + 12, y, label)
        c.drawRightString(MARGIN + (USABLE_WIDTH * 0.48) - 10, y, value)
        y -= 10 + 2
    y += (10 + 2) * len(activity_lines)
    c.setFont("Helvetica", 9)
    routing_lines = [
        f"Account number: {ctx['customer_account_number']}",
        ctx['account_holder'],
        "For Direct Deposit and Automatic Payments use Routing Number (RTN): 053000219",
        "For Wire Transfer use Routing Number (RTN): 121000248"
    ]
    for line in routing_lines:
        wrapped_line = wrap_text(line, "Helvetica", 9, USABLE_WIDTH * 0.48 - 20)
        for subline in wrapped_line:
            c.drawString(MARGIN + (USABLE_WIDTH * 0.48) + 20, y, subline)
            y -= 9 + 2
    c.line(MARGIN + (USABLE_WIDTH * 0.48), activity_y_start + 10, MARGIN + (USABLE_WIDTH * 0.48), y + 10)
    y -= 10
    hrule(y + 10, MARGIN, PAGE_WIDTH - MARGIN)
    
# ── (6) TRANSACTION HISTORY ──────────────────────────────────────
    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, y, "Transaction history")
    y -= 13 + 6
    c.setFont("Helvetica-Bold", 10)
    col_widths = [0.12 * USABLE_WIDTH, 0.36 * USABLE_WIDTH, 0.14 * USABLE_WIDTH, 0.16 * USABLE_WIDTH, 0.22 * USABLE_WIDTH]
    col_x = [MARGIN]
    for w in col_widths:
        col_x.append(col_x[-1] + w)
    col_x[2] -= 20  # Shift Deposits / Credits column left by 20 points (8 + 12)
    headers = ["Date", "Description", "Deposits / Credits", "Withdrawals / Debits", "Ending daily balance"]
    c.setFillColorRGB(0.85, 0.85, 0.85)
    c.rect(MARGIN, y, USABLE_WIDTH, 10 + 3, fill=1)
    c.setFillColorRGB(0, 0, 0)
    for i, header in enumerate(headers):
        if i in [2, 3, 4]:
            c.drawRightString(col_x[i] + col_widths[i] - 8, y + 2, header)
        else:
            c.drawString(col_x[i] + 8, y + 2, header)
    y -= 10 + 3
    c.setFont("Helvetica", 10)
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.4, 0.4, 0.4)
    c.drawString(col_x[1] + 8, y, "Opening balance")
    c.drawRightString(col_x[4] + col_widths[4] - 8, y, ctx['summary']['beginning_balance'])
    c.line(MARGIN, y - 2, PAGE_WIDTH - MARGIN, y - 2)
    y -= 10 + 3
    for transaction in ctx.get('transactions', []):
        if y < MARGIN:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 10)
        c.drawString(col_x[0] + 8, y, transaction.get('date', ''))
        desc = transaction['description'][:45] + "…" if len(transaction['description']) > 45 else transaction['description']
        c.drawString(col_x[1] + 8, y, desc)
        c.drawRightString(col_x[2] + col_widths[2] - 8, y, transaction.get('deposits_credits', ''))
        c.drawRightString(col_x[3] + col_widths[3] - 8, y, transaction.get('withdrawals_debits', ''))
        c.drawRightString(col_x[4] + col_widths[4] - 8, y, transaction.get('ending_balance', ''))
        if not transaction.get('deposits_credits') and not transaction.get('withdrawals_debits'):
            print(f"Warning: Transaction missing both 'deposits_credits' and 'withdrawals_debits' fields: {transaction}")
        c.line(MARGIN, y - 2, PAGE_WIDTH - MARGIN, y - 2)
        y -= 10 + 3
    if not ctx.get('transactions', []):
        c.drawString(MARGIN + 8, y, "No transactions for this period.")
        y -= 10 + 3
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col_x[1] + 8, y, "Total")
    c.drawRightString(col_x[2] + col_widths[2] - 8, y, ctx['summary']['deposits_total'])
    c.drawRightString(col_x[3] + col_widths[3] - 8, y, ctx['summary']['withdrawals_total'])
    c.drawRightString(col_x[4] + col_widths[4] - 8, y, ctx['summary']['ending_balance'])
    y -= 10 + 3
    
    # ── (7) DISCLOSURES ──────────────────────────────────────────────
    y -= 30
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN, y, "Disclosures")
    y -= 9 * 1.3
    disclosures_text = (
        "All account transactions are subject to the Wells Fargo Deposit Account Agreement, available at wellsfargo.com. "
        "Interest rates and Annual Percentage Yields (APYs) may change without notice. For details on overdraft policies and fees, visit wellsfargo.com/overdraft or call 1-800-225-5935."
    )
    disclosure_lines = wrap_text(disclosures_text, "Helvetica", 9, USABLE_WIDTH)
    for line in disclosure_lines:
        if y < MARGIN:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN
            c.setFont("Helvetica", 9)
        c.drawString(MARGIN, y, line)
        y -= 9 * 1.3
    y -= 9 * 1.3
    c.drawString(MARGIN, y, "© 2025 Wells Fargo Bank, N.A. All rights reserved. Member FDIC.")
    
    c.save()
    print(f"PDF generated: {output_file}")



# Cell 3d: PNC Classic

def create_pnc_classic(ctx, output_dir="out"):
    output_file = os.path.join(output_dir, f"pnc_classic_statement_{ctx['customer_account_number'][-4:]}.pdf")
    c = canvas.Canvas(output_file, pagesize=letter)
    c.setFont("Helvetica", 12)  # Match HTML font
    
    # Page dimensions
    PAGE_WIDTH, PAGE_HEIGHT = letter
    margin = 0.5 * inch
    usable_width = PAGE_WIDTH - 2 * margin
    y_position = PAGE_HEIGHT - margin - 24  # Adjust for top padding
    MIN_SPACE_FOR_TABLE = 60  # Minimum space needed for table header, labels, and one row (pt)
    
    # Helper function to wrap text
    def wrap_text(text, font_size, max_width):
        lines = []
        words = text.split()
        current_line = []
        current_width = 0
        c.setFont("Helvetica", font_size)
        for word in words:
            word_width = c.stringWidth(word + " ", "Helvetica", font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        return lines
    
    # Helper function to check for page break
    def check_page_break(space_needed):
        nonlocal y_position
        if y_position < margin + space_needed:
            c.showPage()
            y_position = PAGE_HEIGHT - margin - 24
            c.setFont("Helvetica", 12)
            print(f"Page break triggered: Needed {space_needed}pt, had {y_position - margin}pt")
            return True
        return False
    
    # Header
    c.setFont("Helvetica", 22)
    c.drawString(margin, y_position, f"{ctx['account_type']} Statement")
    y_position -= 18
    c.setFont("Helvetica", 10.5)
    c.drawString(margin, y_position, "PNC Bank")
    if os.path.exists(ctx['logo_path']):
        c.drawImage(ctx['logo_path'], PAGE_WIDTH - margin - 60, y_position + 18, width=0.83*inch, height=0.48*inch, mask='auto')
    else:
        print(f"Warning: Logo file {ctx['logo_path']} not found.")
    y_position -= 30
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Customer & Contact Row
    y_position -= 14
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, f"{ctx['statement_period']}")
    y_position -= 14
    c.drawString(margin, y_position, ctx['account_holder'])
    y_position -= 14
    c.setFont("Helvetica", 12)
    address_lines = wrap_text(ctx['account_holder_address'], 12, usable_width / 2)
    for line in address_lines:
        check_page_break(12)
        c.drawString(margin, y_position, line)
        y_position -= 12
    
    # Right Info Block (start after address lines to avoid overlap)
    right_x = PAGE_WIDTH - margin - 250
    c.setFont("Helvetica", 10.5)
    y_position_right = y_position + 8  # Start relative to final y_position after address
    c.drawString(right_x, y_position_right, f"Primary account number: {ctx['customer_account_number']}")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Page 1 of 1")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Number of enclosures: 0")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "24-hour Online & Mobile Banking at pnc.com")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Customer service: 1-888-PNC-BANK")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Mon-Fri 7 AM–10 PM ET • Sat-Sun 8 AM–5 PM ET")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Spanish: 1-866-HOLA-PNC")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "Write: PO Box 609, Pittsburgh, PA 15230-9738")
    y_position_right -= 12
    c.drawString(right_x, y_position_right, "TTY: 1-800-531-1648")
    y_position = min(y_position, y_position_right) - 14  # Align with lowest point and add padding
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Important Account Information
    check_page_break(60)
    y_position -= 14
    c.setFont("Helvetica", 11)
    c.drawString(margin, y_position, "Important Account Information")
    y_position -= 14
    c.setFont("Helvetica", 12)
    if ctx['account_type'] == "Standard Checking":
        info_text = (
            "Effective July 1, 2025, the monthly service fee will be $10 unless you maintain a minimum daily balance of $1,500 or have qualifying direct deposits of $500 or more per month. "
            "Starting June 30, 2025, PNC will introduce real-time transaction alerts for Standard Checking accounts via the PNC Mobile app. Enable alerts at pnc.com/alerts. "
            "Effective July 15, 2025, PNC will waive overdraft fees for transactions of $5 or less and cap daily overdraft fees at two per day for Standard Checking accounts. "
            "For questions, visit pnc.com or contact our Customer Service at 1-888-PNC-BANK, available 24/7."
        )
    else:
        info_text = (
            "Effective July 1, 2025, the monthly service fee for Business Checking accounts will be $15 unless you maintain a minimum daily balance of $5,000 or have $2,000 in net purchases on a PNC Business Debit Card per month. "
            "Starting June 30, 2025, PNC will offer enhanced cash flow tools for Business Checking accounts via PNC Online Banking, including automated invoice tracking and payment scheduling. "
            "Effective July 15, 2025, PNC will reduce domestic wire transfer fees to $25 for Business Checking accounts, down from $30. "
            "For questions, visit pnc.com or contact our Customer Service at 1-888-PNC-BANK, available 24/7."
        )
    wrapped_text = wrap_text(info_text, 12, usable_width)
    for line in wrapped_text:
        y_position -= 12
        check_page_break(12)
        c.drawString(margin, y_position, line)
    y_position -= 12
    c.drawString(margin, y_position, "Questions? Visit any PNC branch or call 1-888-762-2265 (24/7).")
    y_position -= 14
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Account Summary
    check_page_break(60)
    y_position -= 14
    c.setFont("Helvetica", 15)
    c.drawString(margin, y_position, f"{ctx['account_type']} Summary")
    y_position -= 14
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, f"Account number: {ctx['customer_account_number']}")
    y_position -= 12
    c.drawString(margin, y_position, f"Overdraft Protection Provided By: {ctx.get('summary', {}).get('overdraft_protection1', 'None')}")
    y_position -= 12
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_position, f"Overdraft Coverage: Your account is {ctx.get('summary', {}).get('overdraft_status', 'opted out')}.")
    y_position -= 12
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, f"{ctx['account_holder']}")
    y_position -= 12
    address_lines = wrap_text(ctx['account_holder_address'], 12, usable_width)
    for line in address_lines:
        c.drawString(margin, y_position, line)
        y_position -= 12
        check_page_break(12)
    y_position -= 14
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Balance / Transaction / Interest Summaries
    check_page_break(60)
    y_position -= 14
    c.setFont("Helvetica", 13)
    c.drawString(margin, y_position, "Balance Summary")
    y_position -= 10
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, "Beginning balance")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['beginning_balance'])
    y_position -= 12
    c.drawString(margin, y_position, "Deposits & other additions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['deposits_total'])
    y_position -= 12
    c.drawString(margin, y_position, "Checks & other deductions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['withdrawals_total'])
    y_position -= 12
    c.drawString(margin, y_position, "Ending balance")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx['summary']['ending_balance'])
    y_position -= 12
    c.drawString(margin, y_position, "Average monthly balance")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('average_balance', f"$0.00"))
    y_position -= 12
    c.drawString(margin, y_position, "Charges & fees")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('fees', f"$0.00"))
    y_position -= 20
    check_page_break(20)
    
    c.setFont("Helvetica", 13)
    c.drawString(margin, y_position, "Transaction Summary")
    y_position -= 10
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, "Checks paid/written")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('checks_written', "0"))
    y_position -= 12
    c.drawString(margin, y_position, "Check-card POS transactions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('pos_transactions', "0"))
    y_position -= 12
    c.drawString(margin, y_position, "Check-card/virtual POS PIN txn")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('pos_pin_transactions', "0"))
    y_position -= 12
    c.drawString(margin, y_position, "Total ATM transactions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('total_atm_transactions', "0"))
    y_position -= 12
    c.drawString(margin, y_position, "PNC Bank ATM transactions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('pnc_atm_transactions', "0"))
    y_position -= 12
    c.drawString(margin, y_position, "Other Bank ATM transactions")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('other_atm_transactions', "0"))
    y_position -= 20
    check_page_break(20)
    
    c.setFont("Helvetica", 13)
    c.drawString(margin, y_position, "Interest Summary")
    y_position -= 10
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, "APY earned")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('apy_earned', "0.00%"))
    y_position -= 12
    c.drawString(margin, y_position, "Days in period")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('days_in_period', "30"))
    y_position -= 12
    c.drawString(margin, y_position, "Avg collected balance")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('average_collected_balance', f"$0.00"))
    y_position -= 12
    c.drawString(margin, y_position, "Interest paid this period")
    c.drawRightString(PAGE_WIDTH - margin, y_position, ctx.get('summary', {}).get('interest_paid_period', f"$0.00"))
    y_position -= 12
    c.setFont("Helvetica", 10.5)
    c.drawString(margin, y_position, f"YTD interest paid: {ctx.get('summary', {}).get('interest_paid_ytd', f'$0.00')}")
    y_position -= 20
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Activity Detail
    check_page_break(MIN_SPACE_FOR_TABLE)
    y_position -= 14
    c.setFont("Helvetica", 15)
    c.drawString(margin, y_position, "Activity Detail")
    y_position -= 14
    
    # Calculate Amount column alignment
    c.setFont("Helvetica", 12)
    amount_header_width = c.stringWidth("Amount", "Helvetica", 12)
    amount_x = margin + 0.15 * usable_width + amount_header_width  # Right edge of "Amount" header
    
    # Deposits & Other Additions
    check_page_break(MIN_SPACE_FOR_TABLE)
    c.setFont("Helvetica", 13)
    c.drawString(margin, y_position, "Deposits & Other Additions")
    y_position -= 10
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, "Date")
    c.drawString(margin + 0.15 * usable_width, y_position, "Amount")
    c.drawString(margin + 0.35 * usable_width, y_position, "Description")
    y_position -= 12
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    for deposit in ctx.get('deposits', []):
        check_page_break(12)
        y_position -= 12
        c.drawString(margin, y_position, deposit.get("date", ""))
        c.drawRightString(amount_x, y_position, deposit.get("credit", ""))
        c.drawString(margin + 0.35 * usable_width, y_position, deposit.get("description", ""))
        if not deposit.get("credit"):
            print(f"Warning: Deposit missing 'credit' field: {deposit}")
    y_position -= 12
    c.setFont("Helvetica", 10.5)
    c.drawString(margin, y_position, f"There are {ctx['summary']['deposits_count']} deposits totaling {ctx['summary']['deposits_total']}.")
    y_position -= 20
    
    # Checks & Other Deductions
    check_page_break(MIN_SPACE_FOR_TABLE)
    c.setFont("Helvetica", 13)
    c.drawString(margin, y_position, "Checks & Other Deductions")
    y_position -= 10
    c.setFont("Helvetica", 12)
    c.drawString(margin, y_position, "Date")
    c.drawString(margin + 0.15 * usable_width, y_position, "Amount")
    c.drawString(margin + 0.35 * usable_width, y_position, "Description")
    y_position -= 12
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    for withdrawal in ctx.get('withdrawals', []):
        check_page_break(12)
        y_position -= 12
        c.drawString(margin, y_position, withdrawal.get("date", ""))
        c.drawRightString(amount_x, y_position, withdrawal.get("debit", ""))
        c.drawString(margin + 0.35 * usable_width, y_position, withdrawal.get("description", ""))
        if not withdrawal.get("debit"):
            print(f"Warning: Withdrawal missing 'debit' field: {withdrawal}")
    y_position -= 12
    c.setFont("Helvetica", 10.5)
    c.drawString(margin, y_position, f"There are {ctx['summary']['withdrawals_count']} withdrawals totaling {ctx['summary']['withdrawals_total']}.")
    y_position -= 20
    c.line(margin, y_position, PAGE_WIDTH - margin, y_position)
    
    # Disclosures
    check_page_break(60)
    y_position -= 14
    c.setFont("Helvetica", 11)
    c.drawString(margin, y_position, "Disclosures")
    y_position -= 14
    c.setFont("Helvetica", 12)
    disclosures_text = (
        "All account transactions are subject to the PNC Consumer Funds Availability Policy and Account Agreement, available at pnc.com. "
        "Interest rates and Annual Percentage Yields (APYs) may change without notice. For overdraft information, visit pnc.com/overdraft or call 1-888-762-2265."
    )
    wrapped_disclosures = wrap_text(disclosures_text, 12, usable_width)
    for line in wrapped_disclosures:
        y_position -= 12
        check_page_break(12)
        c.drawString(margin, y_position, line)
    y_position -= 12
    c.drawString(margin, y_position, "PNC Bank, National Association, Member FDIC • Equal Housing Lender.")
    
    c.save()
    print(f"PDF generated: {output_file}")






