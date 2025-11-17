"""
Export Integrations Module
Provides direct export to accounting software (QuickBooks, Xero, etc.)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import csv
import io
from pathlib import Path

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting transactions to various formats"""
    
    def __init__(self):
        pass
    
    def export_to_csv(
        self,
        transactions: List[Dict[str, Any]],
        include_explanations: bool = False
    ) -> str:
        """
        Export transactions to CSV format
        
        Args:
            transactions: List of transaction dicts
            include_explanations: Whether to include explanation columns
            
        Returns:
            CSV string
        """
        if not transactions:
            return ""
        
        output = io.StringIO()
        
        # Determine columns
        base_columns = [
            'date', 'amount', 'currency', 'category', 'subcategory',
            'merchant', 'description', 'confidence', 'method', 'requires_review'
        ]
        
        if include_explanations:
            base_columns.extend(['explanations', 'ensemble_votes'])
        
        writer = csv.DictWriter(output, fieldnames=base_columns)
        writer.writeheader()
        
        for txn in transactions:
            row = {
                'date': txn.get('date', ''),
                'amount': txn.get('amount', ''),
                'currency': txn.get('currency', 'INR'),
                'category': txn.get('category', ''),
                'subcategory': txn.get('subcategory', ''),
                'merchant': txn.get('merchant', ''),
                'description': txn.get('original_text', txn.get('text', '')),
                'confidence': txn.get('confidence', 0.0),
                'method': txn.get('method', ''),
                'requires_review': txn.get('requires_review', False)
            }
            
            if include_explanations:
                row['explanations'] = '; '.join(txn.get('explanations', []))
                votes = txn.get('ensemble_votes', {})
                row['ensemble_votes'] = f"Rule: {votes.get('rule', {}).get('category', 'N/A')}, ML: {votes.get('ml', {}).get('category', 'N/A')}"
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_quickbooks_format(
        self,
        transactions: List[Dict[str, Any]]
    ) -> str:
        """
        Export transactions in QuickBooks IIF format
        
        Args:
            transactions: List of transaction dicts
            
        Returns:
            IIF format string
        """
        lines = []
        
        # IIF Header
        lines.append("!TRNS\tDATE\tACCNT\tAMOUNT\tMEMO")
        lines.append("!SPL\tDATE\tACCNT\tAMOUNT\tMEMO")
        lines.append("!ENDTRNS")
        
        # Map categories to QuickBooks accounts
        category_to_account = {
            'Food & Dining': 'Meals & Entertainment',
            'Groceries': 'Groceries',
            'Transport': 'Auto & Travel',
            'Fuel': 'Auto & Travel',
            'Shopping': 'Merchandise',
            'Bills': 'Utilities',
            'Utilities': 'Utilities',
            'Rent': 'Rent',
            'Health': 'Medical',
            'Education': 'Education',
            'Entertainment': 'Meals & Entertainment',
            'Travel': 'Auto & Travel',
            'Fees & Charges': 'Bank Charges',
            'Other': 'Other Expenses'
        }
        
        for txn in transactions:
            date = txn.get('date', datetime.now().strftime('%Y-%m-%d'))
            amount = abs(float(txn.get('amount', 0)))
            category = txn.get('category', 'Other')
            account = category_to_account.get(category, 'Other Expenses')
            memo = txn.get('original_text', txn.get('text', ''))
            
            # Transaction line
            lines.append(f"TRNS\t{date}\t{account}\t-{amount:.2f}\t{memo}")
            # Split line (bank account)
            lines.append(f"SPL\t{date}\tBank Account\t{amount:.2f}\t{memo}")
            lines.append("ENDTRNS")
        
        return '\n'.join(lines)
    
    def export_to_xero_format(
        self,
        transactions: List[Dict[str, Any]]
    ) -> str:
        """
        Export transactions in Xero CSV format
        
        Args:
            transactions: List of transaction dicts
            
        Returns:
            Xero CSV format string
        """
        output = io.StringIO()
        
        # Xero CSV format
        writer = csv.DictWriter(
            output,
            fieldnames=[
                '*ContactName', '*InvoiceNumber', '*InvoiceDate', '*DueDate',
                'InventoryItemCode', 'Description', 'Quantity', 'UnitAmount',
                'AccountCode', '*TaxType', 'TaxAmount', 'LineAmount'
            ]
        )
        
        writer.writeheader()
        
        # Map categories to Xero account codes
        category_to_account = {
            'Food & Dining': '200',
            'Groceries': '201',
            'Transport': '202',
            'Fuel': '202',
            'Shopping': '203',
            'Bills': '204',
            'Utilities': '204',
            'Rent': '205',
            'Health': '206',
            'Education': '207',
            'Entertainment': '208',
            'Travel': '202',
            'Fees & Charges': '209',
            'Other': '299'
        }
        
        for txn in transactions:
            date = txn.get('date', datetime.now().strftime('%d/%m/%Y'))
            amount = abs(float(txn.get('amount', 0)))
            category = txn.get('category', 'Other')
            account_code = category_to_account.get(category, '299')
            description = txn.get('original_text', txn.get('text', ''))
            
            writer.writerow({
                '*ContactName': txn.get('merchant', ''),
                '*InvoiceNumber': f"TXN-{txn.get('id', '')}",
                '*InvoiceDate': date,
                '*DueDate': date,
                'Description': description,
                'Quantity': '1',
                'UnitAmount': f"{amount:.2f}",
                'AccountCode': account_code,
                '*TaxType': 'GST',
                'TaxAmount': f"{amount * 0.18:.2f}",  # 18% GST
                'LineAmount': f"{amount:.2f}"
            })
        
        return output.getvalue()
    
    def export_to_json(
        self,
        transactions: List[Dict[str, Any]],
        format: str = "standard"
    ) -> str:
        """
        Export transactions to JSON format
        
        Args:
            transactions: List of transaction dicts
            format: Export format ('standard', 'quickbooks', 'xero')
            
        Returns:
            JSON string
        """
        import json
        
        if format == "quickbooks":
            # QuickBooks JSON format
            qb_transactions = []
            for txn in transactions:
                qb_transactions.append({
                    "TxnDate": txn.get('date', datetime.now().strftime('%Y-%m-%d')),
                    "Amount": abs(float(txn.get('amount', 0))),
                    "AccountRef": {"name": txn.get('category', 'Other')},
                    "Line": [{
                        "Amount": abs(float(txn.get('amount', 0))),
                        "DetailType": "AccountBasedExpenseLineDetail",
                        "AccountBasedExpenseLineDetail": {
                            "AccountRef": {"name": txn.get('category', 'Other')}
                        }
                    }]
                })
            return json.dumps({"Transaction": qb_transactions}, indent=2)
        
        elif format == "xero":
            # Xero JSON format
            xero_transactions = []
            for txn in transactions:
                xero_transactions.append({
                    "Type": "ACCREC",
                    "Contact": {"Name": txn.get('merchant', '')},
                    "Date": txn.get('date', datetime.now().strftime('%Y-%m-%d')),
                    "LineItems": [{
                        "Description": txn.get('original_text', txn.get('text', '')),
                        "Quantity": 1,
                        "UnitAmount": abs(float(txn.get('amount', 0))),
                        "AccountCode": "200"
                    }]
                })
            return json.dumps({"Invoices": xero_transactions}, indent=2)
        
        else:
            # Standard JSON format
            return json.dumps(transactions, indent=2, default=str)


# Global instance
export_service = ExportService()
