"""
Transaction Categorization API
FastAPI application for transaction categorization service
"""

import hashlib
import json
import logging
import os
import sys
import time
import subprocess
import yaml
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import (
    Boolean,
    Column,
    Date as SADate,
    DateTime,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Ensure repo root is on sys.path before importing project modules
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()

from core.model import EnsembleRouter, HybridRouter  # noqa: E402
from core.models import (  # noqa: E402
    CategoryResult,
    ErrorResponse,
    FeedbackInput,
    FeedbackResponse,
    HealthResponse,
    MerchantMatch as MerchantMatchModel,
    MerchantMatchResult,
    MerchantQuery,
    NormalizedTransaction,
    TransactionBatchInput,
    TransactionBatchOutput,
    TransactionInput,
    TransactionOutput,
    TrainingRequest,
    TrainingResponse,
)
from core.resolve import MerchantResolver  # noqa: E402
from core.preprocessor import preprocess_transaction  # noqa: E402

RouterType = Union[HybridRouter, EnsembleRouter]
Base = declarative_base()


def bool_from_env(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_path(path_str: Optional[str], fallback: Path) -> Path:
    if not path_str:
        return fallback
    candidate = Path(path_str)
    return candidate if candidate.is_absolute() else (BASE_DIR / candidate)


# Environment-driven configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))
AUTO_ACCEPT_THRESHOLD = float(os.getenv("AUTO_ACCEPT_THRESHOLD", "0.85"))
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.60"))
MCC_WEIGHT = float(os.getenv("MCC_WEIGHT", "0.25"))
RULE_WEIGHT = float(os.getenv("RULE_WEIGHT", "0.25"))
ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.30"))
LLM_WEIGHT = float(os.getenv("LLM_WEIGHT", "0.20"))
LLM_URL = os.getenv("LLM_URL", "http://llm-service:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "3.0"))  # Aggressive 3-second timeout
USE_ENSEMBLE = bool_from_env("USE_ENSEMBLE", False)
FAST_MODE = bool_from_env("FAST_MODE", False)  # Skip LLM when rule+ML agree with high confidence
FAST_MODE_THRESHOLD = float(os.getenv("FAST_MODE_THRESHOLD", "0.90"))  # Confidence threshold for fast mode
PROMETHEUS_ENABLED = bool_from_env("PROMETHEUS_ENABLED", False)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = bool_from_env("API_RELOAD", True)

TAXONOMY_PATH = resolve_path(os.getenv("TAXONOMY_PATH"), BASE_DIR / "data" / "taxonomy.yaml")
GAZETTEER_PATH = resolve_path(
    os.getenv("GAZETTEER_PATH"), BASE_DIR / "data" / "gazetteer" / "merchant_aliases.csv"
)
# Use balanced model by default for best performance across all categories
# Default path can be overridden via MODEL_PATH environment variable
MODEL_PATH = resolve_path(
    os.getenv("MODEL_PATH"),
    BASE_DIR / "models" / "transaction_classifier_balanced_final"
)
FEW_SHOT_PATH = os.getenv("FEW_SHOT_EXAMPLES_PATH")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Transaction AI Categorization API",
    description="AI-powered transaction categorization system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# SQLAlchemy ORM models -----------------------------------------------------
class TransactionRecordORM(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2))
    currency = Column(String(10), default="INR")
    date = Column(SADate)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    confidence = Column(Numeric(5, 4))
    method = Column(String(50))
    merchant = Column(String(255))
    channel = Column(String(50))
    reference = Column(String(255))
    requires_review = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class FeedbackRecordORM(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    transaction_text = Column(Text, nullable=False)
    predicted_category = Column(String(100), nullable=False)
    correct_category = Column(String(100), nullable=False)
    predicted_subcategory = Column(String(100))
    correct_subcategory = Column(String(100))
    amount = Column(Numeric(15, 2))
    date = Column(SADate)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingJobRecordORM(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, nullable=False)
    dataset_path = Column(Text)
    model_name = Column(String(255))
    status = Column(String(50), default="queued")
    accuracy = Column(Numeric(5, 4))
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


# Global runtime state ------------------------------------------------------
router: Optional[RouterType] = None
merchant_resolver: Optional[MerchantResolver] = None
db_engine = None
SessionLocal: Optional[sessionmaker] = None
redis_client: Optional[Redis] = None


# Prometheus metrics --------------------------------------------------------
if PROMETHEUS_ENABLED:
    try:
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            Counter,
            Gauge,
            Histogram,
            generate_latest,
        )

        REQUEST_COUNTER = Counter(
            "categorization_requests_total",
            "Total API requests grouped by endpoint",
            ["endpoint"],
        )
        LATENCY_HIST = Histogram(
            "categorization_latency_seconds",
            "End-to-end request latency",
            ["endpoint"],
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
        )
        METHOD_COUNTER = Counter(
            "method_usage_total", "Method usage count", ["method"]
        )
        REVIEW_COUNTER = Counter(
            "categorization_requires_review_total",
            "Transactions routed to manual review",
            ["endpoint"],
        )
        CACHE_COUNTER = Counter(
            "categorization_cache_events_total",
            "Cache hits/misses",
            ["endpoint", "result"],
        )
        ENSEMBLE_AGREEMENT = Gauge(
            "ensemble_agreement_ratio",
            "Agreement ratio across ensemble methods (last observation)",
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(f"Prometheus client unavailable: {exc}")
        PROMETHEUS_ENABLED = False
        REQUEST_COUNTER = LATENCY_HIST = METHOD_COUNTER = REVIEW_COUNTER = CACHE_COUNTER = None
        ENSEMBLE_AGREEMENT = None
        CONTENT_TYPE_LATEST = None
        generate_latest = None
else:
    REQUEST_COUNTER = LATENCY_HIST = METHOD_COUNTER = REVIEW_COUNTER = CACHE_COUNTER = None
    ENSEMBLE_AGREEMENT = None
    CONTENT_TYPE_LATEST = None
    generate_latest = None


def record_metrics(
    endpoint: str,
    duration: float,
    output: Optional[TransactionOutput] = None,
    cache_hit: Optional[bool] = None,
) -> None:
    if not PROMETHEUS_ENABLED or REQUEST_COUNTER is None:
        return

    REQUEST_COUNTER.labels(endpoint=endpoint).inc()
    LATENCY_HIST.labels(endpoint=endpoint).observe(duration)

    if cache_hit is not None:
        CACHE_COUNTER.labels(endpoint=endpoint, result="hit" if cache_hit else "miss").inc()

    if not output:
        return

    METHOD_COUNTER.labels(method=output.method).inc()
    if output.requires_review:
        REVIEW_COUNTER.labels(endpoint=endpoint).inc()

    if output.ensemble_votes and ENSEMBLE_AGREEMENT:
        total = output.ensemble_votes.get("total_methods") or 0
        agree = output.ensemble_votes.get("agreement_count") or 0
        if total:
            ENSEMBLE_AGREEMENT.set(agree / total)


# Auto-learning helpers -----------------------------------------------------
def load_training_config():
    """Load training configuration"""
    config_path = BASE_DIR / "config" / "training_config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

def count_corrections() -> int:
    """Count total corrections in corrections.jsonl"""
    try:
        corrections_file = BASE_DIR / "data" / "corrections" / "corrections.jsonl"
        if not corrections_file.exists():
            return 0

        count = 0
        with open(corrections_file, 'r') as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    except Exception as e:
        logger.warning(f"Failed to count corrections: {e}")
        return 0

def trigger_auto_retraining():
    """Trigger automatic retraining in background"""
    try:
        logger.info("Triggering automatic retraining...")
        # Run training script in background
        subprocess.Popen(
            ["python3", "scripts/train.py"],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from parent process
        )
        logger.info("Auto-retraining triggered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to trigger auto-retraining: {e}")
        return False

def reload_router_model():
    """Reload the router with updated model (hot swap)"""
    global router
    try:
        logger.info("Reloading router with updated model...")
        old_router = router

        # Initialize new router
        model_path = os.getenv("MODEL_PATH", "models/transaction_classifier_balanced_final")
        new_router = EnsembleRouter(model_path=model_path, enable_llm=True)

        # Atomic swap
        router = new_router
        logger.info("Router reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reload router: {e}")
        # Restore old router if new one failed
        router = old_router if 'old_router' in locals() else router
        return False

# Database helpers ----------------------------------------------------------
def init_database() -> None:
    global db_engine, SessionLocal
    if not DATABASE_URL:
        logger.info("DATABASE_URL not set; database persistence disabled")
        return

    try:
        db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
        logger.info("Database engine initialized")
    except Exception as exc:
        logger.warning(f"Failed to initialize database: {exc}")
        db_engine = None
        SessionLocal = None


@contextmanager
def db_session():  # type: ignore[misc]
    """Context manager for database sessions. Yields None if database not configured."""
    if SessionLocal is None:
        yield None
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _to_decimal(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def persist_transaction_record(output: TransactionOutput) -> Optional[int]:
    if SessionLocal is None:
        return None

    normalized = output.normalized
    with db_session() as session:
        if session is None:
            return None
        try:
            record = TransactionRecordORM(
                original_text=output.original_text,
                amount=_to_decimal(normalized.amount),
                currency=normalized.currency,
                date=_parse_date(normalized.date),
                category=output.category,
                subcategory=output.subcategory,
                confidence=_to_decimal(output.confidence),
                method=output.method,
                merchant=normalized.merchant,
                channel=normalized.channel,
                reference=normalized.reference,
                requires_review=output.requires_review,
            )
            session.add(record)
            session.flush()
            return record.id
        except Exception as exc:
            logger.warning(f"Failed to persist transaction: {exc}")
            return None


def persist_feedback_record(feedback: FeedbackInput) -> Optional[int]:
    if SessionLocal is None:
        return None

    with db_session() as session:
        if session is None:
            return None
        try:
            record = FeedbackRecordORM(
                transaction_text=feedback.transaction_text,
                predicted_category=feedback.predicted_category,
                correct_category=feedback.correct_category,
                predicted_subcategory=feedback.predicted_subcategory,
                correct_subcategory=feedback.correct_subcategory,
                amount=_to_decimal(feedback.amount),
                date=_parse_date(feedback.date),
                notes=feedback.notes,
            )
            session.add(record)
            session.flush()
            return record.id
        except Exception as exc:
            logger.warning(f"Failed to persist feedback: {exc}")
            return None


def enqueue_training_job(request: TrainingRequest) -> str:
    job_id = str(uuid4())
    if SessionLocal is None:
        logger.info("Database not configured; returning ephemeral training job id")
        return job_id

    with db_session() as session:
        if session is None:
            return job_id
        try:
            record = TrainingJobRecordORM(
                job_id=job_id,
                dataset_path=request.dataset_path,
                model_name=request.model_name,
                status="queued",
                metrics=request.parameters or {},
            )
            session.add(record)
        except Exception as exc:
            logger.warning(f"Failed to persist training job: {exc}")
    return job_id


def persist_feedback_locally(feedback: FeedbackInput) -> str:
    feedback_dir = BASE_DIR / "data" / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / f"feedback_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
    payload = feedback.model_dump(mode="json")
    with feedback_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return feedback_file.name


# Cache helpers -------------------------------------------------------------
def init_cache() -> None:
    global redis_client
    if not REDIS_URL:
        logger.info("REDIS_URL not set; response caching disabled")
        return

    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info("Redis cache initialized")
    except RedisError as exc:
        logger.warning(f"Failed to initialize Redis: {exc}")
        redis_client = None


def build_cache_key(transaction: TransactionInput) -> str:
    payload = f"{transaction.text}|{transaction.amount}|{transaction.date}|{transaction.currency}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"txn_cache:{digest}"


def fetch_cached_output(key: str) -> Optional[TransactionOutput]:
    if not redis_client:
        return None
    try:
        cached = redis_client.get(key)
        if not cached:
            return None
        return TransactionOutput(**json.loads(cached))
    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning(f"Failed to fetch cached response: {exc}")
        return None


def cache_output(key: str, output: TransactionOutput) -> None:
    if not redis_client:
        return
    try:
        redis_client.setex(key, CACHE_TTL, json.dumps(output.model_dump(mode="json")))
    except RedisError as exc:
        logger.warning(f"Failed to cache response: {exc}")


# Router and resolver initialization ----------------------------------------
def build_router() -> RouterType:
    taxonomy = str(TAXONOMY_PATH) if TAXONOMY_PATH.exists() else None
    gazetteer = str(GAZETTEER_PATH) if GAZETTEER_PATH.exists() else None
    model_path = str(MODEL_PATH) if MODEL_PATH.exists() else None
    few_shot = str(resolve_path(FEW_SHOT_PATH, BASE_DIR)) if FEW_SHOT_PATH else None

    if USE_ENSEMBLE:
        logger.info("Initializing ensemble router with LLM support")
        return EnsembleRouter(
            taxonomy_path=taxonomy,
            gazetteer_path=gazetteer,
            ml_model_path=model_path,
            llm_url=LLM_URL,
            llm_model=LLM_MODEL,
            few_shot_examples_path=few_shot,
            mcc_weight=MCC_WEIGHT,
            rule_weight=RULE_WEIGHT,
            ml_weight=ML_WEIGHT,
            llm_weight=LLM_WEIGHT,
            auto_accept_threshold=AUTO_ACCEPT_THRESHOLD,
            review_threshold=REVIEW_THRESHOLD,
            enable_parallel=True,
            llm_timeout=LLM_TIMEOUT,
            fast_mode=FAST_MODE,
            fast_mode_threshold=FAST_MODE_THRESHOLD,
        )

    logger.info("Initializing hybrid router (rules + ML)")
    return HybridRouter(
        taxonomy_path=taxonomy,
        gazetteer_path=gazetteer,
        model_path=model_path,
        auto_accept_threshold=AUTO_ACCEPT_THRESHOLD,
        review_threshold=REVIEW_THRESHOLD,
    )


def init_merchant_resolver() -> Optional[MerchantResolver]:
    if not GAZETTEER_PATH.exists():
        return None
    try:
        resolver = MerchantResolver(str(GAZETTEER_PATH))
        logger.info("Merchant resolver initialized")
        return resolver
    except Exception as exc:
        logger.warning(f"Failed to initialize merchant resolver: {exc}")
        return None


# FastAPI lifecycle ---------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    global router, merchant_resolver
    logger.info("Starting Transaction Categorization API...")

    init_database()
    init_cache()

    try:
        router = build_router()
        logger.info("Router initialized (%s)", router.__class__.__name__)
    except Exception as exc:
        logger.error(f"Router initialization failed: {exc}")
        raise

    merchant_resolver = init_merchant_resolver()
    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if redis_client:
        try:
            redis_client.close()
        except Exception:
            pass
    logger.info("Shutting down Transaction Categorization API...")


# Utility helpers -----------------------------------------------------------
def build_transaction_output(
    transaction: TransactionInput,
    normalized_payload: Dict[str, Any],
    result: Any,
) -> TransactionOutput:
    normalized = NormalizedTransaction(**normalized_payload["normalized"])
    alternatives = None
    if result.alternatives:
        alternatives = [
            CategoryResult(
                category=alt[0],
                subcategory=None,
                confidence=alt[1],
                explanations=[],
                method=result.method,
            )
            for alt in result.alternatives
        ]

    return TransactionOutput(
        original_text=transaction.text,
        normalized=normalized,
        category=result.category,
        subcategory=result.subcategory,
        confidence=float(result.confidence),
        explanations=result.explanations or [],
        method=result.method,
        alternatives=alternatives,
        requires_review=result.requires_review,
        ensemble_votes=getattr(result, "ensemble_votes", None),
    )


def get_effective_merch_resolver() -> Optional[MerchantResolver]:
    if merchant_resolver:
        return merchant_resolver
    if router and getattr(router, "merchant_resolver", None):
        return router.merchant_resolver
    return None


def llm_component_status() -> str:
    if not router or not getattr(router, "llm_classifier", None):
        return "unavailable"
    try:
        return "healthy" if router.llm_classifier.check_health() else "degraded"
    except Exception:
        return "degraded"


# API endpoints -------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    return {
        "service": "Transaction AI Categorization API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    components = {
        "router": "healthy" if router else "unavailable",
        "normalizer": "healthy" if router else "unavailable",
        "rule_categorizer": "healthy"
        if router and getattr(router, "rule_categorizer", None)
        else "unavailable",
        "ml_classifier": "healthy"
        if router and getattr(router, "ml_classifier", None)
        else "unavailable",
        "llm_classifier": llm_component_status(),
        "merchant_resolver": "healthy" if get_effective_merch_resolver() else "unavailable",
        "database": "healthy" if SessionLocal else "unavailable",
        "cache": "healthy" if redis_client else "unavailable",
    }

    status = "healthy" if all(value == "healthy" for value in components.values()) else "degraded"
    return HealthResponse(
        status=status,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        components=components,
    )


@app.post("/categorize", response_model=TransactionOutput, tags=["Categorization"])
async def categorize_transaction(transaction: TransactionInput):
    if not router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Preprocess transaction text to extract key information from JSON or clean plain text
    from core.preprocessor import preprocessor
    processed_text, extracted_amount, extracted_date, extracted_currency, extracted_merchant = preprocessor.preprocess_with_fields(transaction.text)

    # Use extracted fields from JSON if available, otherwise fall back to transaction fields
    final_amount = transaction.amount if transaction.amount is not None else extracted_amount
    final_date = transaction.date if transaction.date else extracted_date
    final_currency = transaction.currency if transaction.currency != "INR" else extracted_currency
    final_merchant = extracted_merchant  # Always prefer extracted merchant from JSON

    logger.debug(f"Preprocessed: {transaction.text[:100]}... -> {processed_text}")
    logger.debug(f"Extracted fields: amount={final_amount}, date={final_date}, currency={final_currency}, merchant={final_merchant}")

    cache_key = build_cache_key(transaction)
    cached_output = fetch_cached_output(cache_key)
    if cached_output:
        record_metrics("categorize", 0.0, cached_output, cache_hit=True)
        return cached_output

    start = time.perf_counter()
    try:
        # Normalize first to get clean data for both categorization and response
        normalized_payload = router.normalizer.normalize(
            text=processed_text,  # Use preprocessed text, not raw JSON
            amount=final_amount,
            date=final_date,
            currency=final_currency,
            merchant=final_merchant,
        )

        # Categorize using the normalized data
        result = router.categorize(
            text=processed_text,
            amount=final_amount,
            date=final_date,
            currency=final_currency,
            merchant=final_merchant,
            mcc=transaction.mcc,
        )

        response = build_transaction_output(transaction, normalized_payload, result)

        # Only persist and cache high-confidence results (not requiring review)
        # Low-confidence results are stored only after user feedback
        if not response.requires_review:
            record_id = persist_transaction_record(response)
            if record_id:
                response.record_id = record_id
            cache_output(cache_key, response)
        else:
            logger.info(f"Skipping DB/cache for low confidence result: {response.confidence:.2f}")

        duration = time.perf_counter() - start
        record_metrics("categorize", duration, response, cache_hit=False)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error categorizing transaction: {exc}")
        raise HTTPException(status_code=500, detail=f"Categorization failed: {exc}")


@app.post("/categorize/batch", response_model=TransactionBatchOutput, tags=["Categorization"])
async def categorize_batch(batch: TransactionBatchInput):
    if not router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    start = time.perf_counter()
    try:
        transactions_dict = [
            {
                "text": txn.text,
                "amount": txn.amount,
                "date": txn.date,
                "currency": txn.currency,
                "mcc": txn.mcc,
            }
            for txn in batch.transactions
        ]
        results = router.categorize_batch(transactions_dict)

        outputs: List[TransactionOutput] = []
        for txn, result in zip(batch.transactions, results):
            normalized_payload = router.normalizer.normalize(
                text=txn.text,
                amount=txn.amount,
                date=txn.date,
                currency=txn.currency,
            )
            output = build_transaction_output(txn, normalized_payload, result)

            # Only persist high-confidence results (not requiring review)
            if not output.requires_review:
                record_id = persist_transaction_record(output)
                if record_id:
                    output.record_id = record_id

            outputs.append(output)
            record_metrics("categorize_batch", 0.0, output)

        stats = router.get_stats(results)  # type: ignore[arg-type]
        duration = time.perf_counter() - start
        LATENCY_HIST.labels(endpoint="categorize_batch").observe(duration) if PROMETHEUS_ENABLED else None

        return TransactionBatchOutput(results=outputs, stats=stats)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error categorizing batch: {exc}")
        raise HTTPException(status_code=500, detail=f"Batch categorization failed: {exc}")


@app.post("/merchants", response_model=MerchantMatchResult, tags=["Merchants"])
async def search_merchants(query: MerchantQuery):
    resolver = get_effective_merch_resolver()
    if not resolver:
        raise HTTPException(status_code=503, detail="Merchant resolver not available")

    try:
        matches = resolver.search(query.query, limit=query.limit)
        match_models = [
            MerchantMatchModel(
                merchant_id=m.merchant_id,
                canonical_name=m.canonical_name,
                aliases=m.aliases,
                category=m.category,
                subcategory=m.subcategory,
                similarity_score=m.similarity_score,
            )
            for m in matches
        ]
        return MerchantMatchResult(query=query.query, matches=match_models)
    except Exception as exc:
        logger.error(f"Error searching merchants: {exc}")
        raise HTTPException(status_code=500, detail=f"Merchant search failed: {exc}")


@app.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(feedback: FeedbackInput):
    try:
        # Store feedback record in database
        feedback_id = persist_feedback_record(feedback)
        storage_target = "database"
        if feedback_id is None:
            storage_target = persist_feedback_locally(feedback)

        # ACTIVE LEARNING: Also store corrections in corrections.jsonl for retraining
        corrections_dir = BASE_DIR / "data" / "corrections"
        corrections_dir.mkdir(parents=True, exist_ok=True)
        corrections_file = corrections_dir / "corrections.jsonl"

        correction_entry = {
            "text": feedback.transaction_text,
            "predicted_category": feedback.predicted_category,
            "correct_category": feedback.correct_category,
            "predicted_subcategory": feedback.predicted_subcategory,
            "correct_subcategory": feedback.correct_subcategory,
            "confidence": None,  # Not available from feedback
            "method": None,  # Not available from feedback
            "timestamp": datetime.utcnow().isoformat(),
            "was_incorrect": feedback.predicted_category != feedback.correct_category,
            "amount": feedback.amount,
            "date": feedback.date,
        }

        with open(corrections_file, "a", encoding="utf-8") as f:
            json.dump(correction_entry, f)
            f.write("\n")

        logger.info(f"Stored correction: {feedback.predicted_category} -> {feedback.correct_category} (was_incorrect={correction_entry['was_incorrect']})")

        # Auto-retraining: Check if we've reached the threshold
        config = load_training_config()
        min_corrections = config.get('corrections', {}).get('min_for_retraining', 50)
        correction_count = count_corrections()

        if correction_count >= min_corrections and correction_count % min_corrections == 0:
            # Trigger retraining at exact multiples of threshold
            logger.info(f"Reached {correction_count} corrections (threshold: {min_corrections}), triggering auto-retraining...")
            trigger_auto_retraining()

        # Also store the transaction with the correct category from user feedback
        # This ensures low-confidence transactions are persisted after user review
        if SessionLocal is not None:
            with db_session() as session:
                if session is not None:
                    try:
                        # Determine if user accepted or corrected the prediction
                        was_correct = feedback.predicted_category == feedback.correct_category

                        # Create transaction record with user-confirmed category
                        transaction_record = TransactionRecordORM(
                            original_text=feedback.transaction_text,
                            amount=_to_decimal(feedback.amount),
                            currency="INR",  # Default, could be extended
                            date=_parse_date(feedback.date),
                            category=feedback.correct_category,
                            subcategory=feedback.correct_subcategory,
                            confidence=_to_decimal(1.0 if was_correct else 0.0),  # User-confirmed = 100%
                            method="user_feedback",
                            requires_review=False,
                            reviewed=True,
                        )
                        session.add(transaction_record)
                        session.flush()
                        logger.info(f"Stored transaction from feedback: {transaction_record.id}")

                        # Cache the user-confirmed categorization for future identical transactions
                        if was_correct and redis_client:
                            try:
                                # Build cache key for this transaction
                                cache_key_input = TransactionInput(
                                    text=feedback.transaction_text,
                                    amount=feedback.amount,
                                    date=feedback.date,
                                    currency="INR"
                                )
                                cache_key = build_cache_key(cache_key_input)

                                # Create cached output
                                cached_output = TransactionOutput(
                                    category=feedback.correct_category,
                                    subcategory=feedback.correct_subcategory,
                                    confidence=1.0,
                                    method="user_feedback_cached",
                                    original_text=feedback.transaction_text,
                                    requires_review=False,
                                    normalized=NormalizedTransaction(
                                        merchant=None,
                                        amount=feedback.amount,
                                        date=feedback.date,
                                        currency="INR"
                                    ),
                                    record_id=transaction_record.id
                                )
                                cache_output(cache_key, cached_output)
                                logger.info(f"Cached user-confirmed transaction")
                            except Exception as e:
                                logger.warning(f"Failed to cache user feedback: {e}")

                    except Exception as e:
                        logger.warning(f"Failed to persist transaction from feedback: {e}")

        return FeedbackResponse(
            status="success",
            message=f"Feedback stored in {storage_target}",
            feedback_id=str(feedback_id) if feedback_id else None,
        )
    except Exception as exc:
        logger.error(f"Error saving feedback: {exc}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {exc}")


@app.post("/train", response_model=TrainingResponse, tags=["Training"])
async def trigger_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(
            "Training requested for dataset=%s model=%s",
            request.dataset_path,
            request.model_name,
        )
        job_id = enqueue_training_job(request)
        # Placeholder background task hook
        # background_tasks.add_task(run_training_job, job_id, request)

        return TrainingResponse(
            status="queued",
            message="Training job queued",
            job_id=job_id,
            model_path=None,
            metrics=None,
        )
    except Exception as exc:
        logger.error(f"Error triggering training: {exc}")
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}")


@app.post("/feedback-learning", tags=["Training"])
async def trigger_feedback_learning(background_tasks: BackgroundTasks):
    """
    Trigger automatic learning from user feedback

    This will:
    1. Export feedback from database
    2. Merge with existing training data
    3. Retrain ML model
    4. Update LLM few-shot examples
    """
    try:
        if not DATABASE_URL:
            raise HTTPException(
                status_code=400,
                detail="Database not configured. Cannot perform feedback learning."
            )

        import subprocess

        # Run feedback learning in background
        def run_feedback_learning():
            try:
                logger.info("Starting feedback learning process...")

                cmd = [
                    "python3",
                    str(BASE_DIR / "scripts" / "feedback_learning.py"),
                    "--database-url", DATABASE_URL,
                    "--original-data", str(BASE_DIR / "data" / "datasets" / "synthetic_train.jsonl"),
                    "--min-feedback", "5",  # Lower threshold for demo
                    "--output-dir", str(BASE_DIR / "data" / "learning"),
                    "--model-output", str(MODEL_PATH),
                    "--few-shot-output", str(BASE_DIR / "data" / "few_shot_examples.jsonl")
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=900  # 15 minutes
                )

                if result.returncode == 0:
                    logger.info("✅ Feedback learning completed successfully")
                    logger.info(result.stdout)

                    # Reload the router with new model
                    global router
                    router = build_router()
                    logger.info("🔄 Router reloaded with updated model")
                else:
                    logger.error(f"❌ Feedback learning failed: {result.stderr}")

            except Exception as e:
                logger.error(f"Error in feedback learning: {e}")

        # Schedule background task
        background_tasks.add_task(run_feedback_learning)

        return {
            "status": "started",
            "message": "Feedback learning process started in background",
            "estimated_time": "5-15 minutes"
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error triggering feedback learning: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start feedback learning: {exc}"
        )


@app.post("/reload-model", tags=["Training"])
async def reload_model():
    """
    Reload the router with updated model (hot swap)

    This endpoint allows you to reload the model without restarting the API server.
    Useful after training completes to immediately use the new model.
    """
    try:
        success = reload_router_model()

        if success:
            return {
                "status": "success",
                "message": "Model reloaded successfully",
                "model_path": os.getenv("MODEL_PATH", "models/transaction_classifier_balanced_final")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reload model - check logs for details"
            )

    except Exception as exc:
        logger.error(f"Error reloading model: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Model reload failed: {exc}"
        )


@app.post("/batch-categorize", tags=["Categorization"])
async def batch_categorize_simple(request: Dict[str, List[str]]):
    """
    Simplified batch categorization endpoint for UI
    Accepts array of transaction strings with 5-minute timeout
    """
    if not router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    transactions = request.get("transactions", [])
    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")

    if len(transactions) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 transactions per batch")

    start = time.perf_counter()
    results = []

    try:
        for idx, txn_text in enumerate(transactions):
            try:
                # Validate that transaction text is a string
                if not isinstance(txn_text, str):
                    error_msg = f"Transaction at index {idx} is not a string: {type(txn_text).__name__}. Value: {txn_text}"
                    logger.error(error_msg)
                    results.append({
                        "transaction": str(txn_text) if txn_text else "invalid",
                        "category": "Unknown",
                        "subcategory": None,
                        "confidence": 0.0,
                        "method": "error",
                        "status": "error",
                        "error_message": error_msg
                    })
                    continue
                
                txn_text_str = str(txn_text).strip()
                if not txn_text_str:
                    error_msg = "Transaction text cannot be empty"
                    logger.error(f"Empty transaction at index {idx}")
                    results.append({
                        "transaction": "",
                        "category": "Unknown",
                        "subcategory": None,
                        "confidence": 0.0,
                        "method": "error",
                        "status": "error",
                        "error_message": error_msg
                    })
                    continue
                
                # Categorize each transaction
                result = router.categorize(
                    text=txn_text_str,
                    amount=None,
                    date=None,
                    currency="INR",
                )

                # Build successful result
                results.append({
                    "transaction": txn_text_str,
                    "category": result.category,
                    "subcategory": result.subcategory,
                    "confidence": float(result.confidence),
                    "method": result.method,
                    "status": "success"
                })

                # Log progress for large batches
                if (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx + 1}/{len(transactions)} transactions")

            except Exception as exc:
                logger.warning(f"Error categorizing transaction '{str(txn_text)[:50]}...': {exc}")
                results.append({
                    "transaction": str(txn_text) if txn_text else "invalid",
                    "category": "Unknown",
                    "subcategory": None,
                    "confidence": 0.0,
                    "method": "error",
                    "status": "error",
                    "error_message": str(exc)
                })

        duration = time.perf_counter() - start
        logger.info(f"Batch categorization completed: {len(transactions)} transactions in {duration:.2f}s")

        return {
            "results": results,
            "total": len(transactions),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "duration_seconds": duration
        }

    except Exception as exc:
        logger.error(f"Error in batch categorization: {exc}")
        raise HTTPException(status_code=500, detail=f"Batch categorization failed: {exc}")


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get real-time statistics from the database"""
    if SessionLocal is None:
        # Return default stats if database is not configured
        return {
            "total_processed": 0,
            "avg_latency_ms": 0,
            "accuracy": 0.0,
            "review_rate": 0.0
        }

    with db_session() as session:
        if session is None:
            return {
                "total_processed": 0,
                "avg_latency_ms": 0,
                "accuracy": 0.0,
                "review_rate": 0.0
            }

        try:
            # Get total processed transactions
            from sqlalchemy import func, cast, Float
            total = session.query(func.count(TransactionRecordORM.id)).scalar() or 0

            # Get average confidence as proxy for accuracy
            avg_confidence = session.query(func.avg(TransactionRecordORM.confidence)).scalar() or 0.0

            # Get review rate
            review_count = session.query(func.count(TransactionRecordORM.id)).filter(
                TransactionRecordORM.requires_review == True
            ).scalar() or 0
            review_rate = (review_count / total) if total > 0 else 0.0

            # Calculate average latency (mock for now as we don't store timestamps)
            # In production, you'd calculate this from request timestamps
            avg_latency = 850.0  # Default value

            return {
                "total_processed": total,
                "avg_latency_ms": avg_latency,
                "accuracy": float(avg_confidence) if avg_confidence else 0.0,
                "review_rate": float(review_rate)
            }
        except Exception as exc:
            logger.error(f"Error fetching stats: {exc}")
            return {
                "total_processed": 0,
                "avg_latency_ms": 0,
                "accuracy": 0.0,
                "review_rate": 0.0
            }


if PROMETHEUS_ENABLED and generate_latest:
    @app.get("/metrics")
    async def metrics():
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Error handlers ------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            details=None,
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)},
        ).dict(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD,
        log_level=LOG_LEVEL.lower(),
    )
