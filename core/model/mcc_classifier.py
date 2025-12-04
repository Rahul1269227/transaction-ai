"""
MCC-Based Transaction Classifier
Uses Merchant Category Codes (MCC) for deterministic categorization
"""

import logging
import os
from typing import Optional, Dict, Any
from core.preprocessor import TransactionPreprocessor

logger = logging.getLogger(__name__)

# Load MCC configuration from environment variables
MCC_HIGH_CONFIDENCE = float(os.getenv("MCC_HIGH_CONFIDENCE", "0.95"))
MCC_LOW_CONFIDENCE = float(os.getenv("MCC_LOW_CONFIDENCE", "0.85"))


class MCCClassifier:
    """
    Classifier that uses Merchant Category Codes (MCC) to categorize transactions.

    MCCs are standardized 4-digit codes used by credit card companies to classify
    the business type of merchants. When available, they provide highly reliable
    categorization signals.

    Confidence levels:
    - 0.95: Direct MCC match with well-established mapping
    - 0.85: MCC match but category could overlap (e.g., some retail codes)
    - 0.00: No MCC available or unknown MCC code
    """

    def __init__(self):
        self.preprocessor = TransactionPreprocessor()
        self.mcc_mapping = self.preprocessor.MCC_MAPPING

        # MCC codes that have high confidence (non-overlapping categories)
        self.high_confidence_mccs = {
            # Airlines - very specific
            '3000', '3001', '3002', '3003', '3004', '3005', '3006', '3007',
            '3008', '3009', '3010', '3050', '3298', '4511',

            # Fuel - very specific
            '5541', '5542', '5983',

            # Utilities - very specific
            '4900',

            # Healthcare - very specific
            '8011', '8021', '8031', '8041', '8042', '8043', '8049', '8050', '8062', '8071', '8099',

            # Education - very specific
            '8211', '8220', '8241', '8244', '8249', '8299',

            # Restaurants - very specific
            '5812', '5814', '5813', '5811',

            # Groceries - very specific
            '5411', '5422', '5451', '5462', '5499',

            # Transport - very specific
            '4111', '4112', '4121', '4131', '4784', '4789',

            # ATM - very specific
            '6011',

            # Hotels - very specific
            '7011', '7012',
        }

        logger.info(f"MCC Classifier initialized with {len(self.mcc_mapping)} MCC mappings")

    def categorize(
        self,
        text: str,
        mcc: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Categorize a transaction using MCC code.

        Args:
            text: Transaction description (used for extracting MCC if not provided)
            mcc: Optional MCC code (4-digit string)
            **kwargs: Additional parameters (ignored)

        Returns:
            Dict with keys:
            - category: The predicted category name
            - confidence: Confidence score (0.0 to 1.0)
            - mcc_code: The MCC code used (if any)
            - method: Always "mcc"
        """
        # Try to extract MCC from structured transaction data if not provided
        if not mcc:
            try:
                import json
                data = json.loads(text)
                if isinstance(data, dict):
                    mcc = self.preprocessor._find_mcc(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to extract MCC from plain text patterns like "POS PUR / 5541 / MERCHANT"
        # Common patterns: "/ 5541 /", "MCC:5541", "MCC 5541", "(5541)"
        if not mcc:
            import re
            # Pattern: 4-digit number that's a valid MCC, surrounded by delimiters
            mcc_patterns = [
                r'[/\s](\d{4})[/\s]',      # / 5541 / or space-delimited
                r'MCC[:\s]*(\d{4})',        # MCC:5541 or MCC 5541
                r'\((\d{4})\)',             # (5541)
                r'^(\d{4})[/\s]',           # 5541 / at start
            ]
            for pattern in mcc_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    potential_mcc = match.group(1)
                    # Validate it's a known MCC code
                    if potential_mcc in self.mcc_mapping:
                        mcc = potential_mcc
                        logger.info(f"Extracted MCC {mcc} from plain text: {text[:50]}...")
                        break

        # If no MCC available, return low confidence with default category
        if not mcc:
            logger.debug("No MCC code available for classification")
            return {
                "category": "Other",
                "confidence": 0.0,
                "mcc_code": None,
                "method": "mcc"
            }

        # Normalize MCC code (remove spaces, ensure 4 digits)
        mcc = str(mcc).strip()

        # Look up category from MCC mapping
        category = self.mcc_mapping.get(mcc)

        if not category:
            logger.debug(f"Unknown MCC code: {mcc}")
            return {
                "category": "Other",
                "confidence": 0.0,
                "mcc_code": mcc,
                "method": "mcc"
            }

        # Determine confidence based on MCC specificity
        confidence = MCC_HIGH_CONFIDENCE if mcc in self.high_confidence_mccs else MCC_LOW_CONFIDENCE

        logger.info(f"MCC {mcc} → {category} (confidence: {confidence})")

        return {
            "category": category,
            "confidence": confidence,
            "mcc_code": mcc,
            "method": "mcc"
        }

    def categorize_batch(
        self,
        transactions: list,
        mccs: Optional[list] = None,
        **kwargs
    ) -> list:
        """
        Categorize multiple transactions using MCC codes.

        Args:
            transactions: List of transaction texts
            mccs: Optional list of MCC codes (same length as transactions)
            **kwargs: Additional parameters (ignored)

        Returns:
            List of categorization results
        """
        if mccs and len(mccs) != len(transactions):
            raise ValueError("mccs list must have same length as transactions list")

        results = []
        for i, text in enumerate(transactions):
            mcc = mccs[i] if mccs else None
            result = self.categorize(text, mcc=mcc, **kwargs)
            results.append(result)

        return results


# Singleton instance
_mcc_classifier = None


def get_mcc_classifier() -> MCCClassifier:
    """Get or create singleton MCC classifier instance"""
    global _mcc_classifier
    if _mcc_classifier is None:
        _mcc_classifier = MCCClassifier()
    return _mcc_classifier


def categorize_with_mcc(text: str, mcc: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to categorize transaction using MCC.

    Args:
        text: Transaction description
        mcc: Optional MCC code
        **kwargs: Additional parameters

    Returns:
        Categorization result dict
    """
    classifier = get_mcc_classifier()
    return classifier.categorize(text, mcc=mcc, **kwargs)
