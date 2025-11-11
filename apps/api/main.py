"""
Transaction Categorization API
FastAPI application for transaction categorization service
"""

import os
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import (
    TransactionInput,
    TransactionBatchInput,
    TransactionOutput,
    TransactionBatchOutput,
    MerchantQuery,
    MerchantMatchResult,
    MerchantMatch as MerchantMatchModel,
    FeedbackInput,
    FeedbackResponse,
    TrainingRequest,
    TrainingResponse,
    HealthResponse,
    ErrorResponse,
    NormalizedTransaction,
    CategoryResult
)
from core.model import HybridRouter
from core.resolve import MerchantResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Transaction AI Categorization API",
    description="AI-powered transaction categorization system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
router: Optional[HybridRouter] = None
merchant_resolver: Optional[MerchantResolver] = None

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
TAXONOMY_PATH = BASE_DIR / "data" / "taxonomy.yaml"
GAZETTEER_PATH = BASE_DIR / "data" / "gazetteer" / "merchant_aliases.csv"
MODEL_PATH = BASE_DIR / "models" / "classifier"


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global router, merchant_resolver

    logger.info("Starting Transaction Categorization API...")

    try:
        # Initialize router
        router = HybridRouter(
            taxonomy_path=str(TAXONOMY_PATH) if TAXONOMY_PATH.exists() else None,
            gazetteer_path=str(GAZETTEER_PATH) if GAZETTEER_PATH.exists() else None,
            model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None,
            auto_accept_threshold=0.85,
            review_threshold=0.60
        )
        logger.info("Hybrid router initialized")

        # Initialize standalone merchant resolver for /merchants endpoint
        if GAZETTEER_PATH.exists():
            merchant_resolver = MerchantResolver(str(GAZETTEER_PATH))
            logger.info("Merchant resolver initialized")

        logger.info("API startup complete")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Transaction Categorization API...")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Transaction AI Categorization API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    components = {
        "normalizer": "healthy",
        "rule_categorizer": "healthy" if router and router.rule_categorizer else "unavailable",
        "ml_classifier": "healthy" if router and router.ml_classifier else "unavailable",
        "merchant_resolver": "healthy" if router and router.merchant_resolver else "unavailable",
    }

    all_healthy = all(status == "healthy" for status in components.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        components=components
    )


@app.post("/categorize", response_model=TransactionOutput, tags=["Categorization"])
async def categorize_transaction(transaction: TransactionInput):
    """
    Categorize a single transaction

    Args:
        transaction: Transaction input with text, amount, date

    Returns:
        TransactionOutput with category, confidence, and explanations
    """
    if not router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Categorize
        result = router.categorize(
            text=transaction.text,
            amount=transaction.amount,
            date=transaction.date,
            currency=transaction.currency
        )

        # Normalize for response
        normalized_result = router.normalizer.normalize(
            text=transaction.text,
            amount=transaction.amount,
            date=transaction.date,
            currency=transaction.currency
        )

        # Build response
        return TransactionOutput(
            original_text=transaction.text,
            normalized=NormalizedTransaction(**normalized_result['normalized']),
            category=result.category,
            subcategory=result.subcategory,
            confidence=result.confidence,
            explanations=result.explanations,
            method=result.method,
            alternatives=[
                CategoryResult(
                    category=alt[0],
                    subcategory=None,
                    confidence=alt[1],
                    explanations=[],
                    method=result.method
                )
                for alt in (result.alternatives or [])
            ] if result.alternatives else None,
            requires_review=result.requires_review
        )

    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")


@app.post("/categorize/batch", response_model=TransactionBatchOutput, tags=["Categorization"])
async def categorize_batch(batch: TransactionBatchInput):
    """
    Categorize a batch of transactions

    Args:
        batch: Batch of transactions

    Returns:
        TransactionBatchOutput with results and statistics
    """
    if not router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Convert to dict format
        transactions_dict = [
            {
                'text': txn.text,
                'amount': txn.amount,
                'date': txn.date,
                'currency': txn.currency
            }
            for txn in batch.transactions
        ]

        # Categorize batch
        results = router.categorize_batch(transactions_dict)

        # Build response
        outputs = []
        for txn, result in zip(batch.transactions, results):
            normalized_result = router.normalizer.normalize(
                text=txn.text,
                amount=txn.amount,
                date=txn.date,
                currency=txn.currency
            )

            outputs.append(TransactionOutput(
                original_text=txn.text,
                normalized=NormalizedTransaction(**normalized_result['normalized']),
                category=result.category,
                subcategory=result.subcategory,
                confidence=result.confidence,
                explanations=result.explanations,
                method=result.method,
                requires_review=result.requires_review
            ))

        # Calculate stats
        stats = router.get_stats(results)

        return TransactionBatchOutput(
            results=outputs,
            stats=stats
        )

    except Exception as e:
        logger.error(f"Error categorizing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Batch categorization failed: {str(e)}")


@app.post("/merchants", response_model=MerchantMatchResult, tags=["Merchants"])
async def search_merchants(query: MerchantQuery):
    """
    Search for merchants by name

    Args:
        query: Merchant search query

    Returns:
        List of matching merchants with similarity scores
    """
    if not merchant_resolver:
        raise HTTPException(status_code=503, detail="Merchant resolver not available")

    try:
        matches = merchant_resolver.search(query.query, limit=query.limit)

        # Convert to response model
        match_models = [
            MerchantMatchModel(
                merchant_id=m.merchant_id,
                canonical_name=m.canonical_name,
                aliases=m.aliases,
                category=m.category,
                subcategory=m.subcategory,
                similarity_score=m.similarity_score
            )
            for m in matches
        ]

        return MerchantMatchResult(
            query=query.query,
            matches=match_models
        )

    except Exception as e:
        logger.error(f"Error searching merchants: {e}")
        raise HTTPException(status_code=500, detail=f"Merchant search failed: {str(e)}")


@app.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(feedback: FeedbackInput):
    """
    Submit feedback on categorization

    Args:
        feedback: User feedback with correct category

    Returns:
        FeedbackResponse with status
    """
    try:
        # TODO: Store feedback in database for retraining
        # For now, just log it
        logger.info(f"Feedback received: {feedback.transaction_text} -> {feedback.correct_category}")

        # Save to file (simple implementation)
        feedback_dir = BASE_DIR / "data" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        feedback_file = feedback_dir / f"feedback_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        import json
        with open(feedback_file, 'a') as f:
            f.write(json.dumps(feedback.dict()) + '\n')

        return FeedbackResponse(
            status="success",
            message="Feedback received and saved",
            feedback_id=None  # Could generate UUID
        )

    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@app.post("/train", response_model=TrainingResponse, tags=["Training"])
async def trigger_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger model training (background task)

    Args:
        request: Training request with dataset path and parameters

    Returns:
        TrainingResponse with job ID
    """
    try:
        # TODO: Implement actual training pipeline
        # For now, return placeholder

        logger.info(f"Training request received: {request.dataset_path}")

        # Add background task
        # background_tasks.add_task(train_model, request)

        return TrainingResponse(
            status="queued",
            message="Training job queued",
            job_id="placeholder-job-id",
            model_path=None,
            metrics=None
        )

    except Exception as e:
        logger.error(f"Error triggering training: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            details=None
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)}
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
