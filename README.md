# Table-QA

Code for the task  DataBench, Question-Answering over Tabular Data challenge for the SemEval 2025

Detailed descrition of the code and results can be found in the paper <url>


# INSTALL
```
conda activate py11
python3 -m venv venv
source venv/bin/activate
pip install pdm
pdm install -G dev -G test
pip install pre-commit
pre-commit install

```

## configure .env
Add a .env file to the root of the proyect and add a OPENAI key as:
```
OPENAI_API_KEY="your_openai_key_here"
```

## Overview

Description in more detail than the intro

Musts content that the overview section should contain:
- Name of the project to which this module belongs (provided it makes sense and is not simply the name of the company)
- Input data that is handled and data that is generated with the module (on a business level, not technical)
- Indicate submodules if they exist
- List of functionalities


## Usage

### Installation (optional)

The way to install this project is via Docker, so the `docker` command must be available to the current user.

Once this is done, the image needs to be present locally. If it is available in a registry, you can pull it using:

```bash
docker pull <URL to image>
```

Do note that with private registries you have to log in first using `docker login <URL of the registry>`.

If the image is not in a registry, or you want to build it, refer to the [Docker](#docker) section inside [Development](#development).


### Configuration (optional)

Any configuration can be changed modifying the files that appear below `env_file` in the `tools/docker/docker-compose.yml` file. You may also want to point to another file, or include more.


### Run

To run the aplication, you can use the `tools/docker/docker-compose.yml` file. This is how to do it:

```bash
cd tools/docker/
docker compose up
```

Optionally, you can add `-d` at the end of the last command to run it in the background.



## Development

### Requirements

This project has been developed using Python 3 and [PDM](https://pdm.fming.dev). 
So, `python3` is required.

Dependencies are managed through the PDM tool, which you can install as follows (or via [any other official method](https://pdm.fming.dev/latest/#installation)):

```bash
curl -sSL https://pdm.fming.dev/install-pdm.py | python3 -
```

PDM will detect if it's running in a virtual environment and use it, or create one in the `.venv` directory if it isn't.

There's a `Makefile` file included in this project, which can be used to perform actions with just one simple command. The `make` command must be available in order to use it.

Additionally, this project uses pre-commit hooks to check code quality and format before it's finally committed to the repository. **You must configure the pre-commit hooks to evaluate your code**, follow these steps:

1. Install the pre-commit utility: `make install-dev`
2. Run the following command in the root directory : `pdm run pre-commit install`
3. Done.

You have [more info about pre-commit hooks in the `docs` folder](./docs/pre_commit_hooks.md).

### Dependencies

All required Python packages may be installed using the command:

```bash
make install-dev
```

This will install all the app's dependencies, as well as the development and testing ones. Any new requirement must be added using the `pdm add <dependency>` command.


### Configuration

External configuration is handled using **environment variables** and [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/).
An example env file is provided with the name `example.env`. You can rename it to `.env` and the app will pick it up automatically when running locally.
**Do not bake env files into Docker images or commit them to version control**.

Read more about this in [the external configuration page](/docs/external_config.md).

### Run

To run the program without installing it, use the following command:

```bash
make run
```


### Docker

The `Makefile` can also be used to build a Docker image. The `docker` command must be available to the current user:

```bash
make docker-build
```

To run said image in development mode use the following command, replacing `<command>` with one of the options available in `tqa.cli`:

```bash
make docker-run-dev COMMAND=<command>
```

The `Makefile` contains many other commands for different situations, so it's worth to be familiar with it.


### Tests

```bash
# All tests
make test

# All tests with coverage reports
make test-cov

# All tests verbose mode (not encouraged use logging module instead)
pdm run pytest -s --log-cli-level=INFO

# Unit tests
pdm run pytest -s --log-cli-level=INFO tests/unit

# Validation tests
pdm run pytest -s --log-cli-level=INFO tests/validation
```


To run the *tests/system/test_column_descriptor.py* test you will need an open AI token. Export the environment key 

```
export OPENAI_API_KEY=<your api key>
```

This test will generate a column description from the different tables

```
pytest tests/system/test_column_descriptor.py
```

This test generates a file *table_result.json* with the descriptions of the columns of the tables.


### Scaffolding

- **tqa**: contains the source code.
- **.github/workflows**: contains the CI/CD tasks defined by Gradiant during this project's development.
- **tools**: tools and utilities to help in the execution of the service.

---

**_This project was developed by [Gradiant](https://www.gradiant.org)._**

## License
This repository is licensed under the Mozilla Public License v2.0 - see the [LICENSE](LICENSE) file for details
