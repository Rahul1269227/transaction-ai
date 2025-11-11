"""
Transaction Normalizer
Cleans and normalizes transaction descriptions for better categorization
"""

import re
import unicodedata
from typing import Dict, Optional, Any
from datetime import datetime
from decimal import Decimal

from .patterns import TransactionPatterns, PatternMatch


class TransactionNormalizer:
    """
    Normalizes transaction text through multiple stages:
    1. Unicode normalization
    2. Text cleaning (special chars, extra spaces)
    3. Pattern extraction (channel, merchant, reference, etc.)
    4. Amount and date parsing
    """

    # Common stopwords to remove (but preserve merchant names)
    STOPWORDS = {
        'the', 'and', 'or', 'a', 'an', 'to', 'from', 'in', 'at', 'on', 'for',
        'with', 'by', 'of', 'as', 'is', 'was', 'are', 'were', 'been', 'being'
    }

    # Characters to remove
    SPECIAL_CHARS = r'[^\w\s\-./:\d]'

    # Common abbreviations to expand
    ABBREVIATIONS = {
        'txn': 'transaction',
        'ref': 'reference',
        'pymnt': 'payment',
        'pmt': 'payment',
        'rcvd': 'received',
        'wdl': 'withdrawal',
        'dep': 'deposit',
        'chq': 'cheque',
        'ck': 'cheque',
    }

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize unicode characters to ASCII"""
        # NFKD normalization followed by ASCII encoding
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text

    @staticmethod
    def clean_text(text: str) -> str:
        """Basic text cleaning"""
        # Convert to string if not already
        text = str(text).strip()

        # Normalize unicode
        text = TransactionNormalizer.normalize_unicode(text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep important ones
        # Keep: alphanumeric, spaces, hyphens, slashes, periods, colons, asterisks
        text = re.sub(r'[^\w\s\-./:\*@]', ' ', text)

        # Remove multiple consecutive special chars
        text = re.sub(r'[-./:\*@]{2,}', ' ', text)

        # Trim again
        text = ' '.join(text.split())

        return text

    @staticmethod
    def expand_abbreviations(text: str) -> str:
        """Expand common abbreviations"""
        words = text.lower().split()
        expanded = []

        for word in words:
            # Check if word is an abbreviation
            if word in TransactionNormalizer.ABBREVIATIONS:
                expanded.append(TransactionNormalizer.ABBREVIATIONS[word])
            else:
                expanded.append(word)

        return ' '.join(expanded)

    @staticmethod
    def extract_amount(text: str, fallback_amount: Optional[float] = None) -> Optional[Decimal]:
        """Extract amount from transaction text or use fallback"""
        if fallback_amount is not None:
            return Decimal(str(fallback_amount))

        for pattern in TransactionPatterns.AMOUNT_PATTERNS:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return Decimal(amount_str)
                except:
                    continue

        return None

    @staticmethod
    def extract_date(text: str, fallback_date: Optional[str] = None) -> Optional[str]:
        """Extract date from transaction text or use fallback"""
        if fallback_date:
            return TransactionNormalizer.parse_date(fallback_date)

        for pattern in TransactionPatterns.DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                date_str = match.group(1)
                parsed = TransactionNormalizer.parse_date(date_str)
                if parsed:
                    return parsed

        return None

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Parse date string to ISO format (YYYY-MM-DD)"""
        # List of common date formats
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d-%m-%y',
            '%d/%m/%y',
            '%d %b %Y',
            '%d %B %Y',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        return None

    @staticmethod
    def normalize(
        text: str,
        amount: Optional[float] = None,
        date: Optional[str] = None,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Main normalization method

        Args:
            text: Raw transaction description
            amount: Transaction amount (optional, will try to extract from text)
            date: Transaction date (optional, will try to extract from text)
            currency: Currency code (default: INR)

        Returns:
            Dict with normalized transaction data
        """
        # Clean text
        cleaned_text = TransactionNormalizer.clean_text(text)

        # Extract patterns
        pattern_match = TransactionPatterns.match_transaction(cleaned_text)

        # Extract amount and date
        extracted_amount = TransactionNormalizer.extract_amount(text, amount)
        extracted_date = TransactionNormalizer.extract_date(text, date)

        # Build normalized result
        result = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "normalized": {
                "amount": float(extracted_amount) if extracted_amount else None,
                "currency": currency,
                "date": extracted_date,
                "merchant": pattern_match.merchant,
                "channel": pattern_match.channel,
                "reference": pattern_match.reference,
                "location": pattern_match.location,
            },
            "pattern_match": {
                "channel": pattern_match.channel,
                "merchant": pattern_match.merchant,
                "reference": pattern_match.reference,
                "location": pattern_match.location,
            },
            # For downstream processing
            "search_text": TransactionNormalizer.create_search_text(cleaned_text, pattern_match)
        }

        return result

    @staticmethod
    def create_search_text(cleaned_text: str, pattern_match: PatternMatch) -> str:
        """
        Create optimized search text for embedding and classification
        Combines cleaned text with extracted structured fields
        """
        parts = [cleaned_text]

        if pattern_match.channel:
            parts.append(f"channel:{pattern_match.channel}")

        if pattern_match.merchant:
            parts.append(f"merchant:{pattern_match.merchant}")

        if pattern_match.location:
            parts.append(f"location:{pattern_match.location}")

        return " ".join(parts)

    @staticmethod
    def normalize_batch(transactions: list) -> list:
        """Normalize a batch of transactions"""
        results = []

        for txn in transactions:
            if isinstance(txn, dict):
                normalized = TransactionNormalizer.normalize(
                    text=txn.get('text', txn.get('description', '')),
                    amount=txn.get('amount'),
                    date=txn.get('date', txn.get('timestamp')),
                    currency=txn.get('currency', 'INR')
                )
                results.append(normalized)
            elif isinstance(txn, str):
                normalized = TransactionNormalizer.normalize(txn)
                results.append(normalized)
            else:
                results.append(None)

        return results


# Feature extractors for ML
class FeatureExtractor:
    """Extract handcrafted features for ML models"""

    @staticmethod
    def extract_features(normalized_txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from normalized transaction
        Returns dict of features suitable for ML models
        """
        pattern_match = normalized_txn.get('pattern_match', {})
        normalized = normalized_txn.get('normalized', {})
        cleaned_text = normalized_txn.get('cleaned_text', '')

        features = {
            # Channel features
            'is_upi': pattern_match.get('channel') == 'UPI',
            'is_imps': pattern_match.get('channel') == 'IMPS',
            'is_neft': pattern_match.get('channel') == 'NEFT',
            'is_pos': pattern_match.get('channel') == 'POS',
            'is_atm': pattern_match.get('channel') == 'ATM',
            'is_card': pattern_match.get('channel') == 'CARD',
            'has_channel': pattern_match.get('channel') is not None,

            # Merchant features
            'has_merchant': pattern_match.get('merchant') is not None,
            'merchant_length': len(pattern_match.get('merchant', '')) if pattern_match.get('merchant') else 0,

            # Amount features
            'amount': normalized.get('amount', 0),
            'amount_bucket': FeatureExtractor._get_amount_bucket(normalized.get('amount')),

            # Text features
            'text_length': len(cleaned_text),
            'word_count': len(cleaned_text.split()),
            'has_numbers': bool(re.search(r'\d', cleaned_text)),
            'has_reference': pattern_match.get('reference') is not None,
            'has_location': pattern_match.get('location') is not None,

            # Pattern-based features
            'contains_fuel': any(kw in cleaned_text.lower() for kw in ['hpcl', 'iocl', 'bpcl', 'petrol', 'fuel']),
            'contains_food': any(kw in cleaned_text.lower() for kw in ['zomato', 'swiggy', 'food', 'restaurant']),
            'contains_grocery': any(kw in cleaned_text.lower() for kw in ['bigbasket', 'blinkit', 'grocery', 'dmart']),
            'contains_transport': any(kw in cleaned_text.lower() for kw in ['uber', 'ola', 'cab', 'taxi']),
        }

        return features

    @staticmethod
    def _get_amount_bucket(amount: Optional[float]) -> str:
        """Bucket amount into categories"""
        if amount is None:
            return 'unknown'
        elif amount < 100:
            return 'very_small'
        elif amount < 500:
            return 'small'
        elif amount < 2000:
            return 'medium'
        elif amount < 10000:
            return 'large'
        else:
            return 'very_large'
