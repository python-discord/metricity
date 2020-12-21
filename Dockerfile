FROM python:slim

RUN apt update
RUN apt install -y gcc git

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN pip install poetry

WORKDIR /metricity
COPY poetry.lock pyproject.toml /metricity/

RUN poetry config virtualenvs.create false && poetry install

COPY . /metricity

CMD ["sh", "-c", "alembic upgrade head && poetry run start"]
