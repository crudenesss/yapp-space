FROM python:3.12-slim AS build

WORKDIR /app

RUN pip install poetry==2.4.0

COPY pyproject.toml poetry.lock ./

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN poetry install --only main --no-root 

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN DEBIAN_FRONTEND=noninteractive apt update -y \
    && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends libmagic1 libmagic-dev

ARG USERNAME=app
ARG UID=1000
ARG GID=$UID

ARG PP_PATH=/profile_pictures

RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID $USERNAME

RUN chown -R $USERNAME:$USERNAME /app

RUN mkdir $PP_PATH && chmod -R 700 $PP_PATH && chown -R $USERNAME:$USERNAME $PP_PATH

USER $USERNAME

COPY --from=build --chown=$USERNAME:$USERNAME /app/.venv/ ./.venv/

COPY --chown=${USERNAME}:${USERNAME} ./entrypoint.sh .
    
COPY --chown=$USERNAME:$USERNAME ./src .

ENTRYPOINT [ "sh", "./entrypoint.sh" ]
