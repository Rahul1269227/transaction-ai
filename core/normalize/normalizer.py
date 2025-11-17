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
        currency: str = "INR",
        merchant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main normalization method

        Args:
            text: Raw transaction description
            amount: Transaction amount (optional, will try to extract from text)
            date: Transaction date (optional, will try to extract from text)
            currency: Currency code (default: INR)
            merchant: Merchant name (optional, will try to extract from text)

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

        # Use provided merchant or fall back to pattern matching
        final_merchant = merchant if merchant else pattern_match.merchant

        # Build normalized result
        result = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "normalized": {
                "amount": float(extracted_amount) if extracted_amount else None,
                "currency": currency,
                "date": extracted_date,
                "merchant": final_merchant,
                "channel": pattern_match.channel,
                "reference": pattern_match.reference,
                "location": pattern_match.location,
            },
            "pattern_match": {
                "channel": pattern_match.channel,
                "merchant": final_merchant,
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
        Extract enhanced features from normalized transaction
        Returns dict of features suitable for ML models
        """
        pattern_match = normalized_txn.get('pattern_match', {})
        normalized = normalized_txn.get('normalized', {})
        cleaned_text = normalized_txn.get('cleaned_text', '')
        search_text = normalized_txn.get('search_text', cleaned_text)
        text_lower = cleaned_text.lower()

        amount = normalized.get('amount', 0) or 0
        merchant = pattern_match.get('merchant', '')
        channel = pattern_match.get('channel', '')
        date_str = normalized.get('date')

        features = {
            # Channel features
            'is_upi': channel == 'UPI',
            'is_imps': channel == 'IMPS',
            'is_neft': channel == 'NEFT',
            'is_pos': channel == 'POS',
            'is_atm': channel == 'ATM',
            'is_card': channel == 'CARD',
            'has_channel': channel is not None and channel != '',

            # Merchant features
            'has_merchant': merchant is not None and merchant != '',
            'merchant_length': len(merchant) if merchant else 0,
            'has_numbers_in_merchant': bool(re.search(r'\d', merchant)) if merchant else False,
            'merchant_word_count': len(merchant.split()) if merchant else 0,

            # Amount features (enhanced)
            'amount': amount,
            'amount_log': FeatureExtractor._safe_log(amount),
            'amount_sqrt': FeatureExtractor._safe_sqrt(amount),
            'amount_bucket': FeatureExtractor._get_amount_bucket(amount),
            'is_round_amount': amount > 0 and amount % 100 == 0,
            'is_round_amount_50': amount > 0 and amount % 50 == 0,
            'amount_rounded_to_100': round(amount / 100) * 100 if amount > 0 else 0,
            'amount_digits': len(str(int(amount))) if amount > 0 else 0,

            # Text features (enhanced)
            'text_length': len(cleaned_text),
            'word_count': len(cleaned_text.split()),
            'has_numbers': bool(re.search(r'\d', cleaned_text)),
            'has_special_chars': bool(re.search(r'[^\w\s]', cleaned_text)),
            'has_reference': pattern_match.get('reference') is not None,
            'has_location': pattern_match.get('location') is not None,
            'uppercase_ratio': sum(1 for c in cleaned_text if c.isupper()) / max(len(cleaned_text), 1),
            'digit_ratio': sum(1 for c in cleaned_text if c.isdigit()) / max(len(cleaned_text), 1),

            # N-gram features (bigrams for common patterns)
            'has_bigram_bill_payment': 'bill payment' in text_lower or 'billpayment' in text_lower,
            'has_bigram_fee_charge': any(phrase in text_lower for phrase in ['fee charge', 'service charge', 'penalty charge']),
            'has_bigram_utility_bill': any(phrase in text_lower for phrase in ['utility bill', 'electricity bill', 'water bill', 'phone bill']),
            'has_bigram_card_payment': 'card payment' in text_lower or 'cardpayment' in text_lower,
            'has_bigram_online_order': 'online order' in text_lower or 'onlineorder' in text_lower,

            # Category-specific keyword features (enhanced)
            'contains_fuel': any(kw in text_lower for kw in ['hpcl', 'iocl', 'bpcl', 'petrol', 'fuel', 'diesel', 'gas']),
            'contains_food': any(kw in text_lower for kw in ['zomato', 'swiggy', 'food', 'restaurant', 'cafe', 'dining']),
            'contains_grocery': any(kw in text_lower for kw in ['bigbasket', 'blinkit', 'zepto', 'grocery', 'dmart', 'supermarket']),
            'contains_transport': any(kw in text_lower for kw in ['uber', 'ola', 'rapido', 'cab', 'taxi', 'auto', 'rickshaw']),
            'contains_bills': any(kw in text_lower for kw in ['bill', 'utility', 'electricity', 'water', 'phone', 'internet', 'bsnl', 'airtel', 'jio']),
            'contains_fees': any(kw in text_lower for kw in ['fee', 'charge', 'penalty', 'service charge', 'bank charge']),
            'contains_shopping': any(kw in text_lower for kw in ['amazon', 'flipkart', 'myntra', 'shopping', 'purchase', 'order']),
            'contains_entertainment': any(kw in text_lower for kw in ['netflix', 'prime', 'hotstar', 'spotify', 'movie', 'cinema']),
            'contains_health': any(kw in text_lower for kw in ['hospital', 'doctor', 'pharmacy', 'medical', 'medicine', 'clinic']),
            'contains_education': any(kw in text_lower for kw in ['school', 'college', 'tuition', 'course', 'education', 'exam']),
            'contains_investment': any(kw in text_lower for kw in ['mutual fund', 'sip', 'investment', 'stocks', 'shares']),

            # Temporal features
            'day_of_month': FeatureExtractor._extract_day_of_month(date_str),
            'is_month_end': FeatureExtractor._is_month_end(date_str),
            'is_weekend': FeatureExtractor._is_weekend(date_str),
            'month': FeatureExtractor._extract_month(date_str),

            # Pattern-based features
            'starts_with_upi': cleaned_text.upper().startswith('UPI'),
            'starts_with_imps': cleaned_text.upper().startswith('IMPS'),
            'starts_with_neft': cleaned_text.upper().startswith('NEFT'),
            'starts_with_pos': cleaned_text.upper().startswith('POS'),
            'starts_with_atm': cleaned_text.upper().startswith('ATM'),
            'contains_at': ' AT ' in cleaned_text.upper() or ' AT ' in cleaned_text,
            'contains_to': ' TO ' in cleaned_text.upper() or ' to ' in text_lower,
            'contains_ref': 'ref' in text_lower or 'reference' in text_lower,
        }

        return features

    @staticmethod
    def _safe_log(value: float) -> float:
        """Safe logarithm"""
        import math
        if value > 0:
            return math.log1p(value)
        return 0.0

    @staticmethod
    def _safe_sqrt(value: float) -> float:
        """Safe square root"""
        import math
        if value >= 0:
            return math.sqrt(value)
        return 0.0

    @staticmethod
    def _get_amount_bucket(amount: Optional[float]) -> int:
        """Bucket amount into numeric categories (better for ML)"""
        if amount is None or amount == 0:
            return 0
        elif amount < 100:
            return 1  # very_small
        elif amount < 500:
            return 2  # small
        elif amount < 2000:
            return 3  # medium
        elif amount < 10000:
            return 4  # large
        else:
            return 5  # very_large

    @staticmethod
    def _extract_day_of_month(date_str: Optional[str]) -> int:
        """Extract day of month from date string"""
        if not date_str:
            return 0
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.day
        except:
            return 0

    @staticmethod
    def _extract_month(date_str: Optional[str]) -> int:
        """Extract month from date string"""
        if not date_str:
            return 0
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.month
        except:
            return 0

    @staticmethod
    def _is_month_end(date_str: Optional[str]) -> bool:
        """Check if date is near month end (last 5 days)"""
        if not date_str:
            return False
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.day >= 25
        except:
            return False

    @staticmethod
    def _is_weekend(date_str: Optional[str]) -> bool:
        """Check if date is weekend"""
        if not date_str:
            return False
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.weekday() >= 5  # Saturday = 5, Sunday = 6
        except:
            return False
