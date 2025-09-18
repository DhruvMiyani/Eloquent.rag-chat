#!/usr/bin/env python3
"""
Download and process multiple fintech datasets for RAG application.
This script downloads datasets from Hugging Face, Kaggle, and other sources
and converts them into a unified format for the chatbot knowledge base.
"""

import os
import json
import pandas as pd
from pathlib import Path
import requests
from typing import List, Dict, Any
import time

# Add parent directory to path to import from api
import sys
sys.path.append(str(Path(__file__).parent.parent))

from datasets import load_dataset
import warnings
warnings.filterwarnings("ignore")

def download_bitext_retail_banking():
    """Download Bitext Retail Banking Dataset from Hugging Face."""
    print("Downloading Bitext Retail Banking Dataset...")
    try:
        # Load the dataset
        dataset = load_dataset("bitext/Bitext-retail-banking-llm-chatbot-training-dataset")

        # Convert to pandas for easier processing
        df = dataset['train'].to_pandas()

        print(f"Downloaded {len(df)} records from Bitext Retail Banking Dataset")
        print(f"Columns: {df.columns.tolist()}")

        # Display sample data
        print("\nSample data:")
        print(df.head(3).to_string())

        return df

    except Exception as e:
        print(f"Error downloading Bitext dataset: {e}")
        return None

def download_fintech_t5_data():
    """Download example data from Fintech Chatbot T5 model."""
    print("Downloading Fintech Chatbot T5 example data...")
    try:
        # This model might have example data in its model card or repository
        # For now, we'll create sample data based on the description

        sample_data = [
            {
                "instruction": "How do I activate my card for international usage?",
                "response": "To activate your card for international usage: 1) Log into your mobile app or online banking, 2) Go to Card Settings, 3) Select 'International Usage', 4) Toggle the setting to 'Enabled', 5) Set your travel dates and destinations. You can also call customer service at the number on your card."
            },
            {
                "instruction": "What are my current account balance and recent transactions?",
                "response": "I can help you check your account balance and recent transactions. Please log into your mobile app or online banking to view: 1) Current available balance, 2) Pending transactions, 3) Recent transaction history for the past 30 days, 4) Monthly statements. For security reasons, I cannot display specific amounts here."
            },
            {
                "instruction": "How do I transfer money to another account?",
                "response": "To transfer money: 1) Open your banking app, 2) Select 'Transfer Money', 3) Choose source account, 4) Enter recipient details (account number, routing number), 5) Enter amount, 6) Review and confirm. For external transfers, processing takes 1-3 business days. Internal transfers are usually instant."
            }
        ]

        df = pd.DataFrame(sample_data)
        print(f"Created {len(df)} sample T5 records")
        return df

    except Exception as e:
        print(f"Error creating T5 sample data: {e}")
        return None

def download_customer_support_data():
    """Create sample customer support ticket data."""
    print("Creating sample customer support data...")

    sample_tickets = [
        {
            "instruction": "I can't log into my account, what should I do?",
            "response": "If you can't log into your account: 1) Check your username and password, 2) Ensure caps lock is off, 3) Clear browser cache/cookies, 4) Try password reset if needed, 5) Check for account lockout notifications, 6) Contact support if issues persist. We're here to help 24/7."
        },
        {
            "instruction": "My transaction was declined, why did this happen?",
            "response": "Transaction declines can occur due to: 1) Insufficient funds, 2) Daily spending limits reached, 3) Suspicious activity detected, 4) Merchant payment issues, 5) Card expiration, 6) International transaction blocks. Check your app for specific decline reasons or contact support."
        },
        {
            "instruction": "How do I dispute a charge on my account?",
            "response": "To dispute a charge: 1) Log into your account, 2) Find the transaction, 3) Click 'Dispute Transaction', 4) Select dispute reason, 5) Provide supporting documentation, 6) Submit dispute form. We'll investigate within 10 business days and provide provisional credit if applicable."
        },
        {
            "instruction": "What should I do if my card is lost or stolen?",
            "response": "If your card is lost/stolen: 1) Immediately freeze your card in the mobile app, 2) Report it lost/stolen, 3) Request a replacement card, 4) Review recent transactions for unauthorized charges, 5) Update any automatic payments, 6) Monitor your account closely."
        }
    ]

    df = pd.DataFrame(sample_tickets)
    print(f"Created {len(df)} customer support records")
    return df

