"""
Transaction Preprocessor
Intelligently extracts key information from structured JSON transactions
"""

import json
import re
from typing import Any, Dict, Optional


class TransactionPreprocessor:
    """
    Generic preprocessor that extracts meaningful transaction information
    from complex JSON structures or plain text
    """

    # Common field names for merchants (case-insensitive)
    MERCHANT_FIELDS = [
        'merchant_name', 'merchantname', 'merchant', 'store_name', 'storename',
        'store', 'business_name', 'businessname', 'seller', 'vendor',
        'payee_name', 'payeename', 'payee', 'recipient'
    ]

    # Common field names for amounts
    AMOUNT_FIELDS = [
        'amount', 'value', 'total', 'total_amount', 'totalamount',
        'transaction_amount', 'transactionamount', 'total_debited',
        'debited_amount', 'payment_amount', 'grand_total', 'grandtotal'
    ]

    # Common field names for transaction types/descriptions
    TYPE_FIELDS = [
        'transaction_type', 'transactiontype', 'type', 'description',
        'transaction_description', 'purpose', 'category', 'memo',
        'narration', 'remarks', 'note', 'reference_text'
    ]

    # Common field names for currency
    CURRENCY_FIELDS = ['currency', 'currency_code', 'currencycode']

    # Merchant category codes mapping to readable names
    MCC_MAPPING = {
        '5541': 'Fuel/Service Station',
        '5812': 'Restaurants',
        '5411': 'Grocery Store',
        '5999': 'Retail Store',
        '4111': 'Transportation',
        '4121': 'Taxi/Rideshare',
        '5311': 'Department Store',
        '5732': 'Electronics Store',
        '5912': 'Pharmacy',
        '5942': 'Bookstore',
        '7011': 'Hotel',
        '7832': 'Movie Theater',
        '5814': 'Fast Food',
        '5815': 'Digital Media',
    }

    def __init__(self):
        pass

    def preprocess(self, text: str) -> str:
        """
        Main preprocessing function that handles both JSON and plain text

        Args:
            text: Raw transaction text (could be JSON or plain text)

        Returns:
            Cleaned, concise transaction description
        """
        # Try to parse as JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return self._extract_from_json(data)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, return as-is (might be plain text)
            pass

        # If not JSON or extraction failed, return original (cleaned)
        return self._clean_text(text)

    def _extract_from_json(self, data: Dict[str, Any]) -> str:
        """
        Extract key transaction information from JSON structure

        Strategy:
        1. Find merchant/vendor name
        2. Find transaction type/description
        3. Find amount and currency
        4. Combine into concise description
        """
        parts = []

        # Extract merchant name
        merchant = self._find_merchant(data)
        if merchant:
            parts.append(merchant)

        # Extract transaction type/description
        txn_type = self._find_transaction_type(data)
        if txn_type:
            # Skip if it's generic like "SUCCESS" or just repeats merchant
            if txn_type.upper() not in ['SUCCESS', 'COMPLETED', 'APPROVED']:
                if not merchant or txn_type.lower() not in merchant.lower():
                    parts.append(txn_type)

        # Extract merchant category code (MCC)
        mcc = self._find_mcc(data)
        if mcc and mcc in self.MCC_MAPPING:
            category_hint = self.MCC_MAPPING[mcc]
            parts.append(f"({category_hint})")

        # Extract amount
        amount = self._find_amount(data)
        currency = self._find_currency(data)
        if amount:
            amount_str = f"{currency} {amount}" if currency else f"Rs {amount}"
            parts.append(amount_str)

        # Combine parts
        if parts:
            result = ' '.join(parts)
            # Limit length to avoid timeout
            if len(result) > 500:
                result = result[:497] + "..."
            return result

        # Fallback: convert to compact JSON string
        return self._json_to_compact_text(data)

    def _find_field(self, data: Dict[str, Any], field_names: list, depth: int = 3, prefer_longer: bool = True) -> Optional[str]:
        """
        Recursively search for a field in nested JSON structure

        Args:
            data: JSON object
            field_names: List of possible field names (case-insensitive)
            depth: Maximum recursion depth
            prefer_longer: If True, prefer longer string values (e.g., names over IDs)

        Returns:
            Field value as string, or None if not found
        """
        if depth <= 0:
            return None

        candidates = []

        # Check current level
        for key, value in data.items():
            key_lower = key.lower().replace('_', '').replace('-', '')

            for field_name in field_names:
                field_name_clean = field_name.lower().replace('_', '').replace('-', '')
                if key_lower == field_name_clean or field_name_clean in key_lower:
                    if isinstance(value, (str, int, float)):
                        candidates.append(str(value))
                    elif isinstance(value, dict) and 'value' in value:
                        # Handle nested value objects like {"value": 2000, "currency": "INR"}
                        candidates.append(str(value.get('value', '')))

        # If we found candidates at this level, return the best one
        if candidates:
            if prefer_longer:
                # Prefer longer strings (e.g., "Indian Oil" over "MERCH_001")
                return max(candidates, key=len)
            return candidates[0]

        # Recurse into nested objects
        for value in data.values():
            if isinstance(value, dict):
                result = self._find_field(value, field_names, depth - 1, prefer_longer)
                if result:
                    return result

        return None

    def _find_merchant(self, data: Dict[str, Any]) -> Optional[str]:
        """Find merchant/vendor name in JSON"""
        return self._find_field(data, self.MERCHANT_FIELDS)

    def _find_amount(self, data: Dict[str, Any]) -> Optional[str]:
        """Find transaction amount in JSON"""
        amount = self._find_field(data, self.AMOUNT_FIELDS)
        if amount:
            # Format nicely
            try:
                num = float(amount)
                return f"{num:,.2f}"
            except ValueError:
                return amount
        return None

    def _find_transaction_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Find transaction type/description in JSON"""
        return self._find_field(data, self.TYPE_FIELDS)

    def _find_currency(self, data: Dict[str, Any]) -> Optional[str]:
        """Find currency code in JSON"""
        return self._find_field(data, self.CURRENCY_FIELDS)

    def _find_mcc(self, data: Dict[str, Any]) -> Optional[str]:
        """Find merchant category code in JSON"""
        return self._find_field(data, ['merchant_category_code', 'mcc', 'category_code'])

    def _json_to_compact_text(self, data: Dict[str, Any]) -> str:
        """
        Convert JSON to compact readable text as fallback
        Extracts first few key-value pairs
        """
        parts = []
        count = 0
        max_items = 3

        for key, value in data.items():
            if count >= max_items:
                break
            if isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")
                count += 1
            elif isinstance(value, dict):
                # Get first item from nested dict
                for k, v in value.items():
                    if isinstance(v, (str, int, float)):
                        parts.append(f"{k}: {v}")
                        count += 1
                        break

        result = ', '.join(parts)
        if len(result) > 200:
            result = result[:197] + "..."
        return result

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize plain text transaction descriptions
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Limit length
        if len(text) > 500:
            text = text[:497] + "..."

        return text


# Singleton instance
preprocessor = TransactionPreprocessor()


def preprocess_transaction(text: str) -> str:
    """
    Convenience function to preprocess transaction text

    Args:
        text: Raw transaction text (JSON or plain text)

    Returns:
        Cleaned, concise transaction description
    """
    return preprocessor.preprocess(text)
