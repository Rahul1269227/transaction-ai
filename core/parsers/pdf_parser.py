"""
PDF Bank Statement Parser

Extracts transaction data from PDF bank statements using multiple strategies:
1. Table extraction (pdfplumber) - for structured statements
2. Text pattern matching - for semi-structured statements
3. Line-by-line parsing - for simple statements

Supports common formats from major banks.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

logger = logging.getLogger(__name__)


class PDFBankStatementParser:
    """Extract transactions from PDF bank statements"""

    def __init__(self):
        if not (HAS_PDFPLUMBER or HAS_PYMUPDF):
            raise ImportError("Neither pdfplumber nor PyMuPDF is installed. Install with: pip install pdfplumber PyMuPDF")

    def parse_pdf(self, pdf_path: str, extract_amounts: bool = False) -> List[Dict[str, any]]:
        """
        Parse PDF bank statement and extract transactions

        Args:
            pdf_path: Path to PDF file
            extract_amounts: Whether to extract amount and date (more complex parsing)

        Returns:
            List of transaction dictionaries with keys: text, amount (optional), date (optional)
        """
        transactions = []

        # Try pdfplumber first (better for tables)
        if HAS_PDFPLUMBER:
            try:
                transactions = self._parse_with_pdfplumber(pdf_path, extract_amounts)
                if transactions:
                    logger.info(f"Extracted {len(transactions)} transactions using pdfplumber")
                    return transactions
            except Exception as e:
                logger.warning(f"pdfplumber parsing failed: {e}, falling back to PyMuPDF")

        # Fallback to PyMuPDF
        if HAS_PYMUPDF:
            try:
                transactions = self._parse_with_pymupdf(pdf_path, extract_amounts)
                if transactions:
                    logger.info(f"Extracted {len(transactions)} transactions using PyMuPDF")
                    return transactions
            except Exception as e:
                logger.error(f"PyMuPDF parsing also failed: {e}")

        return transactions

    def _parse_with_pdfplumber(self, pdf_path: str, extract_amounts: bool) -> List[Dict[str, any]]:
        """Parse PDF using pdfplumber (table-based extraction)"""
        transactions = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Try extracting tables first
                tables = page.extract_tables()

                if tables:
                    # Process tables
                    for table in tables:
                        page_transactions = self._extract_from_table(table, extract_amounts)
                        transactions.extend(page_transactions)
                else:
                    # Fallback to text extraction
                    text = page.extract_text()
                    if text:
                        page_transactions = self._extract_from_text(text, extract_amounts)
                        transactions.extend(page_transactions)

        return transactions

    def _parse_with_pymupdf(self, pdf_path: str, extract_amounts: bool) -> List[Dict[str, any]]:
        """Parse PDF using PyMuPDF (text-based extraction)"""
        transactions = []

        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if text:
                page_transactions = self._extract_from_text(text, extract_amounts)
                transactions.extend(page_transactions)

        doc.close()
        return transactions

    def _extract_from_table(self, table: List[List[str]], extract_amounts: bool) -> List[Dict[str, any]]:
        """Extract transactions from a table structure"""
        transactions = []

        if not table or len(table) < 2:
            return transactions

        # Assume first row is header
        headers = [str(h).lower() if h else '' for h in table[0]]

        # Find column indices
        desc_idx = self._find_column_index(headers, ['description', 'transaction', 'particulars', 'narration', 'details'])
        amount_idx = self._find_column_index(headers, ['amount', 'debit', 'withdrawal', 'paid']) if extract_amounts else None
        date_idx = self._find_column_index(headers, ['date', 'transaction date', 'value date']) if extract_amounts else None

        # Process data rows
        for row in table[1:]:
            if not row or len(row) == 0:
                continue

            # Extract description
            description = None
            if desc_idx is not None and desc_idx < len(row):
                description = str(row[desc_idx]).strip() if row[desc_idx] else None

            # If no description column found, try to find text in any column
            if not description:
                for cell in row:
                    if cell and isinstance(cell, str) and len(cell.strip()) > 5:
                        description = cell.strip()
                        break

            if not description or self._is_header_or_footer(description):
                continue

            transaction = {'text': description}

            # Extract amount if requested
            if extract_amounts and amount_idx is not None and amount_idx < len(row):
                amount_str = str(row[amount_idx]).strip() if row[amount_idx] else None
                if amount_str:
                    amount = self._parse_amount(amount_str)
                    if amount:
                        transaction['amount'] = amount

            # Extract date if requested
            if extract_amounts and date_idx is not None and date_idx < len(row):
                date_str = str(row[date_idx]).strip() if row[date_idx] else None
                if date_str:
                    date = self._parse_date(date_str)
                    if date:
                        transaction['date'] = date

            transactions.append(transaction)

        return transactions

    def _extract_from_text(self, text: str, extract_amounts: bool) -> List[Dict[str, any]]:
        """Extract transactions from plain text"""
        transactions = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines, headers, footers
            if not line or len(line) < 10 or self._is_header_or_footer(line):
                continue

            # Look for transaction patterns
            # Common pattern: date + description + amount
            # Example: "15/01/2024  NETFLIX SUBSCRIPTION  INR 649.00"

            if extract_amounts:
                # Try to extract structured data
                match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s*$', line)
                if match:
                    date_str, description, amount_str = match.groups()
                    transaction = {
                        'text': description.strip(),
                        'amount': self._parse_amount(amount_str),
                        'date': self._parse_date(date_str)
                    }
                    transactions.append(transaction)
                    continue

            # Fallback: treat entire line as transaction description
            # Remove date and amount if present at the start/end
            cleaned = re.sub(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+', '', line)  # Remove leading date
            cleaned = re.sub(r'\s+[\d,]+\.?\d*\s*$', '', cleaned)  # Remove trailing amount
            cleaned = cleaned.strip()

            if cleaned and len(cleaned) > 5:
                transactions.append({'text': cleaned})

        return transactions

    def _find_column_index(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords"""
        for keyword in keywords:
            for idx, header in enumerate(headers):
                if keyword in header:
                    return idx
        return None

    def _is_header_or_footer(self, text: str) -> bool:
        """Check if text is likely a header or footer"""
        text_lower = text.lower()

        # Common header/footer patterns
        skip_patterns = [
            'page', 'statement', 'account', 'branch', 'ifsc', 'customer',
            'opening balance', 'closing balance', 'total', 'subtotal',
            'continued', 'date', 'particulars', 'debit', 'credit', 'balance',
            'generated on', 'printed on', 'bank', 'address', 'phone'
        ]

        return any(pattern in text_lower for pattern in skip_patterns)

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            # Remove currency symbols, commas
            cleaned = re.sub(r'[^\d.-]', '', amount_str)
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        try:
            # Try common date formats
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except Exception:
            return None


def parse_bank_statement_pdf(pdf_path: str, extract_amounts: bool = False) -> List[str]:
    """
    Convenience function to extract transaction texts from PDF

    Args:
        pdf_path: Path to PDF file
        extract_amounts: Whether to extract amounts and dates

    Returns:
        List of transaction description strings
    """
    parser = PDFBankStatementParser()
    transactions = parser.parse_pdf(pdf_path, extract_amounts=extract_amounts)
    return [txn['text'] for txn in transactions if 'text' in txn]
