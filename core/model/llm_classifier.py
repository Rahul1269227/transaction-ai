"""
LLM-based Transaction Classifier
Uses local LLM (via Ollama) for transaction categorization
"""

import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMClassifier:
    """
    LLM-based transaction classifier using Ollama

    Uses a local LLM (Llama 3.1 8B) for:
    1. Zero-shot categorization
    2. Few-shot learning with examples
    3. Reasoning about ambiguous transactions
    """

    def __init__(
        self,
        ollama_url: str = "http://llm-service:11434",
        model_name: str = "llama3.1:8b",
        taxonomy_path: Optional[str] = None,
        few_shot_examples: Optional[List[Dict]] = None
    ):
        """
        Initialize LLM classifier

        Args:
            ollama_url: Ollama API endpoint
            model_name: LLM model name
            taxonomy_path: Path to taxonomy YAML
            few_shot_examples: Examples for few-shot learning
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.taxonomy_path = taxonomy_path
        self.few_shot_examples = few_shot_examples or []
        self.categories = []

        # Load taxonomy if provided
        if taxonomy_path:
            self._load_taxonomy()

    def _load_taxonomy(self):
        """Load category taxonomy"""
        import yaml
        try:
            with open(self.taxonomy_path, 'r') as f:
                taxonomy = yaml.safe_load(f)
                self.categories = [cat['name'] for cat in taxonomy.get('categories', [])]
                logger.info(f"Loaded {len(self.categories)} categories from taxonomy")
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            # Default categories
            self.categories = [
                "Food & Dining", "Groceries", "Shopping", "Transport",
                "Fuel", "Health", "Entertainment", "Travel", "Utilities",
                "Bills", "Rent", "Education", "Investments", "ATM/Cash",
                "Transfers/UPI", "Fees & Charges", "Income/Salary", "Other"
            ]

    def _build_prompt(self, transaction_text: str, amount: Optional[float] = None) -> str:
        """
        Build LLM prompt for categorization

        Args:
            transaction_text: Transaction description
            amount: Transaction amount

        Returns:
            Formatted prompt string
        """
        categories_str = ", ".join(self.categories)

        prompt = f"""You are a financial transaction categorization expert. Your task is to categorize bank transactions into predefined categories.

Available Categories:
{categories_str}

Instructions:
1. Analyze the transaction description and amount
2. Choose the MOST appropriate category from the list above
3. Provide a confidence score (0.0 to 1.0)
4. Explain your reasoning briefly

Response Format (JSON only, no extra text):
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}

