"""
Active Learning Module
Implements uncertainty sampling to prioritize low-confidence predictions for human review
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class UncertainPrediction:
    """Represents a prediction that needs human review"""
    transaction_id: int
    transaction_text: str
    predicted_category: str
    confidence: float
    amount: Optional[float]
    date: Optional[str]
    method: str
    ensemble_votes: Dict
    uncertainty_score: float  # Higher = more uncertain
    created_at: datetime


class ActiveLearningService:
    """Service for active learning and uncertainty sampling"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
    
    def calculate_uncertainty_score(
        self,
        confidence: float,
        ensemble_votes: Dict,
        method: str
    ) -> float:
        """
        Calculate uncertainty score for a prediction
        
        Higher score = more uncertain = higher priority for review
        
        Args:
            confidence: Final confidence score
            ensemble_votes: Ensemble voting breakdown
            method: Method used
            
        Returns:
            Uncertainty score (0-1, higher = more uncertain)
        """
        # Base uncertainty from confidence (inverse)
        base_uncertainty = 1.0 - confidence
        
        # Agreement penalty (disagreement = more uncertain)
        agreement_count = ensemble_votes.get('agreement_count', 0)
        total_methods = ensemble_votes.get('total_methods', 1)
        agreement_ratio = agreement_count / total_methods if total_methods > 0 else 0
        
        # If methods disagree, increase uncertainty
        disagreement_penalty = (1.0 - agreement_ratio) * 0.3
        
        # Method-specific uncertainty
        method_uncertainty = 0.0
        if 'llm' in method.lower():
            # LLM-only decisions are less certain
            method_uncertainty = 0.1
        elif 'rule' in method.lower() and 'ml' not in method.lower():
            # Rule-only might miss edge cases
            method_uncertainty = 0.05
        
        # Combine uncertainties
        total_uncertainty = min(1.0, base_uncertainty + disagreement_penalty + method_uncertainty)
        
        return total_uncertainty
    
    def get_uncertain_predictions(
        self,
        limit: int = 50,
        min_uncertainty: float = 0.3,
        max_age_days: int = 7
    ) -> List[UncertainPrediction]:
        """
        Get predictions that need human review (uncertainty sampling)
        
        Args:
            limit: Maximum number of predictions to return
            min_uncertainty: Minimum uncertainty score to include
            max_age_days: Maximum age of predictions to consider
            
        Returns:
            List of uncertain predictions sorted by uncertainty (highest first)
        """
        if not self.db_session:
            logger.warning("No database session - cannot fetch uncertain predictions")
            return []
        
        try:
            from apps.api.main import TransactionRecordORM
            
            # Query transactions that require review or have low confidence
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            transactions = self.db_session.query(TransactionRecordORM).filter(
                TransactionRecordORM.requires_review == True,
                TransactionRecordORM.reviewed == False,
                TransactionRecordORM.created_at >= cutoff_date
            ).order_by(
                TransactionRecordORM.confidence.asc()  # Lowest confidence first
            ).limit(limit).all()
            
            uncertain_predictions = []
            
            for txn in transactions:
                # Calculate uncertainty score
                ensemble_votes = {}
                if txn.method:
                    # Try to reconstruct ensemble votes from method string
                    ensemble_votes = {
                        'agreement_count': 1 if 'unanimous' in txn.method else 0,
                        'total_methods': txn.method.count('+') + 1 if '+' in txn.method else 1
                    }
                
                uncertainty = self.calculate_uncertainty_score(
                    float(txn.confidence) if txn.confidence else 0.0,
                    ensemble_votes,
                    txn.method or 'unknown'
                )
                
                if uncertainty >= min_uncertainty:
                    uncertain_predictions.append(UncertainPrediction(
                        transaction_id=txn.id,
                        transaction_text=txn.original_text,
                        predicted_category=txn.category,
                        confidence=float(txn.confidence) if txn.confidence else 0.0,
                        amount=float(txn.amount) if txn.amount else None,
                        date=txn.date.isoformat() if txn.date else None,
                        method=txn.method or 'unknown',
                        ensemble_votes=ensemble_votes,
                        uncertainty_score=uncertainty,
                        created_at=txn.created_at
                    ))
            
            # Sort by uncertainty (highest first)
            uncertain_predictions.sort(key=lambda x: x.uncertainty_score, reverse=True)
            
            return uncertain_predictions[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching uncertain predictions: {e}")
            return []
    
    def prioritize_for_review(
        self,
        transaction_output: Dict[str, Any],
        transaction_id: Optional[int] = None
    ) -> Tuple[bool, float]:
        """
        Determine if a transaction should be prioritized for review
        
        Args:
            transaction_output: TransactionOutput dict
            transaction_id: Optional transaction ID
            
        Returns:
            (should_prioritize, uncertainty_score)
        """
        confidence = transaction_output.get('confidence', 0.0)
        ensemble_votes = transaction_output.get('ensemble_votes', {})
        method = transaction_output.get('method', 'unknown')
        
        uncertainty = self.calculate_uncertainty_score(confidence, ensemble_votes, method)
        
        # Prioritize if uncertainty > 0.3 or confidence < 0.6
        should_prioritize = uncertainty > 0.3 or confidence < 0.6
        
        return should_prioritize, uncertainty


# Global instance
active_learning_service: Optional[ActiveLearningService] = None


def init_active_learning(db_session: Optional[Session] = None):
    """Initialize active learning service"""
    global active_learning_service
    active_learning_service = ActiveLearningService(db_session)
    logger.info("Active learning service initialized")