def process_banking_chatbot_data():
    """Create enhanced banking chatbot data based on research."""
    print("Creating enhanced banking chatbot data...")

    banking_data = [
        # Account Management
        {
            "instruction": "How do I open a new savings account?",
            "response": "To open a savings account: 1) Visit our website or app, 2) Click 'Open Account', 3) Choose 'Savings Account', 4) Provide personal information (SSN, address, employment), 5) Make initial deposit ($25 minimum), 6) Review terms and sign, 7) Receive account details via email."
        },
        {
            "instruction": "What are the fees for checking accounts?",
            "response": "Our checking account fees: Monthly maintenance fee $12 (waived with $1,500 minimum balance or direct deposit), Overdraft fee $35 per transaction, ATM fees $3 for out-of-network ATMs, Wire transfer fees $25 domestic/$45 international. Premium accounts have reduced fees."
        },
        {
            "instruction": "How do I set up direct deposit?",
            "response": "To set up direct deposit: 1) Get your account and routing numbers from the app, 2) Provide this info to your employer's HR/payroll department, 3) Complete their direct deposit form, 4) Allow 1-2 pay periods for setup, 5) Monitor your account for the first deposit."
        },

        # Security & Fraud Prevention
        {
            "instruction": "How do I enable two-factor authentication?",
            "response": "To enable 2FA: 1) Log into your account, 2) Go to Security Settings, 3) Select 'Two-Factor Authentication', 4) Choose SMS or authenticator app, 5) Verify your phone/setup app, 6) Save backup codes safely, 7) Test login with 2FA enabled."
        },
        {
            "instruction": "What should I do if I suspect fraud on my account?",
            "response": "If you suspect fraud: 1) Immediately freeze affected cards, 2) Report suspected transactions, 3) Change passwords and PINs, 4) Monitor all accounts closely, 5) File a fraud report, 6) Contact credit bureaus to place fraud alert, 7) Keep detailed records of all communications."
        },

        # Payments & Transactions
        {
            "instruction": "What are the limits for wire transfers?",
            "response": "Wire transfer limits: Daily limit $100,000 for verified accounts, Single transaction maximum $50,000, International wires require additional verification, Business accounts have higher limits available, Limits can be temporarily increased with prior approval."
        },
        {
            "instruction": "How long do ACH transfers take?",
            "response": "ACH transfer timing: Standard ACH takes 3-5 business days (free), Same-day ACH available until 5 PM ET (fee applies), International ACH takes 5-7 business days, Transfers initiated on weekends process Monday, Holiday processing may be delayed."
        }
    ]

    df = pd.DataFrame(banking_data)
    print(f"Created {len(df)} enhanced banking records")
    return df

