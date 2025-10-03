.PHONY: test-postgres backend-test-postgres

# Run backend tests against local Postgres (Docker)
test-postgres: backend-test-postgres

backend-test-postgres:
	cd Backend && ./scripts/run_tests_postgres.sh
