"""
LLM-based Transaction Classifier
Uses local LLM (via Ollama) for transaction categorization
"""

import hashlib
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import requests
from datetime import datetime
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import time

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
        self._service_unavailable = False  # Track if service is down
        self._error_logged = False  # Only log error once

        # In-memory cache for LLM responses
        self._response_cache: Dict[str, Tuple[str, float, str]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

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

CRITICAL RULES FOR CATEGORIZATION:

1. **Payment Direction Understanding**:
   - "TO <merchant>" or "PAID TO <merchant>" = PURCHASE transaction
   - "FROM <merchant>" = REFUND or INCOME
   - Wallet payments TO merchants = PURCHASES in the merchant's category

2. **Category Distinctions**:
   - **Shopping**: E-commerce platforms (Amazon, Flipkart, Myntra, Cloudtail), retail stores, online marketplaces
   - **Bills**: Recurring utility payments (electricity, water, phone, internet), EMI, credit card bills
   - **Fees & Charges**: Bank charges, penalties, service fees (NOT merchant payments)
   - **Transfers/UPI**: Person-to-person transfers, account transfers (NOT merchant payments)

3. **Merchant Recognition**:
   - E-commerce sellers (like Cloudtail, Appario, RetailNet) → Shopping
   - Payment wallets (PayTM, PhonePe, GPay) used TO pay merchants → Use merchant's category
   - Unknown merchants with "TO <name>" pattern → Likely Shopping or Services

4. **Context Clues**:
   - Transaction IDs, reference numbers → Not fees
   - "Subscription", "monthly", "plan" → Bills or Entertainment
   - Specific merchant names → Research semantic meaning

Instructions:
1. Analyze the transaction text for payment direction (TO/FROM)
2. Identify any merchant names mentioned
3. Understand the transaction's PURPOSE, not just keywords
4. Choose the MOST appropriate category based on semantic meaning
5. Provide a confidence score (0.0 to 1.0)
6. Explain your reasoning clearly

Response Format (JSON only, no extra text):
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "brief explanation of why this category fits"
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

    def _get_cache_key(self, text: str, amount: Optional[float] = None) -> str:
        """Generate cache key for transaction"""
        cache_input = f"{text.lower().strip()}|{amount if amount else ''}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    async def predict_single_async(
        self,
        text: str,
        amount: Optional[float] = None,
        timeout: int = 120,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Tuple[str, float, str]:
        """
        Async predict category for a single transaction using LLM

        Args:
            text: Transaction text
            amount: Transaction amount
            timeout: Request timeout in seconds (increased to 120s)
            session: Optional aiohttp session for connection pooling

        Returns:
            Tuple of (category, confidence, reasoning)
        """
        # Check cache first
        cache_key = self._get_cache_key(text, amount)
        if cache_key in self._response_cache:
            self._cache_hits += 1
            logger.debug(f"LLM cache hit for: {text[:50]}... (hits: {self._cache_hits}/{self._cache_hits + self._cache_misses})")
            return self._response_cache[cache_key]

        self._cache_misses += 1

        # Create session if not provided
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            # Build prompt
            prompt = self._build_prompt(text, amount)

            # Call Ollama API with async
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.05,
                        "top_p": 0.8,
                        "num_predict": 80,
                        "num_thread": 4  # Parallelize within model inference
                    }
                },
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    logger.error(f"LLM API error: {response.status}")
                    return "Other", 0.5, "LLM API error"

                # Parse response
                result = await response.json()
                llm_output = result.get('response', '').strip()

                # Extract JSON from response
                try:
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
                            category = self._find_closest_category(category)

                        # Cache the successful response
                        result_tuple = (category, confidence, reasoning)
                        self._response_cache[cache_key] = result_tuple
                        logger.debug(f"LLM cache stored for: {text[:50]}...")

                        return result_tuple
                    else:
                        logger.warning(f"No JSON found in LLM response: {llm_output}")
                        return "Other", 0.5, "Failed to parse LLM response"

                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}, response: {llm_output}")
                    return "Other", 0.5, "Invalid JSON from LLM"

        except asyncio.TimeoutError:
            if not self._error_logged:
                logger.warning(f"LLM request timeout ({timeout}s) - may be slow or overloaded")
                self._error_logged = True
            return None, 0.0, "LLM timeout"
        except aiohttp.ClientConnectorError as e:
            if not self._service_unavailable:
                self._service_unavailable = True
                logger.warning(f"LLM service unavailable at {self.ollama_url} - will gracefully degrade to rules+ML only")
            return None, 0.0, "LLM unavailable"
        except Exception as e:
            if not self._error_logged:
                logger.warning(f"LLM prediction error: {e} - will gracefully degrade")
                self._error_logged = True
            return None, 0.0, f"Error: {str(e)}"
        finally:
            if close_session:
                await session.close()

    def predict_single(
        self,
        text: str,
        amount: Optional[float] = None,
        timeout: int = 120
    ) -> Tuple[str, float, str]:
        """
        Predict category for a single transaction using LLM (synchronous wrapper)

        Args:
            text: Transaction text
            amount: Transaction amount
            timeout: Request timeout in seconds (increased to 120s)

        Returns:
            Tuple of (category, confidence, reasoning)
        """
        # Check cache first
        cache_key = self._get_cache_key(text, amount)
        if cache_key in self._response_cache:
            self._cache_hits += 1
            logger.debug(f"LLM cache hit for: {text[:50]}... (hits: {self._cache_hits}/{self._cache_hits + self._cache_misses})")
            return self._response_cache[cache_key]

        self._cache_misses += 1

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
                        "temperature": 0.05,  # Very low temperature for maximum consistency
                        "top_p": 0.8,  # Lower for more focused responses
                        "num_predict": 80  # Reduced from 150 to 80 for faster inference
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

                    # Cache the successful response
                    result = (category, confidence, reasoning)
                    self._response_cache[cache_key] = result
                    logger.debug(f"LLM cache stored for: {text[:50]}...")

                    return result
                else:
                    logger.warning(f"No JSON found in LLM response: {llm_output}")
                    return "Other", 0.5, "Failed to parse LLM response"

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}, response: {llm_output}")
                return "Other", 0.5, "Invalid JSON from LLM"

        except requests.exceptions.ConnectionError as e:
            # LLM service not available - only log once
            if not self._service_unavailable:
                self._service_unavailable = True
                logger.warning(f"LLM service unavailable at {self.ollama_url} - will gracefully degrade to rules+ML only")
            return None, 0.0, "LLM unavailable"
        except requests.exceptions.Timeout:
            if not self._error_logged:
                logger.warning("LLM request timeout - may be slow or overloaded")
                self._error_logged = True
            return None, 0.0, "LLM timeout"
        except Exception as e:
            if not self._error_logged:
                logger.warning(f"LLM prediction error: {e} - will gracefully degrade")
                self._error_logged = True
            return None, 0.0, f"Error: {str(e)}"

    def _find_closest_category(self, category: str) -> str:
        """Find closest matching category from taxonomy"""
        category_lower = category.lower()
        for valid_cat in self.categories:
            if valid_cat.lower() in category_lower or category_lower in valid_cat.lower():
                return valid_cat
        return "Other"

    async def predict_batch_async(
        self,
        texts: List[str],
        amounts: Optional[List[float]] = None,
        max_concurrent: int = 4,
        timeout: int = 120
    ) -> List[Tuple[str, float, str]]:
        """
        Predict categories for multiple transactions in parallel using async

        Args:
            texts: List of transaction texts
            amounts: List of amounts
            max_concurrent: Maximum number of concurrent LLM requests (default: 4)
            timeout: Timeout per request in seconds

        Returns:
            List of (category, confidence, reasoning) tuples
        """
        if amounts is None:
            amounts = [None] * len(texts)

        # Create shared session for connection pooling
        async with aiohttp.ClientSession() as session:
            # Create tasks with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)

            async def predict_with_semaphore(text, amount):
                async with semaphore:
                    return await self.predict_single_async(text, amount, timeout, session)

            # Run all predictions in parallel (limited by semaphore)
            tasks = [predict_with_semaphore(text, amount) for text, amount in zip(texts, amounts)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch prediction error for text {i}: {result}")
                    processed_results.append(("Other", 0.5, f"Error: {str(result)}"))
                else:
                    processed_results.append(result)

            return processed_results

    def predict(
        self,
        texts: List[str],
        amounts: Optional[List[float]] = None,
        batch_size: int = 4
    ) -> List[Tuple[str, float, str]]:
        """
        Predict categories for multiple transactions with parallel processing

        Args:
            texts: List of transaction texts
            amounts: List of amounts
            batch_size: Maximum number of concurrent LLM requests (default: 4)

        Returns:
            List of (category, confidence, reasoning) tuples
        """
        if amounts is None:
            amounts = [None] * len(texts)

        # Use asyncio to run parallel predictions
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If loop is already running (e.g., in async context), use run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.predict_batch_async(texts, amounts, max_concurrent=batch_size)
                )
                return future.result()
        else:
            # Run async batch prediction
            return loop.run_until_complete(
                self.predict_batch_async(texts, amounts, max_concurrent=batch_size)
            )

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
