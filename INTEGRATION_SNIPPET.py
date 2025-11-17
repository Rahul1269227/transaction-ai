"""
Integration Snippet for Enhanced Features
Add this code to apps/api/main.py to enable all new features
"""

# ============================================================================
# ADD THESE IMPORTS AT THE TOP OF apps/api/main.py
# ============================================================================

from apps.api.enhanced_endpoints import router as enhanced_router
from core.auth import init_auth
from core.active_learning import init_active_learning
from core.multitenancy import init_multitenancy

# ============================================================================
# ADD THIS TO THE STARTUP FUNCTION (or create if doesn't exist)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global router, merchant_resolver, db_engine, SessionLocal, redis_client
    
    # ... existing initialization code ...
    
    # Initialize enhanced features
    logger.info("Initializing enhanced features...")
    
    # Initialize authentication and rate limiting
    init_auth(redis_client)
    logger.info("✅ Authentication initialized")
    
    # Initialize active learning
    if SessionLocal:
        init_active_learning(SessionLocal())
        logger.info("✅ Active learning initialized")
    
    # Initialize multi-tenancy
    if SessionLocal:
        init_multitenancy(SessionLocal())
        logger.info("✅ Multi-tenancy initialized")
    
    # Include enhanced router
    app.include_router(enhanced_router)
    logger.info("✅ Enhanced endpoints registered")

# ============================================================================
# OPTIONAL: Add authentication to existing endpoints
# ============================================================================

# Example: Protect categorize endpoint
from core.auth import require_auth, check_rate_limit
from typing import Dict

@app.post("/categorize", response_model=TransactionOutput, tags=["Categorization"])
async def categorize(
    transaction: TransactionInput,
    background_tasks: BackgroundTasks,
    # Add these dependencies (make optional for backward compatibility)
    api_key_info: Optional[Dict] = Depends(lambda: None),  # Optional auth
    rate_limit_info: Optional[Dict] = Depends(lambda: None)  # Optional rate limit
):
    """
    Categorize a transaction
    
    Now supports optional authentication via X-API-Key header
    """
    # ... existing categorization logic ...
    pass

# ============================================================================
# ADD MULTI-TENANCY SUPPORT TO TRANSACTION STORAGE
# ============================================================================

# In the categorize endpoint, after getting result:
from core.multitenancy import get_tenant_context

# Extract tenant context from API key (if provided)
tenant = None
if api_key_info:
    tenant = get_tenant_context(api_key_info)

# When saving to database:
if db_engine and tenant:
    # Add organization_id to transaction record
    txn_record.organization_id = tenant.organization_id

# ============================================================================
# ADD ACTIVE LEARNING PRIORITIZATION
# ============================================================================

# After categorization, check if should prioritize for review
from core.active_learning import active_learning_service

if active_learning_service:
    should_prioritize, uncertainty = active_learning_service.prioritize_for_review(
        result_dict,
        transaction_id=record_id
    )
    
    if should_prioritize:
        logger.info(f"Transaction {record_id} prioritized for review (uncertainty: {uncertainty:.2f})")

# ============================================================================
# DATABASE MIGRATION: Add multi-tenancy tables
# ============================================================================

# Run this once to create tables:
"""
from core.multitenancy import OrganizationORM, UserORM, Base
from apps.api.main import Base as MainBase

# Merge schemas
Base.metadata.create_all(db_engine)
"""

# ============================================================================
# ENVIRONMENT VARIABLES TO ADD TO .env
# ============================================================================

"""
# Fast Mode (already exists, just ensure it's set)
FAST_MODE=true
FAST_MODE_THRESHOLD=0.90

# Authentication (optional, defaults to dev mode)
ENABLE_AUTH=false  # Set to true to require API keys
DEFAULT_RATE_LIMIT=100

# Multi-tenancy
ENABLE_MULTITENANCY=true
"""
