.PHONY: install test lint format run

install:
	python -m pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

run:
	uvicorn src.api.main:app --reload
