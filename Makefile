MAKEFLAGS += -j4

.PHONY: install i 
install i: deps-django deps-frontend
	@echo "Installation complete. You can now run the project."

.PHONY: deps-django
deps-django:
	uv sync

.PHONY: deps-frontend
deps-frontend:
	cd frontend && pnpm install

.PHONY: clean
clean:
	rm -rf .venv frontend/node_modules

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: lint-fix
lint-fix:
	uv run ruff check . --fix

.PHONY: format
format:
	uv run ruff format .

.PHONY: test
test:
	DJANGO_SETTINGS_MODULE=config.settings.test uv run pytest

#### DOCKER DEV #### -----------------------------------------------------------------------------
.PHONY: dev-up dev
dev-up dev:
	docker compose -f dev/docker-compose.dev.yml up --build -d

# Same stack minus analytics (no clickstack): db, redis, s3, app
.PHONY: dev-slim
dev-slim:
	docker compose -f dev/docker-compose.dev.yml up -d --build db redis s3 app

.PHONY: dev-down dev-stop
dev-down dev-stop stop:
	docker compose -f dev/docker-compose.dev.yml down

.PHONY: dev-clean
dev-clean:
	docker compose -f dev/docker-compose.dev.yml down -v

.PHONY: dev-restart restart
dev-restart restart:
	make dev-down
	make dev-up

.PHONY: dev-logs
dev-logs logs:
	docker compose -f dev/docker-compose.dev.yml logs -f

.PHONY: dev-ps
dev-ps ps:
	docker compose -f dev/docker-compose.dev.yml ps

.PHONY: dev-bash bash
dev-bash bash:
	docker compose -f dev/docker-compose.dev.yml exec app bash

.PHONY: dev-shell shell
dev-shell shell:
	docker compose -f dev/docker-compose.dev.yml exec app uv run python manage.py shell -v 2

dev-createsuperuser:
	docker compose -f dev/docker-compose.dev.yml exec app env DJANGO_SUPERUSER_PASSWORD=admin uv run python manage.py createsuperuser --noinput --username admin --email admin@example.com

## - END DOCKER DEV - ## -------------------------------------------------------------------------

#### - DEV commands - #### ---------------------------------------------------------------------------
.PHONY: django-dev
django-dev:
	DJANGO_SETTINGS_MODULE=config.settings.dev uv run python manage.py runserver 0.0.0.0:8000

.PHONY: vite-dev
vite-dev:
	cd frontend && pnpm run dev --host 0.0.0.0 --port 5173

.PHONY: worker-dev
worker-dev:
	DJANGO_SETTINGS_MODULE=config.settings.dev uv run celery -A config worker -l info

.PHONY: beat-dev
beat-dev:
	DJANGO_SETTINGS_MODULE=config.settings.dev uv run celery -A config beat -l info

.PHONY: makemigrations make migrations
makemigrations make migrations:
	uv run python manage.py makemigrations

.PHONY: migrate 
migrate:
	uv run python manage.py migrate
## - END DEV - ## ---------------------------------------------------------------------------

#### - BUILD - #### ------------------------------------------------------------------------------
.PHONY: vite-build
vite-build:
	cd frontend && pnpm run build

.PHONY: docker-build
docker-build:
	docker build -t django-starter-kit .
## - END BUILD - ## -------------------------------------------------------------------------------

### - PROD - ### ---------------------------------------------------------------------------------
.PHONY: collectstatic
collectstatic:
	uv run python manage.py collectstatic --no-input --clear

.PHONY: prod-start
prod-start:
	env DJANGO_SETTINGS_MODULE=config.settings.production ENVIRONMENT=production uv run granian \
		--interface asginl \
		--workers 3 \
		--runtime-mode mt \
	--loop uvloop \
		--host 0.0.0.0 \
		--port 8000 \
		config.asgi:application 

## - END PROD - ## -------------------------------------------------------------------------------

#### - STACK - #### ------------------------------------------------------------------------------
.PHONY: stack-build
stack-build:
	docker build -t django-starter-kit .

.PHONY: stack-deploy
stack-deploy:
	docker stack deploy -c docker-stack.yml django-starter-kit

.PHONY: stack-rm
stack-rm:
	docker stack rm django-starter-kit

.PHONY: stack-logs
stack-logs:
	docker service logs -f django-starter-kit_web

.PHONY: stack-ps
stack-ps:
	docker stack services django-starter-kit
## - END STACK - ##

# deploy:
# 	# This target is for deployment, which is not part of the automated CI/CD pipeline.
# 	# Add your deployment commands here if you need to deploy manually.
# 	echo "Deployment is not automated in CI/CD. Please deploy manually if needed."
