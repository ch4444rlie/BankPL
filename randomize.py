from faker import Faker
import random
from datetime import datetime, timedelta
import streamlit as st

def generate_statement_data(bank_name, account_type="personal"):
    """
    Generate synthetic bank statement data for a given bank.
    
    Args:
        bank_name (str): Name of the bank (e.g., 'Chase', 'Citibank').
        account_type (str): Type of account ('personal' or 'business').
    
    Returns:
        dict: Context dictionary with bank statement data, including sections.
    
    Raises:
        ValueError: If the bank_name is not supported.
    """
    try:
        fake = Faker()
        Faker.seed(random.randint(0, 1000000))

        # Bank-specific configurations
        bank_configs = {
            "Chase": {
                "full_name": "JPMorgan Chase Bank, N.A.",
                "address": "PO Box 659754, San Antonio, TX 78265-9754",
                "logo_path": "sample_logos/chase_bank_logo.png",
                "contact": "1-800-242-7338",
                "website": "chase.com",
                "currency": "$"
            },
            "Wells Fargo": {
                "full_name": "Wells Fargo Bank, N.A.",
                "address": "420 Montgomery Street, San Francisco, CA 94104",
                "logo_path": "sample_logos/wellsfargo_logo.png",
                "contact": "1-800-225-5935",
                "website": "wellsfargo.com",
                "currency": "$"
            },
            "PNC": {
                "full_name": "PNC Bank, National Association",
                "address": "249 Fifth Avenue, Pittsburgh, PA 15222",
                "logo_path": "sample_logos/pnc_logo.png",
                "contact": "1-888-PNC-BANK",
                "website": "pnc.com",
                "currency": "$"
            },
            "Citibank": {
                "full_name": "Citibank, N.A.",
                "address": "388 Greenwich Street, New York, NY 10013",
                "logo_path": "sample_logos/citibank_logo.png",
                "contact": "1-800-374-9700",
                "website": "citibank.com",
                "currency": "£"
            }
        }

        # Validate bank_name
        if bank_name not in bank_configs:
            raise ValueError(f"Unsupported bank: {bank_name}")

        config = bank_configs[bank_name]
        
        # Generate synthetic account data
        account_holder = fake.company().upper() if account_type == "business" else fake.name().upper()
        account_holder_address = fake.address().replace('\n', ', ')
        account_number = fake.bban()
        account_type_name = random.choice(["Chase Total Checking", "Chase Business Complete Checking"]) if bank_name == "Chase" else \
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

        deposit_descriptions = [
            "Direct Deposit", "ATM Deposit", "Mobile Deposit", "Payroll Credit",
            "Refund", "Transfer from Savings", "Cash Deposit"
        ] if account_type == "personal" else [
            "Client Payment", "Invoice Payment", "ACH Credit", "Wire Transfer",
            "Refund", "Business Deposit", "Cash Deposit"
        ]
        withdrawal_descriptions = [
            "ATM Withdrawal", "Debit Card Purchase", "Online Bill Pay",
            "Check Payment", "Transfer to Savings", "Merchant Payment"
        ] if account_type == "personal" else [
            "Vendor Payment", "ACH Debit", "Wire Transfer", "Check Payment",
            "Payroll Expense", "Merchant Payment", "Business Withdrawal"
        ]

        for _ in range(random.randint(10, 25)):
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
        daily_balances = []
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

        # Define bank-specific sections
        sections = [
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
                        ["Beginning Balance", f"{config['currency']}{beginning_balance:.2f}"],
                        ["Deposits and Credits", f"{config['currency']}{deposits_total:.2f}"],
                        ["Withdrawals and Debits", f"{config['currency']}{withdrawals_total:.2f}"],
                        ["Ending Balance", f"{config['currency']}{balance:.2f}"]
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

        # Add bank-specific sections
        if bank_name.lower() == 'wells fargo':
            sections.insert(0, {
                "title": "Your Wells Fargo",
                "content": [{
                    "type": "text",
                    "value": (
                        "It’s a great time to talk with a banker about how Wells Fargo’s accounts "
                        "and services can help you stay competitive by saving you time and money. "
                        "To find out how we can help, stop by any Wells Fargo location or call us at "
                        "{contact}."
                    ),
                    "font": "Helvetica",
                    "size": 10,
                    "wrap": True
                }]
            })
        if bank_name.lower() == 'pnc':
            sections.insert(2, {
                "title": "Transaction and Interest Summary",
                "content": [{
                    "type": "table",
                    "data_key": "transaction_and_interest_summary",
                    "data": [
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
                    ],
                    "col_widths": [0.375, 0.125, 0.375, 0.125],
                    "font": "Helvetica",
                    "size": 10,
                    "style": "none"
                }]
            })
        if bank_name.lower() == 'chase':
            sections.append({
                "title": "Daily Ending Balance",
                "content": [{
                    "type": "table",
                    "data_key": "daily_balances",
                    "headers": ["Date", "Amount"],
                    "col_widths": [0.5, 0.5],
                    "font": "Helvetica",
                    "size": 10,
                    "style": "none"
                }]
            })

        # Context dictionary
        ctx = {
            "bank_name": bank_name,
            "customer_bank_name": config["full_name"],
            "account_holder": account_holder,
            "account_holder_address": account_holder_address,
            "customer_account_number": account_number,
            "account_type": account_type_name,
            "statement_period": statement_period,
            "statement_date": statement_date,
            "logo_path": config["logo_path"],
            "currency": config["currency"],
            "website": config["website"],
            "contact": config["contact"],
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
            "total_pages": 1,
            "layout_style": "two-column" if bank_name.lower() == "pnc" and random.random() > 0.3 else "sequential",
            "sections": sections
        }

        return ctx

    except Exception as e:
        print(f"Error in generate_statement_data for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error in generate_statement_data for {bank_name}: {str(e)}"]
        raise