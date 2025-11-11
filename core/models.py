"""
Pydantic Models for Transaction Categorization
Defines request/response schemas and data models
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ChannelType(str, Enum):
    """Transaction channel types"""
    UPI = "UPI"
    IMPS = "IMPS"
    NEFT = "NEFT"
    RTGS = "RTGS"
    POS = "POS"
    CARD = "CARD"
    ATM = "ATM"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"


class TransactionInput(BaseModel):
    """Input transaction for categorization"""
    text: str = Field(..., description="Transaction description text")
    amount: Optional[float] = Field(None, description="Transaction amount")
    date: Optional[str] = Field(None, description="Transaction date (YYYY-MM-DD or other formats)")
    currency: str = Field(default="INR", description="Currency code")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "text": "UPI-1234567890-ZOMATO PAY*ABCD",
                "amount": 249.00,
                "date": "2025-11-10",
                "currency": "INR"
            }
        }


class TransactionBatchInput(BaseModel):
    """Batch of transactions for categorization"""
    transactions: List[TransactionInput] = Field(..., description="List of transactions")

    class Config:
        schema_extra = {
            "example": {
                "transactions": [
                    {
                        "text": "UPI-1234567890-ZOMATO PAY*ABCD",
                        "amount": 249.00,
                        "date": "2025-11-10"
                    },
                    {
                        "text": "POS 4532 HPCL KANPUR",
                        "amount": 1200.00,
                        "date": "2025-10-04"
                    }
                ]
            }
        }


class NormalizedTransaction(BaseModel):
    """Normalized transaction data"""
    amount: Optional[float] = None
    currency: str = "INR"
    date: Optional[str] = None
    merchant: Optional[str] = None
    channel: Optional[str] = None
    reference: Optional[str] = None
    location: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "amount": 249.00,
                "currency": "INR",
                "date": "2025-11-10",
                "merchant": "ZOMATO",
                "channel": "UPI",
                "reference": "1234567890"
            }
        }


class CategoryResult(BaseModel):
    """Categorization result with confidence"""
    category: str = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, description="Sub-category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    explanations: List[str] = Field(default=[], description="Explanation of categorization decision")
    method: str = Field(..., description="Method used: rule, embedding, hybrid, llm")

    class Config:
        schema_extra = {
            "example": {
                "category": "Food & Dining",
                "subcategory": "Food Delivery",
                "confidence": 0.92,
                "explanations": [
                    "merchant_alias=zomato",
                    "pattern=UPI:ZOMATO",
                    "emb_sim>0.7"
                ],
                "method": "hybrid"
            }
        }


class TransactionOutput(BaseModel):
    """Complete transaction categorization output"""
    original_text: str
    normalized: NormalizedTransaction
    category: str
    subcategory: Optional[str] = None
    confidence: float
    explanations: List[str] = []
    method: str
    alternatives: Optional[List[CategoryResult]] = Field(
        default=None,
        description="Alternative categorization options (for low confidence cases)"
    )
    requires_review: bool = Field(
        default=False,
        description="Whether this transaction requires human review"
    )

    class Config:
        schema_extra = {
            "example": {
                "original_text": "UPI-1234567890-ZOMATO PAY*ABCD",
                "normalized": {
                    "amount": 249.00,
                    "currency": "INR",
                    "date": "2025-11-10",
                    "merchant": "ZOMATO",
                    "channel": "UPI"
                },
                "category": "Food & Dining",
                "subcategory": "Food Delivery",
                "confidence": 0.92,
                "explanations": [
                    "merchant_alias=zomato",
                    "pattern=UPI:ZOMATO"
                ],
                "method": "hybrid",
                "requires_review": False
            }
        }


class TransactionBatchOutput(BaseModel):
    """Batch categorization output"""
    results: List[TransactionOutput]
    stats: Dict[str, Any] = Field(
        default={},
        description="Batch statistics (avg confidence, review count, etc.)"
    )

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "original_text": "UPI-ZOMATO",
                        "category": "Food & Dining",
                        "confidence": 0.92
                    }
                ],
                "stats": {
                    "total": 10,
                    "avg_confidence": 0.87,
                    "requires_review": 2,
                    "by_category": {
                        "Food & Dining": 3,
                        "Transport": 2
                    }
                }
            }
        }


class MerchantQuery(BaseModel):
    """Query for merchant lookup"""
    query: str = Field(..., description="Merchant name or partial text to search")
    limit: int = Field(default=10, ge=1, le=50, description="Number of results to return")

    class Config:
        schema_extra = {
            "example": {
                "query": "zomato",
                "limit": 5
            }
        }


class MerchantMatch(BaseModel):
    """Merchant match result"""
    merchant_id: str
    canonical_name: str
    aliases: List[str]
    category: str
    subcategory: Optional[str]
    similarity_score: float = Field(..., ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "merchant_id": "1",
                "canonical_name": "ZOMATO",
                "aliases": ["zomato", "zmt", "zomt", "zomato pay"],
                "category": "food_dining",
                "subcategory": "Food Delivery",
                "similarity_score": 0.95
            }
        }


class MerchantMatchResult(BaseModel):
    """Merchant matching results"""
    query: str
    matches: List[MerchantMatch]


class FeedbackInput(BaseModel):
    """User feedback on categorization"""
    transaction_text: str
    predicted_category: str
    correct_category: str
    predicted_subcategory: Optional[str] = None
    correct_subcategory: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "transaction_text": "UPI-ZOMATO",
                "predicted_category": "Shopping",
                "correct_category": "Food & Dining",
                "correct_subcategory": "Food Delivery",
                "amount": 249.00,
                "notes": "This should be food delivery"
            }
        }


class FeedbackResponse(BaseModel):
    """Response to feedback submission"""
    status: str = Field(..., description="success or error")
    message: str
    feedback_id: Optional[str] = None


class TrainingRequest(BaseModel):
    """Request to trigger model training"""
    dataset_path: Optional[str] = Field(None, description="Path to training dataset")
    model_name: Optional[str] = Field(None, description="Name for the trained model")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Training parameters")


class TrainingResponse(BaseModel):
    """Response from training request"""
    status: str
    message: str
    job_id: Optional[str] = None
    model_path: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy or unhealthy")
    version: str
    timestamp: str
    components: Dict[str, str] = Field(
        default={},
        description="Status of individual components"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-11T10:00:00Z",
                "components": {
                    "normalizer": "healthy",
                    "classifier": "healthy",
                    "merchant_resolver": "healthy"
                }
            }
        }


# Database models (for storage)
class TransactionRecord(BaseModel):
    """Transaction record for database storage"""
    id: Optional[str] = None
    original_text: str
    amount: Optional[float] = None
    currency: str = "INR"
    date: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    confidence: float
    method: str
    merchant: Optional[str] = None
    channel: Optional[str] = None
    reference: Optional[str] = None
    requires_review: bool = False
    reviewed: bool = False
    correct_category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MerchantRecord(BaseModel):
    """Merchant record for database storage"""
    merchant_id: str
    canonical_name: str
    aliases: List[str]
    category: str
    subcategory: Optional[str] = None
    embedding: Optional[List[float]] = None
    transaction_count: int = 0
    confidence_avg: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Error responses
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid transaction format",
                "details": {
                    "field": "amount",
                    "issue": "must be a positive number"
                }
            }
        }
