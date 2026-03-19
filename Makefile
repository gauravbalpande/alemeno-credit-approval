.PHONY: build up down restart logs migrate makemigrations test shell createsuperuser ingest-data lint

# ── Docker ──────────────────────────────────────────────
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

# ── Django ──────────────────────────────────────────────
migrate:
	docker-compose run --rm web python manage.py migrate

makemigrations:
	docker-compose run --rm web python manage.py makemigrations

test:
	docker-compose run --rm web python manage.py test --verbosity=2

shell:
	docker-compose run --rm web python manage.py shell

createsuperuser:
	docker-compose run --rm web python manage.py createsuperuser

collectstatic:
	docker-compose run --rm web python manage.py collectstatic --noinput

# ── Data Ingestion ──────────────────────────────────────
ingest-data:
	docker-compose run --rm web python manage.py ingest_data \
		--customers /app/backend/customer_data.xlsx \
		--loans /app/backend/loan_data.xlsx

# ── Utilities ───────────────────────────────────────────
health:
	curl -s http://localhost:8000/api/health/ | python3 -m json.tool

docs:
	@echo "Open http://localhost:8000/api/docs/ in your browser"
