.PHONY: test-postgres backend-test-postgres clean-logs

# Run backend tests against local Postgres (Docker)
test-postgres: backend-test-postgres

backend-test-postgres:
	cd Backend && ./scripts/run_tests_postgres.sh

# Clean up log files and test output files
clean-logs:
	@echo "Cleaning log files and test outputs..."
	@rm -f backend.log Backend/backend.log Frontend/frontend.log 2>/dev/null || true
	@rm -f test_output.txt Backend/test_output.txt 2>/dev/null || true
	@rm -f Backend/data/vocabulary_import.log 2>/dev/null || true
	@rm -f repomix_output.txt repomix.config.json 2>/dev/null || true
	@find Backend -maxdepth 1 -type f -name "*.log" -delete 2>/dev/null || true
	@find Frontend -maxdepth 1 -type f -name "*.log" -delete 2>/dev/null || true
	@echo "Log files cleaned successfully"
