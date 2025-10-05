# Performance Tests

These tests are **manually run** and **not part of the automated CI pipeline**. They are skipped in regular test runs because they are slow and resource-intensive.

## Running Performance Tests

To run all performance tests:

```bash
cd Backend
pytest tests/manual/performance/ -v
```

To run a specific performance test file:

```bash
pytest tests/manual/performance/test_api_performance.py -v
pytest tests/manual/performance/test_auth_speed.py -v
pytest tests/manual/performance/test_server.py -v
pytest tests/manual/performance/test_server_startup.py -v
```

## Test Descriptions

### test_api_performance.py

- Tests API endpoint response times
- Measures throughput and latency
- **Duration**: ~30-60 seconds

### test_auth_speed.py

- Tests authentication performance
- Measures login/registration speed
- **Duration**: ~15-30 seconds

### test_server.py

- Tests server startup and shutdown performance
- Measures resource usage
- **Duration**: ~20-40 seconds

### test_server_startup.py

- Tests server initialization time
- Validates startup sequence
- **Duration**: ~10-20 seconds

## Performance Baseline

When running these tests, compare results against baseline metrics:

- API response time: < 200ms (p95)
- Auth response time: < 100ms (p95)
- Server startup: < 5 seconds

## Notes

- Run these tests on a clean environment for consistent results
- Ensure no other services are competing for resources
- Results may vary based on hardware and system load
- These tests are **not** part of the pre-commit or CI pipeline
