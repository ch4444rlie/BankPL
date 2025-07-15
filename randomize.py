from faker import Faker
import os
import random
from datetime import datetime, timedelta


def generate_statement_data(bank_name, base_dir="."):
    """
    Generate synthetic bank statement data for a given bank.
    
    Args:
        bank_name (str): Name of the bank (e.g., 'Chase', 'Citibank').
        base_dir (str): Base directory for logo and output paths.
    
    Returns:
        dict: Context dictionary with bank statement data.
    
    Raises:
        ValueError: If the bank_name is not supported.
        OSError: If logo directory cannot be accessed.
    """
    try:
        fake = Faker()
        Faker.seed(random.randint(0, 1000000))
        output_dir = os.path.join(base_dir, "synthetic_statements")
        logo_dir = os.path.join(base_dir, "sample_logos")

        # Ensure logo directory exists
        if not os.path.exists(logo_dir):
            print(f"Warning: Logo directory {logo_dir} not found. Logo paths will be set to None.")
            logo_dir = None

        # Bank-specific configurations
        bank_configs = {
            "Chase": {
                "full_name": "JPMorgan Chase Bank, N.A.",
                "address": "PO Box 659754, San Antonio, TX 78265-9754",
                "logo": os.path.join(logo_dir, "chase_bank_logo.png") if logo_dir else None,
                "contact": "1-800-242-7338",
                "website": "chase.com",
                "currency": "$"
            },
            "Wells Fargo": {
                "full_name": "Wells Fargo Bank, N.A.",
                "address": "420 Montgomery Street, San Francisco, CA 94104",
                "logo": os.path.join(logo_dir, "wellsfargo_logo.png") if logo_dir else None,
                "contact": "1-800-225-5935",
                "website": "wellsfargo.com",
                "currency": "$"
            },
            "PNC": {
                "full_name": "PNC Bank, National Association",
                "address": "249 Fifth Avenue, Pittsburgh, PA 15222",
                "logo": os.path.join(logo_dir, "pnc_logo.png") if logo_dir else None,
                "contact": "1-888-PNC-BANK",
                "website": "pnc.com",
                "currency": "$"
            },
            "Citibank": {
                "full_name": "Citibank, N.A.",
                "address": "388 Greenwich Street, New York, NY 10013",
                "logo": os.path.join(logo_dir, "citibank_logo.png") if logo_dir else None,
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
        if config["logo"] and not os.path.exists(config["logo"]):
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
            "total_pages": 1
        }

        return ctx

    except OSError as e:
        print(f"Error accessing directories or files: {str(e)}")
        raise
    except Exception as e:
        print(f"Error in generate_statement_data for {bank_name}: {str(e)}")
        raise