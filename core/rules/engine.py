"""
Rule-based Categorization Engine
Fast, deterministic categorization using pattern matching and rules
"""

import re
import yaml
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RuleMatch:
    """Result of rule matching"""
    category: str
    subcategory: Optional[str]
    confidence: float
    matched_rules: List[str]
    explanations: List[str]


class RuleCategorizer:
    """
    Rule-based transaction categorizer
    Uses keywords, patterns, and merchant matching for fast categorization
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Initialize rule categorizer

        Args:
            taxonomy_path: Path to taxonomy YAML file
        """
        self.categories: Dict = {}
        self.keyword_index: Dict[str, List[str]] = {}  # keyword -> category_ids
        self.pattern_index: Dict[str, str] = {}  # compiled pattern -> category_id

        if taxonomy_path:
            self.load_taxonomy(taxonomy_path)

    def load_taxonomy(self, path: str):
        """Load taxonomy from YAML file"""
        taxonomy_file = Path(path)

        if not taxonomy_file.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {path}")

        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            taxonomy = yaml.safe_load(f)

        # Store categories
        for category in taxonomy.get('categories', []):
            cat_id = category['id']
            self.categories[cat_id] = category

            # Index keywords
            for keyword in category.get('keywords', []):
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_index:
                    self.keyword_index[keyword_lower] = []
                self.keyword_index[keyword_lower].append(cat_id)

            # Index patterns (compile regex)
            for pattern_str in category.get('patterns', []):
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    self.pattern_index[pattern_str] = {
                        'pattern': pattern,
                        'category_id': cat_id
                    }
                except re.error:
                    print(f"Warning: Invalid regex pattern: {pattern_str}")

    def categorize(
        self,
        text: str,
        merchant: Optional[str] = None,
        channel: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Optional[RuleMatch]:
        """
        Categorize transaction using rules

        Args:
            text: Transaction text (normalized)
            merchant: Merchant name (if resolved)
            channel: Transaction channel
            amount: Transaction amount

        Returns:
            RuleMatch if categorization successful, None otherwise
        """
        text_lower = text.lower()
        text_upper = text.upper()
        matches: List[Tuple[str, float, List[str]]] = []  # (category_id, score, explanations)

        # DETERMINISTIC RULES (95%+ confidence) - Check FIRST before taxonomy matching
        # These rules are high-precision and should override other methods

        # Rule 1: ATM/Cash withdrawals
        if channel == 'ATM' or any(kw in text_upper for kw in ['ATM CASH', 'ATM WDL', 'ATM WITHDRAWAL', 'CASH WITHDRAWAL']):
            return RuleMatch(
                category="ATM/Cash",
                subcategory="Cash Withdrawal",
                confidence=0.95,
                matched_rules=["deterministic_atm"],
                explanations=["atm_channel_or_keyword"]
            )

        # Rule 2: EMI/Loan payments
        if any(kw in text_upper for kw in ['EMI ', ' EMI', ' LOAN ', 'LOAN REPAYMENT', 'EMI PAYMENT', 'EMI-']):
            return RuleMatch(
                category="EMI/Loan",
                subcategory="Loan Payment",
                confidence=0.95,
                matched_rules=["deterministic_emi"],
                explanations=["emi_or_loan_keyword"]
            )

        # Rule 3: Salary/Income (look for salary keywords)
        if any(kw in text_upper for kw in ['SALARY', 'SAL CREDIT', 'PAYROLL', 'SALARY CREDIT']):
            return RuleMatch(
                category="Income/Salary",
                subcategory="Salary",
                confidence=0.95,
                matched_rules=["deterministic_salary"],
                explanations=["salary_keyword"]
            )

        # Rule 4: Fuel (high-confidence brand matches)
        fuel_brands = ['hpcl', 'iocl', 'bpcl', 'indian oil', 'bharat petroleum', 'hindustan petroleum']
        if any(brand in text_lower for brand in fuel_brands):
            return RuleMatch(
                category="Fuel",
                subcategory="Petrol/Diesel",
                confidence=0.95,
                matched_rules=["deterministic_fuel"],
                explanations=["fuel_brand_keyword"]
            )

        # Rule 5: Fees & Charges (small amounts + fee keywords)
        if amount and amount < 500:
            fee_keywords = ['fee', 'charge', 'penalty', 'service charge', 'bank charge', 'service fee']
            if any(kw in text_lower for kw in fee_keywords):
                return RuleMatch(
                    category="Fees & Charges",
                    subcategory="Bank Fees",
                    confidence=0.90,  # Slightly lower as amount-based
                    matched_rules=["deterministic_fee"],
                    explanations=["fee_keyword_small_amount"]
                )

        # Strategy 1: Merchant-based categorization (highest priority after deterministic rules)
        if merchant:
            merchant_match = self._match_merchant(merchant)
            if merchant_match:
                return merchant_match

        # Strategy 2: Keyword matching
        keyword_matches = self._match_keywords(text_lower)
        matches.extend(keyword_matches)

        # Strategy 3: Pattern matching
        pattern_matches = self._match_patterns(text)
        matches.extend(pattern_matches)

        # Strategy 4: Channel-based hints
        channel_matches = self._match_channel(channel, text_lower)
        matches.extend(channel_matches)

        # Strategy 5: Amount-based hints
        amount_matches = self._match_amount(amount, text_lower)
        matches.extend(amount_matches)

        # Aggregate scores by category
        category_scores: Dict[str, Tuple[float, List[str]]] = {}

        for cat_id, score, explanations in matches:
            if cat_id not in category_scores:
                category_scores[cat_id] = (0.0, [])

            current_score, current_explanations = category_scores[cat_id]
            category_scores[cat_id] = (
                current_score + score,
                current_explanations + explanations
            )

        # Find best match
        if category_scores:
            best_cat_id = max(category_scores.keys(), key=lambda k: category_scores[k][0])
            best_score, best_explanations = category_scores[best_cat_id]

            # Normalize score to 0-1 range
            confidence = min(1.0, best_score / 3.0)  # Divide by max possible matches

            category = self.categories[best_cat_id]

            return RuleMatch(
                category=category['name'],
                subcategory=self._get_best_subcategory(category, text_lower),
                confidence=confidence,
                matched_rules=[best_cat_id],
                explanations=best_explanations
            )

        return None

    def _match_merchant(self, merchant: str) -> Optional[RuleMatch]:
        """Match based on merchant name"""
        merchant_lower = merchant.lower()

        # Direct keyword match on merchant
        for keyword, cat_ids in self.keyword_index.items():
            if keyword in merchant_lower:
                cat_id = cat_ids[0]  # Take first matching category
                category = self.categories[cat_id]

                return RuleMatch(
                    category=category['name'],
                    subcategory=self._get_best_subcategory(category, merchant_lower),
                    confidence=0.95,  # High confidence for merchant match
                    matched_rules=[cat_id],
                    explanations=[f"merchant_keyword={keyword}"]
                )

        return None

    def _match_keywords(self, text: str) -> List[Tuple[str, float, List[str]]]:
        """Match keywords in text"""
        matches = []

        for keyword, cat_ids in self.keyword_index.items():
            if keyword in text:
                for cat_id in cat_ids:
                    matches.append((
                        cat_id,
                        1.0,  # Base score for keyword match
                        [f"keyword={keyword}"]
                    ))

        return matches

    def _match_patterns(self, text: str) -> List[Tuple[str, float, List[str]]]:
        """Match regex patterns"""
        matches = []

        for pattern_str, pattern_info in self.pattern_index.items():
            pattern = pattern_info['pattern']
            cat_id = pattern_info['category_id']

            if pattern.search(text):
                matches.append((
                    cat_id,
                    1.2,  # Slightly higher score for pattern match
                    [f"pattern={pattern_str[:50]}"]
                ))

        return matches

    def _match_channel(
        self,
        channel: Optional[str],
        text: str
    ) -> List[Tuple[str, float, List[str]]]:
        """Provide hints based on channel type"""
        if not channel:
            return []

        matches = []

        # Channel-specific hints
        if channel == "ATM":
            matches.append(("atm_cash", 0.8, [f"channel={channel}"]))

        elif channel in ["UPI", "IMPS", "NEFT", "RTGS"]:
            # Could be transfer or payment
            # Check if it's a known merchant or person name
            if any(kw in text for kw in ['to', 'from', 'transfer']):
                matches.append(("transfers_upi", 0.6, [f"channel={channel}"]))

        elif channel == "POS":
            # Point of sale - likely shopping or fuel
            if any(kw in text for kw in ['hpcl', 'iocl', 'bpcl', 'fuel', 'petrol']):
                matches.append(("fuel", 0.7, [f"channel={channel}"]))

        return matches

    def _match_amount(
        self,
        amount: Optional[float],
        text: str
    ) -> List[Tuple[str, float, List[str]]]:
        """Provide hints based on amount patterns"""
        if amount is None:
            return []

        matches = []

        # Amount-based hints (weak signals)
        if amount >= 10000:
            # Large amounts could be rent, EMI, investments
            if any(kw in text for kw in ['rent', 'lease', 'emi', 'loan']):
                matches.append(("rent", 0.5, ["amount_pattern=large"]))
            elif any(kw in text for kw in ['invest', 'mutual fund', 'sip']):
                matches.append(("investments", 0.5, ["amount_pattern=large"]))

        elif amount < 100:
            # Small amounts could be recharges, utilities
            if any(kw in text for kw in ['recharge', 'mobile', 'dth']):
                matches.append(("utilities", 0.4, ["amount_pattern=small"]))

        return matches

    def _get_best_subcategory(self, category: Dict, text: str) -> Optional[str]:
        """Determine best subcategory based on text"""
        subcategories = category.get('subcategories', [])

        if not subcategories:
            return None

        # Simple heuristic: check which subcategory keywords appear
        for subcat in subcategories:
            subcat_lower = subcat.lower()
            # Check if subcategory name appears in text
            if any(word in text for word in subcat_lower.split()):
                return subcat

        # Return first subcategory as default
        return subcategories[0] if subcategories else None

    def get_category_info(self, category_id: str) -> Optional[Dict]:
        """Get category information by ID"""
        return self.categories.get(category_id)

    def get_all_categories(self) -> List[Dict]:
        """Get all categories"""
        return list(self.categories.values())

    def categorize_batch(self, transactions: List[Dict]) -> List[Optional[RuleMatch]]:
        """Categorize a batch of transactions"""
        results = []

        for txn in transactions:
            result = self.categorize(
                text=txn.get('text', ''),
                merchant=txn.get('merchant'),
                channel=txn.get('channel'),
                amount=txn.get('amount')
            )
            results.append(result)

        return results
