.PHONY: test
test:
	@set -e; \
	trap 'docker compose -p bank-tests -f infra/docker-compose.test.yaml down' EXIT; \
	docker compose -p bank-tests -f infra/docker-compose.test.yaml up -d --wait; \
	python -m coverage run -m pytest -v tests; \
	python -m coverage report --rcfile=.coveragerc

.PHONY: format
format:
	ruff format .

.PHONY: build
build:
	docker build . -t nova -f infra/build/Dockerfile