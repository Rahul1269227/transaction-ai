#!/usr/bin/env python3
"""
Label real Kaggle transaction data using rule-based + LLM classification
"""

import pandas as pd
import yaml
import re
from pathlib import Path
from tqdm import tqdm
import os

# Try to initialize OpenAI client
try:
    from openai import OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = None
except ImportError:
    client = None

def load_taxonomy():
    """Load the taxonomy from YAML file"""
    taxonomy_path = Path(__file__).parent.parent / 'data' / 'taxonomy.yaml'
    with open(taxonomy_path, 'r') as f:
        return yaml.safe_load(f)

def rule_based_classify(transaction_text, taxonomy):
    """
    Use rule-based classification first (fast and accurate for clear cases)
    """
    transaction_lower = transaction_text.lower()

    best_match = None
    best_score = 0

    for category in taxonomy['categories']:
        score = 0

        # Check keywords
        for keyword in category['keywords']:
            if keyword.lower() in transaction_lower:
                score += 2

        # Check patterns (simplified - just check keywords in patterns)
        for pattern in category['patterns']:
            # Extract keywords from simple patterns
            if '(?i)' in pattern:
                pattern_keywords = pattern.replace('(?i)', '').replace('.*', '').replace('\\', '').strip('()')
                if pattern_keywords and pattern_keywords in transaction_lower:
                    score += 1

        if score > best_score:
            best_score = score
            best_match = category['name']

    # Return confidence based on score
    if best_score >= 2:
        return best_match, min(best_score / 5.0, 0.95)
    elif best_score > 0:
        return best_match, best_score / 5.0
    else:
        return None, 0.0

def llm_classify(transaction_text, taxonomy, rule_based_category=None):
    """
    Use LLM for difficult or ambiguous cases
    """
    if client is None:
        return None, 0.0

    # Build category list for LLM
    category_list = []
    for cat in taxonomy['categories']:
        category_list.append(f"- {cat['name']}: {cat['description']}")

    categories_str = "\n".join(category_list)

    prompt = f"""Classify the following bank transaction into one of these categories:

{categories_str}

Transaction: "{transaction_text}"

{"Rule-based system suggested: " + rule_based_category if rule_based_category else ""}

Respond with ONLY the category name, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a transaction categorization expert. Respond with only the category name."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )

        predicted_category = response.choices[0].message.content.strip()

        # Validate that it's a real category
        valid_categories = [cat['name'] for cat in taxonomy['categories']]
        if predicted_category in valid_categories:
            return predicted_category, 0.80
        else:
            # Try to find closest match
            for cat_name in valid_categories:
                if cat_name.lower() in predicted_category.lower():
                    return cat_name, 0.75
            return "Other", 0.50

    except Exception as e:
        print(f"LLM error: {e}")
        return "Other", 0.30

def classify_transaction(transaction_text, taxonomy, use_llm=True):
    """
    Classify transaction using hybrid approach
    """
    # First try rule-based
    rule_category, rule_confidence = rule_based_classify(transaction_text, taxonomy)

    # If high confidence, return immediately
    if rule_confidence >= 0.80:
        return rule_category, rule_confidence, "rule_based"

    # If medium confidence and we're using LLM, validate with LLM
    if use_llm and rule_confidence >= 0.30:
        llm_category, llm_confidence = llm_classify(transaction_text, taxonomy, rule_category)
        # If LLM agrees or has different opinion with high confidence, use it
        if llm_category == rule_category:
            return llm_category, min(0.90, rule_confidence + llm_confidence), "hybrid"
        else:
            return llm_category, llm_confidence, "llm"

    # Low confidence from rules, use LLM if available
    if use_llm:
        llm_category, llm_confidence = llm_classify(transaction_text, taxonomy)
        return llm_category, llm_confidence, "llm"

    # Fallback to rule-based even if low confidence
    if rule_category:
        return rule_category, rule_confidence, "rule_based"

    return "Other", 0.30, "fallback"

def main():
    print("Loading real transaction data...")

    # Load data
    df = pd.read_csv('data/raw/bank_transactions.csv')
    print(f"Loaded {len(df)} transactions")

    # Load taxonomy
    taxonomy = load_taxonomy()
    print(f"Loaded taxonomy with {len(taxonomy['categories'])} categories")

    # Ask user about LLM usage
    use_llm = client is not None

    if use_llm:
        print("\n✓ OpenAI API key found - will use LLM for ambiguous cases")
        print("This will be more accurate but slower and will incur API costs.")
    else:
        print("\n⚠ No OpenAI API key found - using only rule-based classification")
        print("Set OPENAI_API_KEY environment variable to use LLM enhancement.")

    # Sample for testing - you can remove this to process all
    print("\nProcessing transactions...")

    # Get unique transaction descriptions for efficiency
    unique_transactions = df['TRANSACTION DETAILS'].value_counts()
    print(f"Found {len(unique_transactions)} unique transaction patterns")

    # Create mapping
    transaction_mapping = {}

    for trans_text in tqdm(unique_transactions.index[:5000], desc="Classifying"):  # Process top 5000 patterns
        category, confidence, method = classify_transaction(trans_text, taxonomy, use_llm)
        transaction_mapping[trans_text] = {
            'category': category,
            'confidence': confidence,
            'method': method
        }

    # Apply mapping to full dataset
    print("\nApplying labels to full dataset...")
    df['category'] = df['TRANSACTION DETAILS'].map(
        lambda x: transaction_mapping.get(x, {'category': 'Other'})['category']
    )
    df['confidence'] = df['TRANSACTION DETAILS'].map(
        lambda x: transaction_mapping.get(x, {'confidence': 0.5})['confidence']
    )
    df['classification_method'] = df['TRANSACTION DETAILS'].map(
        lambda x: transaction_mapping.get(x, {'method': 'fallback'})['method']
    )

    # Save labeled data
    output_path = 'data/labeled/real_transactions_labeled.csv'
    Path('data/labeled').mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"\n✓ Saved labeled data to {output_path}")
    print(f"\nCategory distribution:")
    print(df['category'].value_counts())
    print(f"\nAverage confidence: {df['confidence'].mean():.2f}")
    print(f"\nClassification method distribution:")
    print(df['classification_method'].value_counts())

    # Save summary statistics
    summary = {
        'total_transactions': len(df),
        'unique_patterns': len(unique_transactions),
        'category_distribution': df['category'].value_counts().to_dict(),
        'avg_confidence': float(df['confidence'].mean()),
        'method_distribution': df['classification_method'].value_counts().to_dict()
    }

    summary_path = 'data/labeled/labeling_summary.yaml'
    with open(summary_path, 'w') as f:
        yaml.dump(summary, f, default_flow_style=False)

    print(f"\n✓ Saved summary to {summary_path}")

if __name__ == '__main__':
    main()