"""

        # Add few-shot examples if available
        if self.few_shot_examples:
            prompt += "\nExamples:\n"
            for ex in self.few_shot_examples[:5]:  # Use up to 5 examples
                prompt += f"\nTransaction: {ex['text']}"
                if ex.get('amount'):
                    prompt += f" | Amount: ₹{ex['amount']}"
                prompt += f"\nCategory: {ex['category']}\n"

        # Add the transaction to categorize
        prompt += f"\nNow categorize this transaction:\n"
        prompt += f"Transaction: {transaction_text}"
        if amount:
            prompt += f" | Amount: ₹{amount}"
        prompt += "\n\nYour response (JSON only):"

        return prompt

    def predict_single(
        self,
        text: str,
        amount: Optional[float] = None,
        timeout: int = 60
    ) -> Tuple[str, float, str]:
        """
        Predict category for a single transaction using LLM

        Args:
            text: Transaction text
            amount: Transaction amount
            timeout: Request timeout in seconds

        Returns:
            Tuple of (category, confidence, reasoning)
        """
        try:
            # Build prompt
            prompt = self._build_prompt(text, amount)

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "top_p": 0.9,
                        "num_predict": 200
                    }
                },
                timeout=timeout
            )

            if response.status_code != 200:
                logger.error(f"LLM API error: {response.status_code}")
                return "Other", 0.5, "LLM API error"

            # Parse response
            result = response.json()
            llm_output = result.get('response', '').strip()

            # Extract JSON from response
            try:
                # Try to find JSON in the response
                json_start = llm_output.find('{')
                json_end = llm_output.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_output[json_start:json_end]
                    parsed = json.loads(json_str)

                    category = parsed.get('category', 'Other')
                    confidence = float(parsed.get('confidence', 0.5))
                    reasoning = parsed.get('reasoning', 'No reasoning provided')

                    # Validate category
                    if category not in self.categories:
                        # Try to find closest match
                        category = self._find_closest_category(category)

                    return category, confidence, reasoning
                else:
                    logger.warning(f"No JSON found in LLM response: {llm_output}")
                    return "Other", 0.5, "Failed to parse LLM response"

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}, response: {llm_output}")
                return "Other", 0.5, "Invalid JSON from LLM"

        except requests.exceptions.Timeout:
            logger.error("LLM request timeout")
            return "Other", 0.3, "LLM timeout"
        except Exception as e:
            logger.error(f"LLM prediction error: {e}")
            return "Other", 0.3, f"Error: {str(e)}"

    def _find_closest_category(self, category: str) -> str:
        """Find closest matching category from taxonomy"""
        category_lower = category.lower()
        for valid_cat in self.categories:
            if valid_cat.lower() in category_lower or category_lower in valid_cat.lower():
                return valid_cat
        return "Other"

    def predict(
        self,
        texts: List[str],
        amounts: Optional[List[float]] = None,
        batch_size: int = 1
    ) -> List[Tuple[str, float, str]]:
        """
        Predict categories for multiple transactions

        Args:
            texts: List of transaction texts
            amounts: List of amounts
            batch_size: Currently only supports 1 (sequential processing)

        Returns:
            List of (category, confidence, reasoning) tuples
        """
        if amounts is None:
            amounts = [None] * len(texts)

        results = []
        for text, amount in zip(texts, amounts):
            result = self.predict_single(text, amount)
            results.append(result)

        return results

    def check_health(self) -> bool:
        """Check if LLM service is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def load_few_shot_examples(self, examples_path: str):
        """
        Load few-shot examples from JSONL file

        Args:
            examples_path: Path to JSONL file with examples
        """
        try:
            examples = []
            with open(examples_path, 'r') as f:
                for line in f:
                    examples.append(json.loads(line.strip()))

            # Sample diverse examples across categories
            from collections import defaultdict
            by_category = defaultdict(list)
            for ex in examples:
                by_category[ex['category']].append(ex)

            # Take 1-2 examples per category, up to 20 total
            sampled = []
            for category, cat_examples in by_category.items():
                sampled.extend(cat_examples[:2])
                if len(sampled) >= 20:
                    break

            self.few_shot_examples = sampled[:20]
            logger.info(f"Loaded {len(self.few_shot_examples)} few-shot examples")

        except Exception as e:
            logger.error(f"Failed to load few-shot examples: {e}")


# Factory function for easy initialization
def create_llm_classifier(
    ollama_url: str = "http://llm-service:11434",
    model_name: str = "llama3.1:8b",
    taxonomy_path: Optional[str] = None,
    examples_path: Optional[str] = None
) -> Optional[LLMClassifier]:
    """
    Create and initialize LLM classifier

    Args:
        ollama_url: Ollama service URL
        model_name: LLM model name
        taxonomy_path: Path to taxonomy file
        examples_path: Path to few-shot examples

    Returns:
        LLMClassifier instance or None if initialization fails
    """
    try:
        classifier = LLMClassifier(
            ollama_url=ollama_url,
            model_name=model_name,
            taxonomy_path=taxonomy_path
        )

        # Load few-shot examples if provided
        if examples_path:
            classifier.load_few_shot_examples(examples_path)

        # Check health
        if not classifier.check_health():
            logger.warning("LLM service not available, classifier may not work")

        return classifier
    except Exception as e:
        logger.error(f"Failed to create LLM classifier: {e}")
        return None
