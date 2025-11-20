"""
Transaction Pattern Definitions
Regex patterns for extracting information from various transaction formats
"""

import re
from typing import Dict, List, Optional, Pattern
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    channel: Optional[str] = None
    merchant: Optional[str] = None
    reference: Optional[str] = None
    receiver: Optional[str] = None
    sender: Optional[str] = None
    location: Optional[str] = None
    matched_pattern: Optional[str] = None


class TransactionPatterns:
    """
    Comprehensive pattern matching for various transaction formats
    Supports: UPI, IMPS, NEFT, RTGS, POS, ATM, Card transactions
    """

    # UPI Patterns
    UPI_PATTERNS = [
        # UPI-REF-MERCHANT
        re.compile(r'UPI[-/]?(\d+)[-/]?(.+?)(?:\s|$)', re.IGNORECASE),
        # UPI/MERCHANT/REF
        re.compile(r'UPI[/\-\s]+([A-Za-z0-9\s]+)[/\-]+(\d+)', re.IGNORECASE),
        # Standard UPI format
        re.compile(r'UPI\s+(?:TO|FROM)?\s*(.+?)(?:\s+REF\s*[:\-]?\s*(\d+))?', re.IGNORECASE),
        # MERCHANT*UPI or MERCHANT-UPI
        re.compile(r'([A-Za-z0-9]+)[\*\-]UPI', re.IGNORECASE),
    ]

    # IMPS Patterns
    IMPS_PATTERNS = [
        # IMPS-REF-TO-NAME
        re.compile(r'IMPS[-/]?(\d+)[-/]?(?:TO|FROM)?\s*([A-Za-z\s]+)', re.IGNORECASE),
        # IMPS/NAME/REF
        re.compile(r'IMPS[/\-\s]+([A-Za-z\s]+)[/\-]+(\d+)', re.IGNORECASE),
        # Standard IMPS
        re.compile(r'IMPS\s+(?:TO|FROM)?\s*(.+?)(?:\s+REF\s*[:\-]?\s*(\d+))?', re.IGNORECASE),
    ]

    # NEFT Patterns
    NEFT_PATTERNS = [
        # NEFT-REF-TO-NAME
        re.compile(r'NEFT[-/]?(\d+)[-/]?(?:TO|FROM)?\s*([A-Za-z\s]+)', re.IGNORECASE),
        # NEFT/NAME/REF
        re.compile(r'NEFT[/\-\s]+([A-Za-z\s]+)[/\-]+(\d+)', re.IGNORECASE),
        # Standard NEFT
        re.compile(r'NEFT\s+(?:TO|FROM)?\s*(.+?)(?:\s+REF\s*[:\-]?\s*(\d+))?', re.IGNORECASE),
    ]

    # RTGS Patterns
    RTGS_PATTERNS = [
        re.compile(r'RTGS[-/]?(\d+)[-/]?(?:TO|FROM)?\s*([A-Za-z\s]+)', re.IGNORECASE),
        re.compile(r'RTGS[/\-\s]+([A-Za-z\s]+)[/\-]+(\d+)', re.IGNORECASE),
        re.compile(r'RTGS\s+(?:TO|FROM)?\s*(.+?)(?:\s+REF\s*[:\-]?\s*(\d+))?', re.IGNORECASE),
    ]

    # POS (Point of Sale) Patterns
    POS_PATTERNS = [
        # POS REF MERCHANT LOCATION
        re.compile(r'POS\s+(\d+)\s+([A-Za-z0-9\s]+?)(?:\s+([A-Za-z\s]+?))?$', re.IGNORECASE),
        # POS/MERCHANT/LOCATION
        re.compile(r'POS[/\-\s]+(.+?)[/\-\s]+([A-Za-z\s]+)', re.IGNORECASE),
        # Standard POS
        re.compile(r'POS\s+(.+?)(?:\s+AT\s+(.+?))?$', re.IGNORECASE),
    ]

    # ATM Patterns
    ATM_PATTERNS = [
        # ATM WDL REF LOCATION
        re.compile(r'ATM\s+(?:WDL|WITHDRAWAL)\s+(\d+)\s*(.+)?', re.IGNORECASE),
        # ATM/REF/LOCATION
        re.compile(r'ATM[/\-\s]+(\d+)[/\-\s]*(.+)?', re.IGNORECASE),
        # Standard ATM
        re.compile(r'ATM\s+(.+?)(?:\s+AT\s+(.+?))?$', re.IGNORECASE),
    ]

    # Card Transaction Patterns
    CARD_PATTERNS = [
        # Card ending with XXXX at MERCHANT
        re.compile(r'(?:CARD|DEBIT|CREDIT)\s+(?:ENDING\s+)?[X*]*(\d{4})\s+(?:AT|@)\s+(.+)', re.IGNORECASE),
        # Standard card format
        re.compile(r'(?:CARD|DEBIT|CREDIT)\s+(.+?)(?:\s+AT\s+(.+?))?$', re.IGNORECASE),
    ]

    # Reference number patterns
    REFERENCE_PATTERNS = [
        re.compile(r'REF\s*[:\-#]?\s*(\d+)', re.IGNORECASE),
        re.compile(r'TXN\s*[:\-#]?\s*(\d+)', re.IGNORECASE),
        re.compile(r'TRANSACTION\s*[:\-#]?\s*(\d+)', re.IGNORECASE),
        re.compile(r'RRN\s*[:\-#]?\s*(\d+)', re.IGNORECASE),
    ]

    # Location patterns
    LOCATION_PATTERNS = [
        re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:IN|INDIA)?$'),
        re.compile(r'(?:AT|@|IN)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
    ]

    # Merchant patterns
    MERCHANT_PATTERNS = [
        # TO MERCHANT (payment to merchant) - HIGHEST PRIORITY
        re.compile(r'\bTO\s+([A-Z][A-Z0-9\s]+)', re.IGNORECASE),
        # MERCHANT*PAY or MERCHANT-PAY
        re.compile(r'([A-Za-z0-9]+)[\*\-](?:PAY|PAYMENT|PMT)', re.IGNORECASE),
        # Common merchant prefixes
        re.compile(r'(?:PAID\s+TO|FROM)\s+([A-Za-z0-9\s]+)', re.IGNORECASE),
    ]

    # Amount patterns
    AMOUNT_PATTERNS = [
        # INR 1,234.56 or Rs 1234.56
        re.compile(r'(?:INR|RS|₹)\s*([0-9,]+\.?\d*)', re.IGNORECASE),
        # 1234.56 INR
        re.compile(r'([0-9,]+\.?\d*)\s*(?:INR|RS|₹)', re.IGNORECASE),
    ]

    # Date patterns
    DATE_PATTERNS = [
        # DD-MM-YYYY or DD/MM/YYYY
        re.compile(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'),
        # YYYY-MM-DD
        re.compile(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'),
        # DD MMM YYYY
        re.compile(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', re.IGNORECASE),
    ]

    @classmethod
    def extract_channel(cls, text: str) -> Optional[str]:
        """Extract transaction channel from text"""
        text_upper = text.upper()

        if any(pattern.search(text) for pattern in cls.UPI_PATTERNS):
            return "UPI"
        elif any(pattern.search(text) for pattern in cls.IMPS_PATTERNS):
            return "IMPS"
        elif any(pattern.search(text) for pattern in cls.NEFT_PATTERNS):
            return "NEFT"
        elif any(pattern.search(text) for pattern in cls.RTGS_PATTERNS):
            return "RTGS"
        elif any(pattern.search(text) for pattern in cls.POS_PATTERNS):
            return "POS"
        elif any(pattern.search(text) for pattern in cls.ATM_PATTERNS):
            return "ATM"
        elif any(pattern.search(text) for pattern in cls.CARD_PATTERNS):
            return "CARD"

        return None

    @classmethod
    def extract_reference(cls, text: str) -> Optional[str]:
        """Extract reference number from text"""
        for pattern in cls.REFERENCE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    @classmethod
    def extract_location(cls, text: str) -> Optional[str]:
        """Extract location from text"""
        for pattern in cls.LOCATION_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    @classmethod
    def extract_merchant(cls, text: str, channel: Optional[str] = None) -> Optional[str]:
        """Extract merchant name from text based on channel"""
        if not channel:
            channel = cls.extract_channel(text)

        if channel == "UPI":
            for pattern in cls.UPI_PATTERNS:
                match = pattern.search(text)
                if match:
                    # Usually merchant is in group 2 or the last captured group
                    groups = match.groups()
                    merchant = groups[-1] if len(groups) > 1 else groups[0]
                    return merchant.strip() if merchant else None

        elif channel == "IMPS":
            for pattern in cls.IMPS_PATTERNS:
                match = pattern.search(text)
                if match:
                    groups = match.groups()
                    return groups[1].strip() if len(groups) > 1 and groups[1] else None

        elif channel == "POS":
            for pattern in cls.POS_PATTERNS:
                match = pattern.search(text)
                if match:
                    return match.group(1).strip() if match.group(1) else None

        # Try generic merchant patterns
        for pattern in cls.MERCHANT_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()

        # FALLBACK: If no channel and no merchant pattern, use the whole text as merchant
        # This allows the MerchantResolver to fuzzy-match against the gazetteer
        # Remove common noise like transaction IDs, dates, amounts
        cleaned = text
        # Remove trailing/leading numbers and special chars
        cleaned = re.sub(r'^\W+|\W+$', '', cleaned)
        # Remove reference numbers (long digit sequences)
        cleaned = re.sub(r'\s+\d{6,}.*$', '', cleaned)
        # Remove transaction type keywords if they appear alone
        cleaned = re.sub(r'\b(transaction|payment|purchase|order|bill)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # Only return if we have something meaningful (at least 3 chars)
        if len(cleaned) >= 3:
            return cleaned

        return None

    @classmethod
    def match_transaction(cls, text: str) -> PatternMatch:
        """
        Comprehensive pattern matching for transaction text
        Returns PatternMatch object with extracted information
        """
        result = PatternMatch()

        # Extract channel first
        result.channel = cls.extract_channel(text)

        # Extract reference
        result.reference = cls.extract_reference(text)

        # Extract location
        result.location = cls.extract_location(text)

        # Extract merchant based on channel
        result.merchant = cls.extract_merchant(text, result.channel)

        return result
