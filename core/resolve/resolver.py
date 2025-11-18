"""
Merchant Resolver
Fuzzy matching and alias resolution for merchant names
"""

import csv
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher
from dataclasses import dataclass


@dataclass
class MerchantInfo:
    """Merchant information"""
    merchant_id: str
    canonical_name: str
    aliases: List[str]
    category: str
    subcategory: Optional[str] = None


@dataclass
class MerchantMatch:
    """Merchant match result"""
    merchant_id: str
    canonical_name: str
    aliases: List[str]
    category: str
    subcategory: Optional[str]
    similarity_score: float
    match_type: str  # exact, alias, fuzzy, trigram


class MerchantResolver:
    """
    Merchant resolver with multiple matching strategies:
    1. Exact match on canonical name
    2. Alias matching (exact and fuzzy)
    3. Trigram/n-gram fuzzy matching
    4. Token-based matching
    """

    def __init__(self, gazetteer_path: Optional[str] = None):
        """
        Initialize merchant resolver

        Args:
            gazetteer_path: Path to merchant aliases CSV file
        """
        self.merchants: Dict[str, MerchantInfo] = {}
        self.alias_to_merchant: Dict[str, str] = {}  # alias -> merchant_id
        self.trigram_index: Dict[str, List[str]] = {}  # trigram -> merchant_ids

        if gazetteer_path:
            self.load_gazetteer(gazetteer_path)

    def load_gazetteer(self, path: str):
        """Load merchant gazetteer from CSV file"""
        gazetteer_file = Path(path)

        if not gazetteer_file.exists():
            raise FileNotFoundError(f"Gazetteer file not found: {path}")

        with open(gazetteer_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                merchant_id = row['merchant_id']
                canonical_name = row['canonical_name'].upper()
                aliases_str = row['aliases']
                category = row['category']
                subcategory = row.get('subcategory', None)

                # Parse aliases (comma-separated)
                aliases = [a.strip().upper() for a in aliases_str.split(',')]

                # Create merchant info
                merchant_info = MerchantInfo(
                    merchant_id=merchant_id,
                    canonical_name=canonical_name,
                    aliases=aliases,
                    category=category,
                    subcategory=subcategory
                )

                self.merchants[merchant_id] = merchant_info

                # Build alias index
                self.alias_to_merchant[canonical_name] = merchant_id
                for alias in aliases:
                    self.alias_to_merchant[alias] = merchant_id

                # Build trigram index
                self._index_trigrams(canonical_name, merchant_id)
                for alias in aliases:
                    self._index_trigrams(alias, merchant_id)

    def _index_trigrams(self, text: str, merchant_id: str):
        """Index trigrams for fuzzy matching"""
        text = text.upper()
        # Generate trigrams
        trigrams = self._get_trigrams(text)

        for trigram in trigrams:
            if trigram not in self.trigram_index:
                self.trigram_index[trigram] = []
            if merchant_id not in self.trigram_index[trigram]:
                self.trigram_index[trigram].append(merchant_id)

    def _get_trigrams(self, text: str) -> List[str]:
        """Generate trigrams from text"""
        text = re.sub(r'\s+', '', text)  # Remove spaces
        if len(text) < 3:
            return [text]

        trigrams = []
        for i in range(len(text) - 2):
            trigrams.append(text[i:i+3])

        return trigrams

    def _calculate_trigram_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity based on trigrams"""
        trigrams1 = set(self._get_trigrams(text1.upper()))
        trigrams2 = set(self._get_trigrams(text2.upper()))

        if not trigrams1 or not trigrams2:
            return 0.0

        intersection = trigrams1.intersection(trigrams2)
        union = trigrams1.union(trigrams2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_sequence_similarity(self, text1: str, text2: str) -> float:
        """Calculate sequence similarity using difflib"""
        return SequenceMatcher(None, text1.upper(), text2.upper()).ratio()

    def _clean_merchant_text(self, text: str) -> str:
        """Clean merchant text for matching"""
        # Convert to uppercase
        text = text.upper()

        # Remove common noise patterns
        text = re.sub(r'\*PAY|\*PAYMENT|\-PAY|\-PAYMENT', '', text)
        text = re.sub(r'INTL TRX ', '', text)  # Remove "INTL TRX" prefix
        text = re.sub(r'[\*\-/\.]+', ' ', text)  # Also remove dots
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def resolve(
        self,
        merchant_text: str,
        threshold: float = 0.7,
        top_k: int = 5
    ) -> List[MerchantMatch]:
        """
        Resolve merchant name to canonical merchant

        Args:
            merchant_text: Merchant name from transaction
            threshold: Minimum similarity threshold (0-1)
            top_k: Number of top matches to return

        Returns:
            List of merchant matches sorted by similarity score
        """
        if not merchant_text:
            return []

        # Clean merchant text
        cleaned_text = self._clean_merchant_text(merchant_text)

        matches: List[MerchantMatch] = []

        # Strategy 1: Exact match on canonical name or alias
        exact_match = self._exact_match(cleaned_text)
        if exact_match:
            matches.append(exact_match)
            return matches  # Return immediately for exact matches

        # Strategy 2: Fuzzy match on aliases
        alias_matches = self._fuzzy_alias_match(cleaned_text, threshold)
        matches.extend(alias_matches)

        # Strategy 3: Trigram-based fuzzy matching
        trigram_matches = self._trigram_match(cleaned_text, threshold)
        matches.extend(trigram_matches)

        # Deduplicate and sort by score
        unique_matches = self._deduplicate_matches(matches)
        unique_matches.sort(key=lambda x: x.similarity_score, reverse=True)

        # Return top-k matches above threshold
        return [m for m in unique_matches[:top_k] if m.similarity_score >= threshold]

    def _exact_match(self, text: str) -> Optional[MerchantMatch]:
        """Try exact match on canonical name or aliases"""
        text_upper = text.upper()

        # First try exact match
        if text_upper in self.alias_to_merchant:
            merchant_id = self.alias_to_merchant[text_upper]
            merchant = self.merchants[merchant_id]

            return MerchantMatch(
                merchant_id=merchant_id,
                canonical_name=merchant.canonical_name,
                aliases=merchant.aliases,
                category=merchant.category,
                subcategory=merchant.subcategory,
                similarity_score=1.0,
                match_type='exact'
            )

        # Try substring match (alias in text or text in alias)
        # This helps with "Netflix subscription" matching "NETFLIX" alias
        for alias, merchant_id in self.alias_to_merchant.items():
            # Skip wildcards for substring matching
            if '*' in alias:
                continue

            # Check if alias is a substring of text or vice versa
            # Use word boundary matching to avoid false positives
            alias_clean = alias.replace('*', '').strip()
            if len(alias_clean) >= 4:  # Only for meaningful aliases (4+ chars)
                # Check if alias appears as a word in the text
                if alias_clean in text_upper or text_upper in alias_clean:
                    # Verify it's a word match, not just substring
                    words_in_text = text_upper.split()
                    if alias_clean in words_in_text or any(alias_clean in word for word in words_in_text):
                        merchant = self.merchants[merchant_id]
                        # High score for word-level matches (merchant name found in transaction text)
                        # Don't penalize for extra context words like "coffee grande latte"
                        score = 0.85  # High confidence for clear merchant name matches
                        return MerchantMatch(
                            merchant_id=merchant_id,
                            canonical_name=merchant.canonical_name,
                            aliases=merchant.aliases,
                            category=merchant.category,
                            subcategory=merchant.subcategory,
                            similarity_score=score,
                            match_type='substring'
                        )

        return None

    def _fuzzy_alias_match(self, text: str, threshold: float) -> List[MerchantMatch]:
        """Fuzzy match against all aliases"""
        matches = []

        for alias, merchant_id in self.alias_to_merchant.items():
            # Calculate similarity
            similarity = self._calculate_sequence_similarity(text, alias)

            if similarity >= threshold:
                merchant = self.merchants[merchant_id]
                matches.append(MerchantMatch(
                    merchant_id=merchant_id,
                    canonical_name=merchant.canonical_name,
                    aliases=merchant.aliases,
                    category=merchant.category,
                    subcategory=merchant.subcategory,
                    similarity_score=similarity,
                    match_type='alias'
                ))

        return matches

    def _trigram_match(self, text: str, threshold: float) -> List[MerchantMatch]:
        """Match using trigram similarity"""
        # Get trigrams from query
        query_trigrams = self._get_trigrams(text.upper())

        # Find candidate merchants
        candidate_merchants = set()
        for trigram in query_trigrams:
            if trigram in self.trigram_index:
                candidate_merchants.update(self.trigram_index[trigram])

        # Calculate similarity for each candidate
        matches = []
        for merchant_id in candidate_merchants:
            merchant = self.merchants[merchant_id]

            # Calculate max similarity against canonical name and aliases
            max_similarity = 0.0

            for name in [merchant.canonical_name] + merchant.aliases:
                similarity = self._calculate_trigram_similarity(text, name)
                max_similarity = max(max_similarity, similarity)

            if max_similarity >= threshold:
                matches.append(MerchantMatch(
                    merchant_id=merchant_id,
                    canonical_name=merchant.canonical_name,
                    aliases=merchant.aliases,
                    category=merchant.category,
                    subcategory=merchant.subcategory,
                    similarity_score=max_similarity,
                    match_type='trigram'
                ))

        return matches

    def _deduplicate_matches(self, matches: List[MerchantMatch]) -> List[MerchantMatch]:
        """Deduplicate matches, keeping highest score for each merchant"""
        best_matches: Dict[str, MerchantMatch] = {}

        for match in matches:
            if match.merchant_id not in best_matches:
                best_matches[match.merchant_id] = match
            else:
                # Keep match with higher score
                if match.similarity_score > best_matches[match.merchant_id].similarity_score:
                    best_matches[match.merchant_id] = match

        return list(best_matches.values())

    def search(self, query: str, limit: int = 10) -> List[MerchantMatch]:
        """
        Search merchants by query string

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching merchants
        """
        return self.resolve(query, threshold=0.5, top_k=limit)

    def get_merchant(self, merchant_id: str) -> Optional[MerchantInfo]:
        """Get merchant by ID"""
        return self.merchants.get(merchant_id)

    def get_all_merchants(self) -> List[MerchantInfo]:
        """Get all merchants"""
        return list(self.merchants.values())

    def add_merchant(
        self,
        merchant_id: str,
        canonical_name: str,
        aliases: List[str],
        category: str,
        subcategory: Optional[str] = None
    ):
        """Add a new merchant to the resolver"""
        canonical_name = canonical_name.upper()
        aliases = [a.upper() for a in aliases]

        merchant_info = MerchantInfo(
            merchant_id=merchant_id,
            canonical_name=canonical_name,
            aliases=aliases,
            category=category,
            subcategory=subcategory
        )

        self.merchants[merchant_id] = merchant_info

        # Update indexes
        self.alias_to_merchant[canonical_name] = merchant_id
        for alias in aliases:
            self.alias_to_merchant[alias] = merchant_id

        self._index_trigrams(canonical_name, merchant_id)
        for alias in aliases:
            self._index_trigrams(alias, merchant_id)
