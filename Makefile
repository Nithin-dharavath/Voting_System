.PHONY: dev test lint format typecheck seed clean docker-build docker-up docker-down ci-test ci-test-unit

dev:
	uvicorn app:app --reload

test:
	pytest -v

test-cov:
	pytest --cov=. --cov-report=term-missing

lint:
	ruff check .

format:
	black .
	ruff check --fix .

typecheck:
	mypy app.py

seed:
	python database/seed.py

admin:
	python database/create_admin.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

docker-build:
	docker build -t voting-system .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

ci-test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

ci-test-unit:
	pytest -m "not integration" --tb=short -q
