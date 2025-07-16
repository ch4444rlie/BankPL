from faker import Faker
import random
from datetime import datetime, timedelta
import streamlit as st

def generate_statement_data(bank_name, account_type="personal", num_transactions=25):
    """
    Generate synthetic bank statement data for a given bank.
    
    Args:
        bank_name (str): Name of the bank (e.g., 'Chase', 'Citibank').
        account_type (str): Type of account ('personal' or 'business').
        num_transactions (int): Number of transactions to generate.
    
    Returns:
        dict: Context dictionary with bank statement data, including sections.
    
    Raises:
        ValueError: If the bank_name is not supported.
    """
    try:
        fake = Faker()
        Faker.seed(random.randint(0, 1000000))

        # Bank-specific configurations with preprocessed address lines
        bank_configs = {
            "Chase": {
                "full_name": "JPMorgan Chase Bank, N.A.",
                "address": "PO Box 659754, San Antonio, TX 78265-9754",
                "address_lines": [
                    "JPMorgan Chase Bank, N.A. Mail Code TX78265",
                    "PO Box 659754",
                    "San Antonio, TX 78265-9754"
                ],
                "logo_path": "sample_logos/chase_bank_logo.png",
                "contact": "1-800-242-7338",
                "website": "chase.com",
                "currency": "$"
            },
            "Wells Fargo": {
                "full_name": "Wells Fargo Bank, N.A.",
                "address": "420 Montgomery Street, San Francisco, CA 94104",
                "address_lines": [
                    "Wells Fargo Bank, N.A. Mail Code CA94104",
                    "420 Montgomery Street",
                    "San Francisco, CA 94104"
                ],
                "logo_path": "sample_logos/wellsfargo_logo.png",
                "contact": "1-800-225-5935",
                "website": "wellsfargo.com",
                "currency": "$"
            },
            "PNC": {
                "full_name": "PNC Bank, National Association",
                "address": "249 Fifth Avenue, Pittsburgh, PA 15222",
                "address_lines": [
                    "PNC Bank, National Association Mail Code PA15222",
                    "249 Fifth Avenue",
                    "Pittsburgh, PA 15222"
                ],
                "logo_path": "sample_logos/pnc_logo.png",
                "contact": "1-888-PNC-BANK",
                "website": "pnc.com",
                "currency": "$"
            },
            "Citibank": {
                "full_name": "Citibank, N.A.",
                "address": "Citigroup Centre, Canada Square, Canary Wharf, London, E14 5LB",
                "address_lines": [
                    "Citibank, N.A. Mail Code E145LB",
                    "Citigroup Centre, Canada Square",
                    "Canary Wharf, London, E14 5LB"
                ],
                "logo_path": "sample_logos/citibank_logo.png",
                "contact": "0800 005 555",
                "website": "citibank.co.uk",
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

        # Generate transactions
        transactions = []
        balance = round(random.uniform(1000, 10000), 2)
        beginning_balance = balance
        deposits_count = 0
        withdrawals_count = 0
        deposits_total = 0.0
        withdrawals_total = 0.0

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

        for _ in range(num_transactions):
            trans_date = fake.date_between(start_date=start_date, end_date=end_date)
            trans_type = random.choice(["credit", "debit"])
            amount = round(random.uniform(10, 1000), 2)
            
            if trans_type == "credit":
                description = random.choice(deposit_descriptions)
                credit = f"{config['currency']}{amount:.2f}"
                debit = ""
                deposits_count += 1
                deposits_total += amount
            else:
                description = random.choice(withdrawal_descriptions)
                credit = ""
                debit = f"{config['currency']}{amount:.2f}"
                withdrawals_count += 1
                withdrawals_total += amount
            
            transaction = {
                "date": trans_date.strftime('%m/%d'),
                "description": description,
                "credit": credit,
                "debit": debit,
                "deposits_credits": credit,
                "withdrawals_debits": debit
            }
            transactions.append(transaction)

        # Sort transactions by date
        transactions.sort(key=lambda x: datetime.strptime(x['date'], '%m/%d'))

        # Recalculate balance in chronological order
        running_balance = beginning_balance
        for transaction in transactions:
            if transaction["credit"]:
                amount = float(transaction["credit"].replace(config["currency"], ""))
                running_balance += amount
            if transaction["debit"]:
                amount = float(transaction["debit"].replace(config["currency"], ""))
                running_balance -= amount
            transaction["balance"] = f"{config['currency']}{running_balance:.2f}"
            transaction["ending_balance"] = f"{config['currency']}{running_balance:.2f}"

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

        # Define summary
        summary = {
            "beginning_balance": f"{config['currency']}{beginning_balance:.2f}",
            "deposits_count": str(deposits_count),
            "deposits_total": f"{config['currency']}{deposits_total:.2f}",
            "withdrawals_count": str(withdrawals_count),
            "withdrawals_total": f"{config['currency']}{withdrawals_total:.2f}",
            "ending_balance": f"{config['currency']}{running_balance:.2f}",
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
        }

        # Define bank-specific sections
        sections = [
            {
                "title": "Bank Address",
                "content": [
                    {
                        "type": "text",
                        "value": config['address_lines'][0],
                        "font": "Helvetica",
                        "size": 10,
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "value": config['address_lines'][1],
                        "font": "Helvetica",
                        "size": 10,
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "value": config['address_lines'][2],
                        "font": "Helvetica",
                        "size": 10,
                        "wrap": True
                    }
                ]
            },
            {
                "title": "Important Account Information",
                "content": [{
                    "type": "text",
                    "value": (
                        "Effective 1 July 2025, the monthly service fee for {account_type} accounts will increase to £12 unless you maintain a minimum daily balance of £1,200, have £400 in qualifying direct debits, or maintain a linked savings account with a balance of £4,000 or more. "
                        "For questions, visit {website} or call {contact}."
                    ) if bank_name == "Citibank" else (
                        "Effective July 1, 2025, the monthly service fee for {account_type} accounts will increase to $15 unless you maintain a minimum daily balance of $1,500, have $500 in qualifying direct deposits, or maintain a linked savings account with a balance of $5,000 or more. "
                        "For questions, visit {website} or call {contact}."
                    ),
                    "font": "Helvetica",
                    "size": 10,
                    "wrap": True
                }]
            },
            {
                "title": "Transaction History",
                "content": [{
                    "type": "table",
                    "data_key": "transactions",
                    "headers": ["Date", "Description", "Amount", "Balance"],
                    "col_widths": [0.125, 0.375, 0.25, 0.25],
                    "font": "Helvetica",
                    "size": 10,
                    "style": "none"
                }]
            },
            {
                "title": "Customer Service",
                "content": [{
                    "type": "table",
                    "data": [
                        ["Website:", bank_name.lower() + ".co.uk" if bank_name == "Citibank" else bank_name.lower() + ".com"],
                        ["Phone:", config["contact"] if bank_name != "Citibank" else f"0800 005 555"],
                        ["Español:", f"1-800-{random.randint(100, 999)}-{random.randint(1000, 9999)}"],
                        ["International:", f"1-800-{random.randint(100, 999)}-{random.randint(1000, 9999)}"]
                    ],
                    "headers": [],  # No headers
                    "col_widths": [0.375, 0.125],
                    "font": "Helvetica",
                    "size": 10,
                    "style": "none"
                }]
            }
        ]

        # Add bank-specific sections
        if bank_name.lower() == 'wells fargo':
            sections.append({
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
            sections.append({
                "title": "Transaction and Interest Summary",
                "content": [{
                    "type": "table",
                    "data_key": "transaction_and_interest_summary",
                    "headers": [],
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
                    "headers": [],  # No headers
                    "col_widths": [0.375, 0.125],
                    "font": "Helvetica",
                    "size": 10,
                    "style": "none"
                }]
            })

        # Randomize section order, ensuring Chase's Daily Ending Balance is second-to-last
        # Ensure Customer Service is in the first two sections
        customer_service_section = [s for s in sections if s["title"] == "Customer Service"]
        other_sections = [s for s in sections if s["title"] != "Customer Service"]
        if customer_service_section:
            # Randomly place Customer Service as first or second
            first_two = [customer_service_section[0]] if random.randint(0, 1) == 0 else []
            remaining_sections = other_sections
            if first_two:
                sections = first_two + remaining_sections
            else:
                # Place Customer Service second by shuffling remaining and inserting
                random.shuffle(remaining_sections)
                sections = remaining_sections[:1] + customer_service_section + remaining_sections[1:]
        
        # For Chase, ensure Daily Ending Balance is second-to-last
        if bank_name.lower() == 'chase':
            daily_balance = [s for s in sections if s["title"] == "Daily Ending Balance"]
            other_sections = [s for s in sections if s["title"] != "Daily Ending Balance"]
            random.shuffle(other_sections)
            sections = other_sections + daily_balance

        # Context dictionary
        ctx = {
            "bank_name": bank_name,
            "customer_bank_name": config["full_name"],
            "account_holder": account_holder,
            "account_holder_address": account_holder_address,
            "bank_address_lines": config["address_lines"],
            "customer_account_number": account_number,
            "account_type": account_type_name,
            "statement_period": statement_period,
            "statement_date": statement_date,
            "logo_path": config["logo_path"],
            "currency": config["currency"],
            "website": config["website"],
            "contact": config["contact"],
            "summary": summary,
            "transactions": transactions,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "daily_balances": daily_balances,
            "show_fee_waiver": random.choice([True, False]),
            "customer_iban": fake.iban() if bank_name == "Citibank" else "",
            "client_number": fake.uuid4() if bank_name == "Citibank" else "",
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%m/%d/%Y') if bank_name == "Citibank" else "",
            "total_pages": 1,
            "layout_style": "sequential" if random.randint(0, 1) == 0 else "two-column",
            "logo_position": random.choice(["left", "right", "center"]),
            "sections": sections
        }

        # Add Account Summary section
        sections.append({
            "title": "Account Summary",
            "content": [{
                "type": "table",
                "data_key": "account_summary",
                "headers": [],
                "col_widths": [0.375, 0.125],
                "font": "Helvetica",
                "size": 10,
                "style": "none"
            }]
        })

        # Re-randomize section order to include Account Summary, ensuring Chase's Daily Ending Balance is second-to-last
        if bank_name.lower() == 'chase':
            daily_balance = [s for s in sections if s["title"] == "Daily Ending Balance"]
            other_sections = [s for s in sections if s["title"] != "Daily Ending Balance"]
            random.shuffle(other_sections)
            sections = other_sections + daily_balance
        else:
            random.shuffle(sections)

        # Update ctx with the new sections
        ctx["sections"] = sections

        return ctx

    except Exception as e:
        print(f"Error in generate_statement_data for {bank_name}: {str(e)}")
        st.session_state['logs'] = st.session_state.get('logs', []) + [f"[{datetime.now()}] Error in generate_statement_data for {bank_name}: {str(e)}"]
        raise