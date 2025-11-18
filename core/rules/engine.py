"""
Rule-based Categorization Engine
Fast, deterministic categorization using pattern matching and rules
"""

import os
import re
import yaml
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Load rules configuration from environment variables
RULE_HIGH_CONFIDENCE = float(os.getenv("RULE_HIGH_CONFIDENCE", "0.95"))
RULE_MEDIUM_CONFIDENCE = float(os.getenv("RULE_MEDIUM_CONFIDENCE", "0.90"))
RULE_MAX_CONFIDENCE = float(os.getenv("RULE_MAX_CONFIDENCE", "0.98"))


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
        amount: Optional[float] = None,
        date: Optional[str] = None  # Date in ISO format (YYYY-MM-DD)
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
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_atm"],
                explanations=["atm_channel_or_keyword"]
            )

        # Rule 2: Rent/Housing payments (mortgage, rent, property tax, maintenance)
        if any(kw in text_upper for kw in ['MORTGAGE', 'HOME LOAN', 'HOUSING LOAN', 'MORTGAGE PAYMENT', 'MORTGAGE SERVICE']):
            return RuleMatch(
                category="Rent",
                subcategory="Mortgage/Home Loan",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_mortgage"],
                explanations=["mortgage_keyword"]
            )

        # Property tax
        if any(kw in text_upper for kw in ['PROPERTY TAX', 'HOUSE TAX', 'MUNICIPAL TAX']):
            return RuleMatch(
                category="Rent",
                subcategory="Property Tax",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_property_tax"],
                explanations=["property_tax_keyword"]
            )

        # Rent payments
        if any(kw in text_upper for kw in ['RENT PAYMENT', 'TO LANDLORD', 'RENT TO']):
            return RuleMatch(
                category="Rent",
                subcategory="Rent",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_rent"],
                explanations=["rent_keyword"]
            )

        # Society/Apartment maintenance
        if ('MAINTENANCE' in text_upper and any(kw in text_upper for kw in ['SOCIETY', 'APARTMENT', 'BUILDING', 'HOA'])) or \
           any(kw in text_upper for kw in ['HOA PAYMENT', 'MAINTENANCE CHARGE', 'MAINTENANCE FEE']):
            return RuleMatch(
                category="Rent",
                subcategory="HOA/Maintenance",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_maintenance"],
                explanations=["maintenance_keyword"]
            )

        # Rule 3: EMI/Loan payments
        if any(kw in text_upper for kw in ['EMI ', ' EMI', ' LOAN ', 'LOAN REPAYMENT', 'EMI PAYMENT', 'EMI-']):
            return RuleMatch(
                category="Bills",
                subcategory="Loan EMI",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_emi"],
                explanations=["emi_or_loan_keyword"]
            )

        # Rule 4: Salary/Income (look for salary keywords)
        if any(kw in text_upper for kw in ['SALARY', 'SAL CREDIT', 'PAYROLL', 'SALARY CREDIT']):
            return RuleMatch(
                category="Income/Salary",
                subcategory="Salary",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_salary"],
                explanations=["salary_keyword"]
            )

        # Rule 5: Fuel (high-confidence brand matches)
        fuel_brands = ['hpcl', 'iocl', 'bpcl', 'indian oil', 'bharat petroleum', 'hindustan petroleum']
        if any(brand in text_lower for brand in fuel_brands):
            return RuleMatch(
                category="Fuel",
                subcategory="Petrol/Diesel",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_fuel"],
                explanations=["fuel_brand_keyword"]
            )

        # Rule 6: Fees & Charges (small amounts + fee keywords)
        # Only apply if no clear merchant is present (avoid false positives for small purchases)
        if amount and amount < 500:
            # Use word boundaries to avoid false matches (e.g., "coffee" contains "fee")
            fee_patterns = [r'\bfee\b', r'\bcharge\b', r'\bpenalty\b', r'service charge', r'bank charge', r'service fee']
            has_fee_keyword = any(re.search(pattern, text_lower) for pattern in fee_patterns)

            # Exclude if it has recognizable merchant names
            non_fee_merchants = ['starbucks', 'coffee', 'cafe', 'restaurant', 'food', 'grocery', 'store']
            has_merchant = any(m in text_lower for m in non_fee_merchants)

            if has_fee_keyword and not has_merchant:
                return RuleMatch(
                    category="Fees & Charges",
                    subcategory="Bank Fees",
                    confidence=RULE_MEDIUM_CONFIDENCE,  # Slightly lower as amount-based
                    matched_rules=["deterministic_fee"],
                    explanations=["fee_keyword_small_amount"]
                )

        # Rule 6: Subscription Services from Known Merchants (Apple, Netflix, Spotify, etc.)
        # High confidence for well-known subscription services
        subscription_merchants = [
            'apple.com', 'apple.com/bill', 'netflix', 'spotify', 'google.com/bill',
            'microsoft.com', 'adobe.com', 'amazon prime', 'disney', 'hotstar',
            'youtube premium', 'apple music', 'apple tv'
        ]
        if any(merchant in text_lower for merchant in subscription_merchants):
            return RuleMatch(
                category="Bills",
                subcategory="Subscription",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_subscription"],
                explanations=["subscription_merchant"]
            )

        # Rule 7: Fraud & Security - Suspicious International Transactions
        # Pattern: "INTL TRX" + fraud keywords (not just INTL TRX alone)
        # Exclude legitimate international merchants (Apple, Netflix, Spotify, etc.)
        fraud_keywords = ['unauthorized', 'fraud alert', 'suspicious activity', 'disputed charge', 'chargeback']
        intl_keywords = ['intl trx', 'international transaction', 'intl txn']

        # Check for direct fraud keywords (high confidence)
        if any(kw in text_lower for kw in fraud_keywords):
            return RuleMatch(
                category="Fraud & Security",
                subcategory="Suspicious International",
                confidence=RULE_HIGH_CONFIDENCE,
                matched_rules=["deterministic_fraud"],
                explanations=["fraud_keyword"]
            )

        # Check for INTL TRX + unauthorized (not just INTL TRX alone, as it could be legitimate subscriptions)
        # Only flag as fraud if INTL appears with actual fraud indicators
        if any(intl in text_lower for intl in intl_keywords):
            # Check if it's NOT a known legitimate international merchant
            legitimate_intl_merchants = ['apple', 'netflix', 'spotify', 'google', 'microsoft', 'amazon', 'adobe']
            if not any(merchant in text_lower for merchant in legitimate_intl_merchants):
                # Only flag if it has "unauthorized" or similar fraud keywords
                if any(kw in text_lower for kw in fraud_keywords):
                    return RuleMatch(
                        category="Fraud & Security",
                        subcategory="Suspicious International",
                        confidence=RULE_HIGH_CONFIDENCE,
                        matched_rules=["deterministic_fraud"],
                        explanations=["intl_fraud_keyword"]
                    )

        # Rule 8: Home Improvement (hardware stores, tools, repairs)
        home_improvement_keywords = [
            'home depot', 'lowes', 'ace hardware', 'menards', 'true value',
            'benjamin moore', 'sherwin williams', 'floor & decor', 'lumber liquidators',
            'harbor freight', 'tractor supply', 'hardware', 'plumber', 'electrician',
            'carpenter', 'contractor', 'renovation', 'repair service', 'handyman',
            'paint store', 'lumber', 'flooring', 'roofing', 'hvac', 'appliance repair'
        ]
        if any(kw in text_lower for kw in home_improvement_keywords):
            return RuleMatch(
                category="Home Improvement",
                subcategory="Hardware/Repairs",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_home_improvement"],
                explanations=["home_improvement_keyword"]
            )

        # Rule 9: Pets (pet stores, vet, grooming, pet food)
        pets_keywords = [
            'petsmart', 'petco', 'chewy', 'pet supplies', 'vca', 'banfield',
            'bluepearl', 'veterinary', 'vet clinic', 'pet hospital', 'dog food',
            'cat food', 'pet food', 'pet grooming', 'dog grooming', 'cat grooming',
            'pet boarding', 'doggy daycare', 'pet sitting', 'dog walking',
            'purina', 'royal canin', 'blue buffalo', 'hills science diet'
        ]
        if any(kw in text_lower for kw in pets_keywords):
            return RuleMatch(
                category="Pets",
                subcategory="Pet Care",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_pets"],
                explanations=["pets_keyword"]
            )

        # Rule 10: Kids & Family (kids stores, daycare, toys, baby products)
        kids_family_keywords = [
            'firstcry', 'hopscotch', 'mothercare', 'babyoye', 'hamleys', 'toys r us',
            'childrens place', 'carters', 'oshkosh', 'gymboree', 'gap kids',
            'buy buy baby', 'pottery barn kids', 'daycare', 'preschool', 'kindergarten',
            'nursery', 'kids activities', 'baby clothes', 'diapers', 'baby formula',
            'pampers', 'huggies', 'baby food', 'kids clothing', 'toys',
            'kids education', 'playschool', 'kids camp', 'kids lessons'
        ]
        if any(kw in text_lower for kw in kids_family_keywords):
            return RuleMatch(
                category="Kids & Family",
                subcategory="Kids Products/Services",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_kids_family"],
                explanations=["kids_family_keyword"]
            )

        # Rule 11: Electronics & Technology (electronics stores, computer stores, tech repairs)
        electronics_keywords = [
            'best buy', 'apple store', 'microsoft store', 'b&h photo', 'micro center',
            'newegg', 'crutchfield', 'gamestop', 'dell', 'hp store', 'lenovo',
            'asus', 'sony store', 'samsung store', 'reliance digital', 'croma',
            'vijay sales', 'sangeetha mobiles', 'poorvika', 'laptop', 'computer',
            'smartphone', 'iphone', 'ipad', 'macbook', 'tablet', 'monitor',
            'keyboard', 'headphones', 'camera', 'electronics repair', 'tech support',
            'geek squad', 'screen replacement', 'laptop repair'
        ]
        if any(kw in text_lower for kw in electronics_keywords):
            return RuleMatch(
                category="Electronics & Technology",
                subcategory="Electronics/Computers",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_electronics"],
                explanations=["electronics_keyword"]
            )

        # Rule 12: Subscriptions & Memberships (streaming, software, cloud, gym, etc.)
        subscription_keywords = [
            'hulu', 'hbo max', 'paramount+', 'peacock', 'discovery+', 'youtube tv',
            'sling tv', 'fubo tv', 'tidal', 'pandora', 'soundcloud',
            'icloud storage', 'google one', 'dropbox', 'onedrive', 'pcloud',
            'office 365', 'microsoft 365', 'grammarly', 'canva pro', 'notion',
            'evernote', 'lastpass', '1password', 'nordvpn', 'expressvpn', 'surfshark',
            'medium membership', 'patreon', 'github pro', 'slack premium', 'zoom pro',
            'asana', 'trello', 'kindle unlimited', 'audible', 'scribd', 'blinkist',
            'peloton', 'apple fitness', 'beachbody', 'fitbit premium', 'strava',
            'playstation plus', 'xbox game pass', 'nintendo online', 'ea play',
            'coursera', 'udemy', 'linkedin learning', 'skillshare', 'masterclass',
            'duolingo', 'babbel', 'rosetta stone', 'costco membership', 'sams club',
            'aaa membership', '24 hour fitness', 'planet fitness', 'la fitness',
            'equinox', 'classpass', 'headspace', 'calm', 'betterhelp',
            'subscription', 'membership', 'premium', 'pro plan', 'recurring payment'
        ]
        if any(kw in text_lower for kw in subscription_keywords):
            return RuleMatch(
                category="Subscriptions & Memberships",
                subcategory="Subscription Service",
                confidence=RULE_MEDIUM_CONFIDENCE,
                matched_rules=["deterministic_subscription_memberships"],
                explanations=["subscription_membership_keyword"]
            )

        # Strategy 1: Temporal pattern detection (boosts confidence for date-based categories)
        temporal_boost = self._match_temporal_patterns(text_lower, date, amount)

        # Strategy 2: Merchant-based categorization (highest priority after deterministic rules)
        if merchant:
            merchant_match = self._match_merchant(merchant)
            if merchant_match:
                # Apply temporal boost if applicable
                if temporal_boost and temporal_boost[0] == self._get_category_id(merchant_match.category):
                    boost_amount, explanation = temporal_boost[1], temporal_boost[2]
                    merchant_match.confidence = min(RULE_MAX_CONFIDENCE, merchant_match.confidence + boost_amount)
                    merchant_match.explanations.append(explanation)
                return merchant_match

        # Strategy 3: Keyword matching
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

            # Apply temporal boost if applicable
            if temporal_boost and temporal_boost[0] == best_cat_id:
                boost_amount, boost_explanation = temporal_boost[1], temporal_boost[2]
                confidence = min(RULE_MAX_CONFIDENCE, confidence + boost_amount)
                best_explanations.append(boost_explanation)

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
                    confidence=RULE_HIGH_CONFIDENCE,  # High confidence for merchant match
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

    def _match_temporal_patterns(
        self,
        text: str,
        date: Optional[str],
        amount: Optional[float]
    ) -> Optional[Tuple[str, float, str]]:
        """
        Detect temporal patterns and boost confidence for date-sensitive categories

        Args:
            text: Transaction text (lowercase)
            date: Transaction date in ISO format (YYYY-MM-DD)
            amount: Transaction amount

        Returns:
            Tuple of (category_id, confidence_boost, explanation) or None
        """
        if not date:
            return None

        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date)
            day_of_month = dt.day
            is_month_start = day_of_month <= 5
            is_month_end = day_of_month >= 25
            is_mid_month = 10 <= day_of_month <= 20

            # Temporal Pattern 1: Salary (typically 1st-5th of month)
            if is_month_start and amount and amount >= 10000:
                if any(kw in text for kw in ['salary', 'credit', 'income', 'payroll', 'sal']):
                    return ("income_salary", 0.10, "temporal_salary_pattern")

            # Temporal Pattern 2: Rent (typically month-end or month-start)
            if (is_month_end or is_month_start) and amount and amount >= 5000:
                if any(kw in text for kw in ['rent', 'lease', 'landlord', 'housing']):
                    return ("rent", 0.10, "temporal_rent_pattern")

            # Temporal Pattern 3: EMI/Loans (typically same date each month, often 1st-10th)
            if day_of_month <= 10 and amount and amount >= 1000:
                if any(kw in text for kw in ['emi', 'loan', 'repayment', 'installment']):
                    return ("bills", 0.08, "temporal_emi_pattern")

            # Temporal Pattern 4: Subscriptions (recurring monthly, often mid-month)
            if any(kw in text for kw in ['subscription', 'recurring', 'monthly', 'netflix', 'spotify', 'prime']):
                return ("bills", 0.08, "temporal_subscription_pattern")

            # Temporal Pattern 5: Utility bills (often mid to end of month)
            if is_mid_month or is_month_end:
                if any(kw in text for kw in ['bill', 'electricity', 'water', 'gas', 'internet', 'broadband']):
                    return ("bills", 0.07, "temporal_utility_pattern")

        except (ValueError, AttributeError):
            # Invalid date format or other error
            pass

        return None

    def _get_category_id(self, category_name: str) -> Optional[str]:
        """Get category ID from category name"""
        for cat_id, category in self.categories.items():
            if category['name'] == category_name:
                return cat_id
        return None

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