def convert_to_unified_format(datasets: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Convert all datasets to unified FAQ format."""
    print("Converting datasets to unified format...")

    unified_data = []

    for dataset_name, df in datasets.items():
        print(f"Processing {dataset_name} with {len(df)} records...")

        for idx, row in df.iterrows():
            # Determine question and answer columns
            if 'instruction' in df.columns and 'response' in df.columns:
                question = str(row['instruction'])
                answer = str(row['response'])
            elif 'question' in df.columns and 'answer' in df.columns:
                question = str(row['question'])
                answer = str(row['answer'])
            elif 'query' in df.columns and 'response' in df.columns:
                question = str(row['query'])
                answer = str(row['response'])
            else:
                print(f"Unknown column format in {dataset_name}: {df.columns.tolist()}")
                continue

            # Skip empty or very short entries
            if len(question.strip()) < 10 or len(answer.strip()) < 20:
                continue

            # Categorize based on content
            category = categorize_question(question, answer, dataset_name)

            unified_entry = {
                "id": f"{dataset_name}_{idx:04d}",
                "category": category,
                "question": question.strip(),
                "answer": answer.strip(),
                "source": dataset_name
            }

            unified_data.append(unified_entry)

    print(f"Created {len(unified_data)} unified FAQ entries")
    return unified_data

def categorize_question(question: str, answer: str, source: str) -> str:
    """Categorize questions based on content."""
    text = (question + " " + answer).lower()

    if any(keyword in text for keyword in ['account', 'balance', 'open', 'close', 'verification', 'verify', 'register', 'sign up']):
        return "Account & Registration"
    elif any(keyword in text for keyword in ['payment', 'transfer', 'wire', 'ach', 'transaction', 'send money', 'deposit']):
        return "Payments & Transactions"
    elif any(keyword in text for keyword in ['security', 'fraud', 'password', '2fa', 'authentication', 'stolen', 'unauthorized']):
        return "Security & Fraud Prevention"
    elif any(keyword in text for keyword in ['compliance', 'regulation', 'legal', 'kyc', 'aml', 'tax', 'ssn']):
        return "Regulations & Compliance"
    elif any(keyword in text for keyword in ['support', 'help', 'issue', 'problem', 'error', 'troubleshoot', 'login']):
        return "Technical Support & Troubleshooting"
    else:
        return "General Banking"

def save_enhanced_dataset(unified_data: List[Dict[str, Any]], output_file: str):
    """Save enhanced dataset to JSON file."""
    # Group by category
    categorized_data = {}
    for entry in unified_data:
        category = entry['category']
        if category not in categorized_data:
            categorized_data[category] = []
        categorized_data[category].append(entry)

    # Create final structure
    final_data = {
        "description": "Enhanced Fintech FAQ Dataset - Multiple Sources Combined",
        "version": "1.0",
        "total_entries": len(unified_data),
        "categories": list(categorized_data.keys()),
        "sources": list(set(entry['source'] for entry in unified_data)),
        "faqs": []
    }

    # Add categorized FAQs
    for category, entries in categorized_data.items():
        category_data = {
            "category": category,
            "count": len(entries),
            "questions": entries
        }
        final_data["faqs"].append(category_data)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"Enhanced dataset saved to {output_file}")
    print(f"Total entries: {len(unified_data)}")
    print(f"Categories: {len(categorized_data)}")
    for category, entries in categorized_data.items():
        print(f"  - {category}: {len(entries)} entries")

def main():
    """Main function to download and process all datasets."""
    print("=== Fintech Dataset Download and Processing ===")

    datasets = {}

    # Download datasets
    print("\n1. Downloading Bitext Retail Banking Dataset...")
    try:
        bitext_data = download_bitext_retail_banking()
        if bitext_data is not None:
            datasets['bitext_banking'] = bitext_data
    except Exception as e:
        print(f"Failed to download Bitext dataset: {e}")

    print("\n2. Creating Fintech T5 sample data...")
    t5_data = download_fintech_t5_data()
    if t5_data is not None:
        datasets['fintech_t5'] = t5_data

    print("\n3. Creating customer support data...")
    support_data = download_customer_support_data()
    if support_data is not None:
        datasets['customer_support'] = support_data

    print("\n4. Creating enhanced banking data...")
    banking_data = process_banking_chatbot_data()
    if banking_data is not None:
        datasets['enhanced_banking'] = banking_data

    if not datasets:
        print("No datasets were successfully loaded!")
        return

    # Convert to unified format
    print("\n5. Converting to unified format...")
    unified_data = convert_to_unified_format(datasets)

    # Save enhanced dataset
    output_file = Path(__file__).parent / "enhanced_fintech_faq_data.json"
    print(f"\n6. Saving enhanced dataset to {output_file}...")
    save_enhanced_dataset(unified_data, str(output_file))

    print("\n=== Dataset Processing Complete ===")
    print(f"Enhanced dataset available at: {output_file}")

if __name__ == "__main__":
    main()

