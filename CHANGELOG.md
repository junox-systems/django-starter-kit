# Changelog

## [0.3.0](https://github.com/junox-systems/django-starter-kit/compare/v0.2.0...v0.3.0) (2026-08-08)


### Features

* add AWS_S3_ENDPOINT_URL for S3-compatible storage backends ([a8b8a87](https://github.com/junox-systems/django-starter-kit/commit/a8b8a874f2b5eae3a58022fb7bc0f4cd3262e0a1))
* add clickstack observability to dev compose with analytics profile ([341ac64](https://github.com/junox-systems/django-starter-kit/commit/341ac64c01b3fc29a0f0b942ebc1f1b04144a17a))
* add docker swarm stack file replacing root compose ([678ffce](https://github.com/junox-systems/django-starter-kit/commit/678ffce470c0706b4e5c1e515bc55008325467a6))
* add generic Stimulus controller for Svelte mounting ([e3a41f2](https://github.com/junox-systems/django-starter-kit/commit/e3a41f2d01d750e50e9381baa679b90bf696e8e8))
* add prod entrypoint script with db wait + migrate ([835c71b](https://github.com/junox-systems/django-starter-kit/commit/835c71b8d5fcaa724beebff47d7b87335df7863a))
* add rustfs S3 service to dev compose ([b4bfd9b](https://github.com/junox-systems/django-starter-kit/commit/b4bfd9bcf4bcc348e47b242f118bc6844aa4b298))
* add swarm stack targets and analytics profile shortcut to Makefile ([22674f7](https://github.com/junox-systems/django-starter-kit/commit/22674f75177ac56554c2cb6d02ec77c49e15ad64))
* configurable otel log level per environment ([a07ef3d](https://github.com/junox-systems/django-starter-kit/commit/a07ef3d76615e18cd1a4cb3d5a27187fafc0f9ea))
* remove htmx — Django forms + Stimulus + Svelte islands replace it ([7564c2e](https://github.com/junox-systems/django-starter-kit/commit/7564c2efaa83cd3f576b322f3bec12fa6baf5f06))
* rewrite prod Dockerfile as multi-stage almalinux:10-kitten-minimal with uv-only ([6405e72](https://github.com/junox-systems/django-starter-kit/commit/6405e72bb9f818084d56432d2d02a2d1112cddf8))


### Bug Fixes

* add S3 partial config warning, widen hash regex, document CONN_MAX_AGE ([21a9777](https://github.com/junox-systems/django-starter-kit/commit/21a97775aee5d8d4f18f04962f291e718966b3af))
* add settings guard in asgi.py, fix Makefile prod-start ([126c259](https://github.com/junox-systems/django-starter-kit/commit/126c25967331bb451218b32a26d72530aa04532f))
* address final review findings — swarm depends_on list, OTEL_ENABLED, stack-deploy IMAGE_NAME, settings module env, worker healthcheck, init.sh probe ([1f9d807](https://github.com/junox-systems/django-starter-kit/commit/1f9d8071bc018b4df33833ec907df7ee06abe9f6))
* clean DMR_SETTINGS override, document SSL/HSTS setup ([e29655b](https://github.com/junox-systems/django-starter-kit/commit/e29655be3fd938a6c0ca83438bdcfaf863e7fa87))
* clickstack local mode — no login required ([7ea53bf](https://github.com/junox-systems/django-starter-kit/commit/7ea53bf84e81bed77613571fa26c506d25802989))
* link frontend traces to backend via asgi middleware ([566c3a9](https://github.com/junox-systems/django-starter-kit/commit/566c3a95f065eb709cfa9dd78c082ebf0456fc7a))
* remove .env requirement, dev uses filesystem storage ([af3e6ec](https://github.com/junox-systems/django-starter-kit/commit/af3e6eca749f9819fdf1719b372c7330f1a16af3))
* resolve verification issues ([e8de5b8](https://github.com/junox-systems/django-starter-kit/commit/e8de5b804b83f2c841db682a2187caf0ff1b526c))
* slim runtime stage to uv+python only, dockerignore staticfiles ([d22c8c4](https://github.com/junox-systems/django-starter-kit/commit/d22c8c43fef471e4b164510fbfefb799654e3ea7))
* update Dockerfile to python:3.14-slim ([8e63c8b](https://github.com/junox-systems/django-starter-kit/commit/8e63c8b7c7a231c84e752090560e493774fa26da))


### Documentation

* add AGENTS.md for AI agents, symlink CLAUDE.md -&gt; AGENTS.md ([374793a](https://github.com/junox-systems/django-starter-kit/commit/374793aa8e28c13379e4c28c2316caf14cb200e1))
* add harden & slim design spec ([5a7da8b](https://github.com/junox-systems/django-starter-kit/commit/5a7da8bed1292600e33bbdba0ba91ed59304bb7e))
* add implementation plan for harden-and-slim ([b7bb9b0](https://github.com/junox-systems/django-starter-kit/commit/b7bb9b03c2503cdad4ebf84c722c71a1b30f2590))
* amend plan — fix rustfs healthcheck endpoint, bucket init, .env note ([b4cd6e9](https://github.com/junox-systems/django-starter-kit/commit/b4cd6e949469e6674bf9c651fc60336323b92cec))
* document username/email normalization rationale in User model ([0f182c2](https://github.com/junox-systems/django-starter-kit/commit/0f182c258018296a0cf082067f32e824aa877116))
* mark harden-and-slim plan complete ([e09fcf4](https://github.com/junox-systems/django-starter-kit/commit/e09fcf4194242ee6fbaf4d56bed4a889e5d0e726))
* update DEVELOPMENT.md — remove htmx references, document svelte-bridge ([e353b01](https://github.com/junox-systems/django-starter-kit/commit/e353b010c8b26943cf028cd7d595fda99d84fd05))
* update README for harden-and-slim changes ([2ff4e8b](https://github.com/junox-systems/django-starter-kit/commit/2ff4e8b94587d432b03cbee336e67266bf0600f8))
* update README for rustfs, clickstack, swarm stack ([bc5bfba](https://github.com/junox-systems/django-starter-kit/commit/bc5bfbabb3fb836d5f6ddcd446cf1c1df73caf41))

## [0.2.0](https://github.com/junox-systems/django-starter-kit/compare/v0.1.0...v0.2.0) (2026-05-14)


### Features

* django-unfold ([67dea2b](https://github.com/junox-systems/django-starter-kit/commit/67dea2b2963b28096c2381732c820e19bcc82f21))
* replace Django REST Framework with Django Modern REST (DMR) for API development ([317d41e](https://github.com/junox-systems/django-starter-kit/commit/317d41e8411f9bf0070cb998d70e500b98fc1df1))
* replace Django REST Framework with dmr for API controllers and OpenAPI generation ([2914f38](https://github.com/junox-systems/django-starter-kit/commit/2914f38f558429a642445365436449fda32e63c4))
* svelte v5 init ([aac2663](https://github.com/junox-systems/django-starter-kit/commit/aac2663cd6cc94dd7cd9fe7cb9095aef11a914fa))
* update project minimum Python requirement to 3.14 ([af3255f](https://github.com/junox-systems/django-starter-kit/commit/af3255f19b23b3054e3e07d007fda1b8311aacfa))
* upgrade frontend pkgs ([438351d](https://github.com/junox-systems/django-starter-kit/commit/438351d60df953bb933abfbad417d14c2867dc1f))
* use uuid v7 ([12184d3](https://github.com/junox-systems/django-starter-kit/commit/12184d32e5d169d211a0c1d0eb275af4d4a0d00b))

## 0.1.0 (2025-08-27)


### Features

* add turbo helper, enable turbo globally, work with debug toolbar ([6c7c7b7](https://github.com/junoxlabs/django-starter-kit/commit/6c7c7b7bcd1317429f31f35eca1d1bc9dac93b9e))
* dev compose for db, rabbitmq, s3 and redis ([7d47877](https://github.com/junoxlabs/django-starter-kit/commit/7d47877481bad5e2d7fb8d00d4dc0f0d97b89731))
* improved BRIEF.md ([4182b4f](https://github.com/junoxlabs/django-starter-kit/commit/4182b4f8bd41d91d029acdc8bb5768308cd7c4b6))
* integrate opentelemetry ([89879e3](https://github.com/junoxlabs/django-starter-kit/commit/89879e3c017bcc2a585883cfc2159aa100cd7d83))
* makefile, uvloop for async in granian ([cd5aac5](https://github.com/junoxlabs/django-starter-kit/commit/cd5aac534c3aaefe8ad09761a5e21e025b75cfbf))
* more useful users model ([55b3625](https://github.com/junoxlabs/django-starter-kit/commit/55b3625a8614aaa26efee0f1d8deed150023444d))
* pages app for pages ([9bf1f0b](https://github.com/junoxlabs/django-starter-kit/commit/9bf1f0bbf63c4e0c7740d0566d2c96ea0ae1c671))
* reproducible dev environment; docs; ([52cf1a6](https://github.com/junoxlabs/django-starter-kit/commit/52cf1a6ca6a36078cbb636d2455e48ecb0fa0a07))
* update psycopg to v3 ([39e211b](https://github.com/junoxlabs/django-starter-kit/commit/39e211b200c237acc358b5200b0dcaa6f0666cd7))
* upgrade frontend to latest ([727e3c9](https://github.com/junoxlabs/django-starter-kit/commit/727e3c9cb27f55fbef2fe2c4b2e5e9cb6d3f0869))
* vite, frontend working on prod and dev ([e234027](https://github.com/junoxlabs/django-starter-kit/commit/e234027d2fe85903938d2b5d7e6dbea2eb708c72))
* working django init ([40db5ef](https://github.com/junoxlabs/django-starter-kit/commit/40db5ef096c4568c297f9a04654eaaf63e12e8ea))


### Bug Fixes

* debug_toolbar on prod, 400 error on prod ([929707f](https://github.com/junoxlabs/django-starter-kit/commit/929707fa206c358b05aef2b6ba657f4bb2253326))
* dependencies on dev environment (docker) not working ([b30ef41](https://github.com/junoxlabs/django-starter-kit/commit/b30ef41ee139e567e2a0763e541a0b013bf64b21))
* django-vite, vite working on dev server ([1ef4a96](https://github.com/junoxlabs/django-starter-kit/commit/1ef4a96e1d7c78fecf4bf1ad656e763cc93bec34))
* fmt; versions; paradedb instead of base pg ([8288b3b](https://github.com/junoxlabs/django-starter-kit/commit/8288b3b7883d71d2b8ca6783a65f705a381283f8))
* stop turbo drive, vite auto import controllers ([7649298](https://github.com/junoxlabs/django-starter-kit/commit/7649298221b22232f4b002649ec7898d6f7b91e9))
