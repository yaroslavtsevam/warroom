# syntax=docker/dockerfile:1
ARG PY_VERSION=3.12

##
# Build stage: build and install dependencies
##
FROM python:${PY_VERSION} AS builder

ARG VERSION=0.dev
ENV PDM_BUILD_SCM_VERSION=${VERSION}

WORKDIR /project

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm pdm-dockerize

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=pdm.lock,target=pdm.lock \
    --mount=type=cache,target=$HOME/.cache,uid=$UUID \
    pdm dockerize --prod -v

##
# Run stage: create the final runtime container
##
FROM python:${PY_VERSION} AS runtime

WORKDIR /app

# Fetch built dependencies
COPY --from=builder /project/dist/docker /app
# Copy needed files from your project (filter using `.dockerignore`)
COPY  . /app

ENTRYPOINT ["/app/entrypoint"]
CMD ["pdm run main.py"]



# build stage
#FROM python:3.12-slim-bookworm AS builder

# install PDM
#RUN pip install pdm

# copy files
#COPY pyproject.toml pdm.lock README.md main.py /project/
#COPY src/ /project/src

# install dependencies and project into the local packages directory
#WORKDIR /project
#RUN mkdir __pypackages__ && pdm sync --prod --no-editable


# run stage
#FROM python:3.12-slim-bookworm

# retrieve packages from build stage
#ENV PYTHONPATH=/project/pkgs
#COPY --from=builder /project/__pypackages__/3.12/lib /project/pkgs

# retrieve executables
#COPY --from=builder /project/__pypackages__/3.12/bin/* /bin/

# set command/entrypoint, adapt to fit your needs
#CMD [ "pdm", "run", "main.py"]

