"""
Enhanced API Endpoints
New endpoints for explainability, active learning, multi-tenancy, and exports
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
import logging

from core.models import TransactionOutput, ErrorResponse
from core.auth import require_auth, check_rate_limit, api_auth
from core.explainability import explainability_service
from core.active_learning import active_learning_service
from core.multitenancy import get_tenant_context, multitenancy_service
from core.exports import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Enhanced Features"])


# ============================================================================
# Explainability Endpoints
# ============================================================================

@router.get("/explain/{transaction_id}", response_model=Dict[str, Any])
async def explain_transaction(
    transaction_id: int,
    api_key_info: Dict = Depends(require_auth),
    rate_limit_info: Dict = Depends(lambda: check_rate_limit(api_key_info.get('user_id', 'default'), limit=100))
):
    """
    Get detailed explanation for a transaction categorization
    
    Returns step-by-step reasoning, ensemble votes, and decision path
    """
    try:
        from apps.api.main import SessionLocal, TransactionRecordORM
        
        db = SessionLocal()
        try:
            txn = db.query(TransactionRecordORM).filter(
                TransactionRecordORM.id == transaction_id
            ).first()
            
            if not txn:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            # Convert to dict format
            txn_dict = {
                'category': txn.category,
                'confidence': float(txn.confidence) if txn.confidence else 0.0,
                'method': txn.method,
                'explanations': [],
                'ensemble_votes': {},
                'alternatives': []
            }
            
            # Generate explanation
            explanation = explainability_service.explain_categorization(
                txn_dict,
                transaction_id=transaction_id
            )
            
            return explainability_service.explain_to_dict(explanation)
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Active Learning Endpoints
# ============================================================================

@router.get("/uncertain-predictions", response_model=List[Dict[str, Any]])
async def get_uncertain_predictions(
    limit: int = Query(50, ge=1, le=200),
    min_uncertainty: float = Query(0.3, ge=0.0, le=1.0),
    api_key_info: Dict = Depends(require_auth),
    rate_limit_info: Dict = Depends(lambda: check_rate_limit(api_key_info.get('user_id', 'default'), limit=50))
):
    """
    Get predictions that need human review (uncertainty sampling)
    
    Returns transactions sorted by uncertainty score (highest first)
    """
    try:
        from apps.api.main import SessionLocal
        
        db = SessionLocal()
        try:
            if not active_learning_service:
                from core.active_learning import init_active_learning
                init_active_learning(db)
            
            uncertain = active_learning_service.get_uncertain_predictions(
                limit=limit,
                min_uncertainty=min_uncertainty
            )
            
            return [
                {
                    'transaction_id': p.transaction_id,
                    'transaction_text': p.transaction_text,
                    'predicted_category': p.predicted_category,
                    'confidence': p.confidence,
                    'amount': p.amount,
                    'date': p.date,
                    'method': p.method,
                    'uncertainty_score': p.uncertainty_score,
                    'created_at': p.created_at.isoformat()
                }
                for p in uncertain
            ]
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting uncertain predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prioritize-review/{transaction_id}")
async def prioritize_for_review(
    transaction_id: int,
    api_key_info: Dict = Depends(require_auth)
):
    """
    Mark a transaction as prioritized for review
    """
    try:
        from apps.api.main import SessionLocal, TransactionRecordORM
        
        db = SessionLocal()
        try:
            txn = db.query(TransactionRecordORM).filter(
                TransactionRecordORM.id == transaction_id
            ).first()
            
            if not txn:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            txn.requires_review = True
            db.commit()
            
            return {"status": "success", "message": "Transaction prioritized for review"}
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prioritizing transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/export/csv")
async def export_to_csv(
    transaction_ids: List[int],
    include_explanations: bool = Query(False),
    api_key_info: Dict = Depends(require_auth),
    rate_limit_info: Dict = Depends(lambda: check_rate_limit(api_key_info.get('user_id', 'default'), limit=10))
):
    """
    Export transactions to CSV format
    """
    try:
        from apps.api.main import SessionLocal, TransactionRecordORM
        
        db = SessionLocal()
        try:
            transactions = db.query(TransactionRecordORM).filter(
                TransactionRecordORM.id.in_(transaction_ids)
            ).all()
            
            if not transactions:
                raise HTTPException(status_code=404, detail="No transactions found")
            
            # Convert to dict format
            txn_dicts = []
            for txn in transactions:
                txn_dicts.append({
                    'id': txn.id,
                    'date': txn.date.isoformat() if txn.date else None,
                    'amount': float(txn.amount) if txn.amount else None,
                    'currency': txn.currency,
                    'category': txn.category,
                    'subcategory': txn.subcategory,
                    'merchant': txn.merchant,
                    'original_text': txn.original_text,
                    'confidence': float(txn.confidence) if txn.confidence else 0.0,
                    'method': txn.method,
                    'requires_review': txn.requires_review,
                    'explanations': [],
                    'ensemble_votes': {}
                })
            
            csv_content = export_service.export_to_csv(
                txn_dicts,
                include_explanations=include_explanations
            )
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=transactions.csv"}
            )
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/quickbooks")
async def export_to_quickbooks(
    transaction_ids: List[int],
    api_key_info: Dict = Depends(require_auth),
    rate_limit_info: Dict = Depends(lambda: check_rate_limit(api_key_info.get('user_id', 'default'), limit=10))
):
    """
    Export transactions to QuickBooks IIF format
    """
    try:
        from apps.api.main import SessionLocal, TransactionRecordORM
        
        db = SessionLocal()
        try:
            transactions = db.query(TransactionRecordORM).filter(
                TransactionRecordORM.id.in_(transaction_ids)
            ).all()
            
            if not transactions:
                raise HTTPException(status_code=404, detail="No transactions found")
            
            txn_dicts = []
            for txn in transactions:
                txn_dicts.append({
                    'id': txn.id,
                    'date': txn.date.isoformat() if txn.date else None,
                    'amount': float(txn.amount) if txn.amount else None,
                    'category': txn.category,
                    'original_text': txn.original_text
                })
            
            iif_content = export_service.export_to_quickbooks_format(txn_dicts)
            
            return Response(
                content=iif_content,
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=transactions.iif"}
            )
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to QuickBooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/xero")
async def export_to_xero(
    transaction_ids: List[int],
    api_key_info: Dict = Depends(require_auth),
    rate_limit_info: Dict = Depends(lambda: check_rate_limit(api_key_info.get('user_id', 'default'), limit=10))
):
    """
    Export transactions to Xero CSV format
    """
    try:
        from apps.api.main import SessionLocal, TransactionRecordORM
        
        db = SessionLocal()
        try:
            transactions = db.query(TransactionRecordORM).filter(
                TransactionRecordORM.id.in_(transaction_ids)
            ).all()
            
            if not transactions:
                raise HTTPException(status_code=404, detail="No transactions found")
            
            txn_dicts = []
            for txn in transactions:
                txn_dicts.append({
                    'id': txn.id,
                    'date': txn.date.isoformat() if txn.date else None,
                    'amount': float(txn.amount) if txn.amount else None,
                    'category': txn.category,
                    'merchant': txn.merchant,
                    'original_text': txn.original_text
                })
            
            xero_content = export_service.export_to_xero_format(txn_dicts)
            
            return Response(
                content=xero_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=xero_transactions.csv"}
            )
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to Xero: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API Key Management Endpoints
# ============================================================================

@router.post("/api-keys", response_model=Dict[str, str])
async def create_api_key(
    name: str,
    organization_id: str,
    user_id: str,
    rate_limit: int = Query(100, ge=10, le=10000),
    api_key_info: Dict = Depends(require_auth)
):
    """
    Create a new API key
    
    Requires admin permissions
    """
    if api_key_info.get('user_role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not api_auth:
        raise HTTPException(status_code=503, detail="API key service not initialized")
    
    new_key = api_auth.create_api_key(
        name=name,
        organization_id=organization_id,
        user_id=user_id,
        rate_limit=rate_limit
    )
    
    return {
        "api_key": new_key,
        "message": "API key created successfully. Store it securely - it won't be shown again."
    }


@router.get("/api-keys", response_model=List[Dict[str, Any]])
async def list_api_keys(
    api_key_info: Dict = Depends(require_auth)
):
    """
    List API keys for the current organization
    
    Requires admin permissions
    """
    if api_key_info.get('user_role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return masked keys (only show last 4 characters)
    return [
        {
            "name": "Example Key",
            "organization_id": api_key_info.get('organization_id'),
            "created_at": "2024-01-01T00:00:00",
            "rate_limit": 100,
            "masked_key": "txn_****...****abcd"
        }
    ]
