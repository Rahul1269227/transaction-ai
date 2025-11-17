"""
Explainability Module
Provides detailed explanations for transaction categorization decisions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExplanationComponent:
    """Single component of an explanation"""
    method: str  # 'rule', 'ml', 'llm', 'merchant'
    component_type: str  # 'keyword_match', 'pattern_match', 'embedding', 'reasoning', etc.
    description: str
    confidence: float
    details: Dict[str, Any]


@dataclass
class Explanation:
    """Complete explanation for a categorization"""
    transaction_id: Optional[int]
    final_category: str
    final_confidence: float
    method_used: str
    components: List[ExplanationComponent]
    ensemble_votes: Dict[str, Any]
    decision_path: List[str]  # Step-by-step decision process
    alternatives: List[Dict[str, float]]  # Alternative categories with scores


class ExplainabilityService:
    """Service for generating explanations"""
    
    def __init__(self):
        pass
    
    def explain_categorization(
        self,
        transaction_output: Dict[str, Any],
        transaction_id: Optional[int] = None
    ) -> Explanation:
        """
        Generate detailed explanation for a categorization
        
        Args:
            transaction_output: TransactionOutput dict from categorization
            transaction_id: Optional transaction ID
            
        Returns:
            Explanation object
        """
        components = []
        decision_path = []
        
        # Extract ensemble votes
        ensemble_votes = transaction_output.get('ensemble_votes', {})
        method = transaction_output.get('method', 'unknown')
        category = transaction_output.get('category', 'Unknown')
        confidence = transaction_output.get('confidence', 0.0)
        
        # Rule-based explanations
        if ensemble_votes.get('rule'):
            rule_vote = ensemble_votes['rule']
            components.append(ExplanationComponent(
                method='rule',
                component_type='rule_match',
                description=f"Rule-based categorizer matched '{rule_vote['category']}'",
                confidence=rule_vote.get('confidence', 0.0),
                details={
                    'category': rule_vote['category'],
                    'explanations': transaction_output.get('explanations', [])
                }
            ))
            decision_path.append(f"Rule engine: {rule_vote['category']} (confidence: {rule_vote.get('confidence', 0.0):.2f})")
        
        # ML explanations
        if ensemble_votes.get('ml'):
            ml_vote = ensemble_votes['ml']
            components.append(ExplanationComponent(
                method='ml',
                component_type='embedding_classification',
                description=f"ML embedding classifier predicted '{ml_vote['category']}'",
                confidence=ml_vote.get('confidence', 0.0),
                details={
                    'category': ml_vote['category'],
                    'model': 'LightGBM + Sentence Transformers',
                    'embedding_model': 'all-MiniLM-L6-v2'
                }
            ))
            decision_path.append(f"ML classifier: {ml_vote['category']} (confidence: {ml_vote.get('confidence', 0.0):.2f})")
        
        # LLM explanations
        if ensemble_votes.get('llm'):
            llm_vote = ensemble_votes['llm']
            # Extract reasoning from explanations if available
            reasoning = "LLM reasoning provided"
            for exp in transaction_output.get('explanations', []):
                if 'llm_reasoning' in exp.lower():
                    reasoning = exp.split(':', 1)[1] if ':' in exp else exp
            
            components.append(ExplanationComponent(
                method='llm',
                component_type='llm_reasoning',
                description=f"LLM analyzed transaction and reasoned: {reasoning}",
                confidence=llm_vote.get('confidence', 0.0),
                details={
                    'category': llm_vote['category'],
                    'reasoning': reasoning,
                    'model': 'Llama 3.1 8B'
                }
            ))
            decision_path.append(f"LLM reasoning: {llm_vote['category']} (confidence: {llm_vote.get('confidence', 0.0):.2f})")
        
        # Merchant match explanations
        if ensemble_votes.get('merchant'):
            merchant_vote = ensemble_votes['merchant']
            components.append(ExplanationComponent(
                method='merchant',
                component_type='merchant_gazetteer',
                description=f"Merchant matched in gazetteer: {merchant_vote.get('merchant', 'unknown')}",
                confidence=merchant_vote.get('confidence', 0.0),
                details={
                    'merchant': merchant_vote.get('merchant'),
                    'category': merchant_vote.get('category'),
                    'match_type': 'gazetteer'
                }
            ))
            decision_path.append(f"Merchant match: {merchant_vote.get('category', 'unknown')} (confidence: {merchant_vote.get('confidence', 0.0):.2f})")
        
        # Ensemble decision
        agreement_count = ensemble_votes.get('agreement_count', 0)
        total_methods = ensemble_votes.get('total_methods', 0)
        
        if agreement_count == total_methods and total_methods > 1:
            decision_path.append(f"✅ Unanimous agreement: All {total_methods} methods agreed on '{category}'")
        elif agreement_count > 1:
            decision_path.append(f"✅ Majority agreement: {agreement_count}/{total_methods} methods agreed on '{category}'")
        else:
            decision_path.append(f"⚠️ Single method decision: Only one method provided result")
        
        decision_path.append(f"Final decision: {category} (confidence: {confidence:.2f})")
        
        # Extract alternatives if available
        alternatives = []
        if transaction_output.get('alternatives'):
            alternatives = transaction_output['alternatives']
        
        return Explanation(
            transaction_id=transaction_id,
            final_category=category,
            final_confidence=confidence,
            method_used=method,
            components=components,
            ensemble_votes=ensemble_votes,
            decision_path=decision_path,
            alternatives=alternatives
        )
    
    def explain_to_dict(self, explanation: Explanation) -> Dict[str, Any]:
        """Convert Explanation to dict for JSON serialization"""
        return {
            'transaction_id': explanation.transaction_id,
            'final_category': explanation.final_category,
            'final_confidence': explanation.final_confidence,
            'method_used': explanation.method_used,
            'components': [asdict(comp) for comp in explanation.components],
            'ensemble_votes': explanation.ensemble_votes,
            'decision_path': explanation.decision_path,
            'alternatives': explanation.alternatives
        }


# Global instance
explainability_service = ExplainabilityService()
