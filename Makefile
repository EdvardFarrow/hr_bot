.PHONY: help install run test lint format docker-up docker-down docker-logs clean

install:
	poetry install

run:
	poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

format:
	poetry run black .

lint:
	poetry run flake8 .

check: format lint


test:
	poetry run pytest -v

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

badge:
	poetry run pytest --cov=app --cov-report=term-missing
	poetry run coverage-badge -o coverage.svg -f

help:
    @echo "Available commands:"
	@echo "  make install      - Install dependencies (Poetry)"
	@echo "  make run          - Run the server locally"
	@echo "  make format       - Format the code (Black)"
	@echo "  make lint         - Lint the code (Flake8)"
	@echo "  make check        - Run format and lint"
	@echo "  make test         - Run tests"
	@echo "  make docker-up    - Bring up Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make clean        - Clean up junk files"
	@echo "  make badge        - Badge for coverage"