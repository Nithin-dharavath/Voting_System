.PHONY: dev test lint format typecheck seed clean

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
