# LLM Connection Error Fix

## Problem

The application was logging connection errors repeatedly when LLM service (Ollama) was not running:

```
ERROR - LLM prediction error: HTTPConnectionPool(host='localhost', port=11434):
Max retries exceeded with url: /api/generate (Caused by NewConnectionError...)
```

This happened on every transaction when `USE_ENSEMBLE=true` but Ollama wasn't running.

## Solution

Implemented graceful degradation with intelligent error handling:

### 1. Added Connection State Tracking

```python
# In LLMClassifier.__init__
self._service_unavailable = False  # Track if service is down
self._error_logged = False  # Only log error once
```

### 2. Improved Error Handling

Changed from `logger.error()` (repeated) to `logger.warning()` (once):

```python
except requests.exceptions.ConnectionError as e:
    # Only log once
    if not self._service_unavailable:
        self._service_unavailable = True
        logger.warning(f"LLM service unavailable at {self.ollama_url} - will gracefully degrade to rules+ML only")
    return None, 0.0, "LLM unavailable"
```

### 3. Ensemble Router Handles None Gracefully

```python
# In EnsembleRouter._run_llm_classifier
if category is None or confidence == 0.0:
    return None  # Gracefully skip LLM
```

## Behavior Now

### Without Ollama Running:

**Before**:
```
ERROR - LLM prediction error: ConnectionError... (repeated for every transaction)
ERROR - LLM prediction error: ConnectionError...
ERROR - LLM prediction error: ConnectionError...
```

**After**:
```
WARNING - LLM service unavailable at http://localhost:11434 - will gracefully degrade to rules+ML only
(no more errors - system continues using Rules + ML)
```

### With Ollama Running:

Works normally with all 3 methods (Rules + ML + LLM) in ensemble.

## Configuration

Ensemble mode is now safe to keep enabled:

```bash
# In .env
USE_ENSEMBLE=true  # Safe - degrades gracefully if LLM unavailable
```

**Benefits**:
- ✅ No repeated error messages
- ✅ Single warning on first failure
- ✅ Graceful degradation to Rules + ML
- ✅ Works perfectly when Ollama is available
- ✅ Best of both worlds

## How It Works

1. **First transaction**: LLM connection fails → logs WARNING once → continues with Rules + ML
2. **Subsequent transactions**: Skips LLM silently → uses Rules + ML only
3. **If Ollama starts later**: Automatically resumes using LLM (requires restart)

## Testing

```bash
# Test without Ollama
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "UPI-SWIGGY-RESTAURANT", "amount": 250}'

# Returns correctly using Rules + ML:
# → "Food & Dining" (no errors in logs)

# Start Ollama and restart API
ollama serve  # In separate terminal
# Restart API
# Now uses all 3 methods
```

## Start Ollama (Optional)

If you want to use the full ensemble with LLM:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Start service
ollama serve
```

Then restart your application - it will automatically detect and use LLM.

## Summary

**Fixed**: HTTP connection pool errors are now handled gracefully
**Impact**: Single warning instead of repeated errors
**Benefit**: Ensemble mode can stay enabled - works with or without Ollama
**Action**: None required - already fixed in code
