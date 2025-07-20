# Concurrency-Safe ModelManager Implementation

This document describes the implementation of a thread-safe ModelManager to prevent race conditions when accessing shared ML models on GPU resources.

## Problem Statement

The original ModelManager had potential race conditions when multiple threads or processes tried to access the same ML models simultaneously, especially on GPU resources. This could lead to:

- CUDA out of memory errors
- Model corruption
- Inconsistent model states
- Application crashes

## Solution Overview

The new implementation provides:

1. **Thread-safe model access** using reentrant locks
2. **Usage tracking** to monitor concurrent model access
3. **Context managers** for safe model acquisition and release
4. **Exclusive access modes** for operations requiring sole model access
5. **Monitoring capabilities** for debugging and optimization

## Key Features

### 1. Thread-Safe Singleton Pattern

```python
class ModelManager:
    _instance = None
    _lock = threading.RLock()  # Class-level lock for instance creation
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance
```

### 2. Individual Model Locks

Each model type has its own reentrant lock:

- `_whisper_lock`: For Whisper transcription model
- `_translation_lock`: For MarianMT translation models
- `_spacy_lock`: For SpaCy NLP model
- `_cuda_lock`: For CUDA memory operations

### 3. Safe Model Access Context Managers

#### Whisper Model
```python
with model_manager.get_whisper_model_safe() as model:
    transcription = model.transcribe(audio_file)
```

#### SpaCy Model
```python
with model_manager.get_spacy_model_safe() as nlp:
    doc = nlp(text)
    tokens = [token.text for token in doc]
```

#### Translation Model
```python
with model_manager.get_translation_model_safe(src_lang, tgt_lang) as (model, tokenizer):
    inputs = tokenizer([text], return_tensors='pt')
    outputs = model.generate(**inputs)
```

### 4. Usage Tracking

The ModelManager tracks concurrent usage of each model:

```python
# Get current usage statistics
stats = model_manager.get_model_usage_stats()
print(stats)
# Output:
# {
#     'current_usage': {'whisper': 1, 'translation': 0, 'spacy': 2},
#     'device': 'cuda',
#     'models_loaded': {'whisper': True, 'translation': True, 'spacy': True}
# }
```

### 5. Exclusive Access Mode

For operations requiring exclusive model access:

```python
with model_manager.exclusive_model_access('whisper', timeout=30):
    # Only this thread can access the Whisper model
    model = model_manager.get_whisper_model()
    # Perform exclusive operations
```

### 6. Concurrency Control

Wait for model availability with configurable limits:

```python
# Wait for model to be available (max 1 concurrent user)
if model_manager.wait_for_model_availability('whisper', max_concurrent=1, timeout=30):
    # Model is available for use
    pass
```

## Implementation Details

### Thread-Safe Model Initialization

Models are initialized lazily and thread-safely:

```python
def get_whisper_model(self):
    with self._whisper_lock:
        if self.whisper_model is None:
            import whisper
            model_name = get_whisper_model()  # From config
            self.whisper_model = whisper.load_model(model_name, device=self.device)
        return self.whisper_model
```

### Usage Tracking Implementation

```python
@contextmanager
def _track_model_usage(self, model_name: str):
    """Context manager to track model usage."""
    with self._usage_lock:
        self._model_usage[model_name] = self._model_usage.get(model_name, 0) + 1
    
    try:
        yield
    finally:
        with self._usage_lock:
            self._model_usage[model_name] = max(0, self._model_usage.get(model_name, 0) - 1)
```

### Safe Cleanup

The cleanup process waits for ongoing operations:

```python
def cleanup_all_models(self):
    with self._whisper_lock, self._translation_lock, self._spacy_lock, self._cuda_lock:
        # Wait for ongoing model usage to complete
        max_wait_time = 30  # seconds
        wait_start = time.time()
        
        while any(usage > 0 for usage in self._model_usage.values()):
            if time.time() - wait_start > max_wait_time:
                console.print("[bold yellow]Warning: Forcing cleanup despite ongoing model usage[/bold yellow]")
                break
            time.sleep(1)
        
        # Clean up models
        self.whisper_model = None
        self.translation_model = None
        # ... etc
```

## API Integration

The FastAPI server now includes a monitoring endpoint:

```python
@app.get("/api/model-stats")
async def get_model_stats():
    """Get current model usage statistics for monitoring."""
    manager = get_model_manager()
    stats = manager.get_model_usage_stats()
    return JSONResponse(content={"success": True, "stats": stats})
```

## Migration Guide

### Before (Not Thread-Safe)
```python
# Old way - potential race conditions
model = context.model_manager.get_whisper_model()
transcription = model.transcribe(audio_file)
context.model_manager.cleanup_cuda_memory()
```

### After (Thread-Safe)
```python
# New way - thread-safe
with context.model_manager.get_whisper_model_safe() as model:
    transcription = model.transcribe(audio_file)
    context.model_manager.cleanup_cuda_memory()
```

## Testing

Use the provided test script to verify concurrency safety:

```bash
python test_concurrent_models.py
```

This script tests:
- Concurrent model access from multiple threads
- Usage statistics accuracy
- Exclusive access functionality
- Error handling and timeouts

## Performance Considerations

1. **Reentrant Locks**: Allow the same thread to acquire a lock multiple times
2. **Fine-Grained Locking**: Each model has its own lock to minimize contention
3. **Usage Tracking**: Minimal overhead with atomic operations
4. **Context Managers**: Automatic cleanup ensures resources are always released

## Monitoring and Debugging

### Model Usage Statistics
```python
stats = model_manager.get_model_usage_stats()
print(f"Current usage: {stats['current_usage']}")
print(f"Models loaded: {stats['models_loaded']}")
print(f"Device: {stats['device']}")
```

### API Monitoring
```bash
curl http://localhost:8000/api/model-stats
```

## Benefits

1. **Race Condition Prevention**: Thread-safe access to all models
2. **Resource Management**: Proper cleanup and memory management
3. **Monitoring**: Real-time usage statistics for debugging
4. **Scalability**: Support for multiple concurrent requests
5. **Reliability**: Graceful handling of timeouts and errors
6. **Backward Compatibility**: Existing code continues to work

## Deployment Recommendations

1. **Single Worker**: For development, use `uvicorn --workers 1`
2. **Multiple Workers**: For production, the thread-safe implementation supports multiple workers
3. **Monitoring**: Use the `/api/model-stats` endpoint for health checks
4. **Resource Limits**: Configure appropriate timeouts based on your hardware

## Future Enhancements

1. **Model Pool**: Implement a pool of model instances for higher concurrency
2. **Load Balancing**: Distribute model access across multiple GPUs
3. **Caching**: Implement intelligent model caching strategies
4. **Metrics**: Add detailed performance metrics and logging