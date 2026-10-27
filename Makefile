COMPOSE = docker compose
MANAGE = $(COMPOSE) run --rm backend python manage.py

.PHONY: up down clean logs ps shell migrate superuser test fmt lint

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f backend

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec backend python manage.py shell

migrate: up
	@echo "== taDB (postgres)"
	@$(MANAGE) migrate --noinput
	@echo "== tsDB (clickhouse)"
	@$(MANAGE) migrate --noinput --database=tsdb

superuser:
	$(MANAGE) createsuperuser

test:
	$(COMPOSE) --profile test run --build --rm tests

fmt:
	poetry run ruff format .
	poetry run ruff check --fix .

lint:
	poetry run ruff format --check .
	poetry run ruff check .
