BASE_PROJECT_NAME := myproject
PROJECT_NAME := tqa
DOCKER_IMAGE_TAG := $(BASE_PROJECT_NAME)/$(PROJECT_NAME)
DOCKER_CONTAINER_NAME := $(BASE_PROJECT_NAME)-$(PROJECT_NAME)

install-dev:  ## install package in "editable" mode with dev and test dependencies
	pdm install -G dev -G test

install-test:  ## install package in "editable" mode with only test dependencies
	pdm install -G test

install:  ## install standalone package
	pdm install --prod

test:  ## run tests
	pdm run pytest -sv tests

test-cov:  ## run tests with coverage reports (for Jenkins)
	pdm run pytest --cov tqa \
		-o junit_family=xunit2 -o cache_dir=/tmp \
		--cov-report term-missing \
		--cov-report xml:./reports/coverage.xml --junitxml=./reports/junit-result.xml \
		-sv tests

run:  ## Run on host
	pdm run python -m tqa.cli --help

docker-build: ## run docker build to create docker image
	docker build . -t $(DOCKER_IMAGE_TAG)

docker-run-dev: ## run docker image in dev mode (with network=host and using the local .env)
	docker run --rm --net=host --env-file .env --name $(DOCKER_CONTAINER_NAME) -t $(DOCKER_IMAGE_TAG) $(COMMAND)

docker-clean: ## remove docker image
	docker rmi $(DOCKER_IMAGE_TAG) || exit 0

help:  ## This help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
