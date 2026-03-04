.PHONY: install generate up down test lint fmt alembic-up alembic-rev

install:
	poetry install

run: generate
	$$env:PYTHONPATH='src;generated/src'; poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

generate:
	npx openapi-generator-cli generate -i /local/openapi/marketplace.yaml -g python-fastapi -o /local/generated --additional-properties=packageName=marketplace_gen,sourceFolder=src,fastapiImplementationPackage=impl

up:
	docker-compose up --build

down:
	docker-compose down -v

test:
	poetry run pytest -q

lint:
	poetry run ruff check .

fmt:
	poetry run ruff format .

alembic-up:
	poetry run alembic upgrade head

alembic-rev:
	poetry run alembic revision --autogenerate -m "migration"