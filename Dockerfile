ARG PYTHON_VERSION=3.11

# build stage
FROM python:${PYTHON_VERSION} AS builder

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock README.md /project/
COPY tqa/ /project/tqa

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


# run stage
FROM python:${PYTHON_VERSION}-slim as runtime

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/*/lib /project/pkgs

# retrieve executables
COPY --from=builder /project/__pypackages__/*/bin/* /bin/

# set command/entrypoint, adapt to fit your needs
ENTRYPOINT ["python", "-m", "tqa.cli"]
