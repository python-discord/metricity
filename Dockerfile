FROM --platform=linux/amd64 ghcr.io/chrislovering/python-poetry-base:3.10-slim

ENV PYTHONHASHSEED=random

# Install Dependencies
WORKDIR /metricity
COPY poetry.lock pyproject.toml ./
RUN poetry install


COPY . /metricity
CMD ["bash", "entry_point.sh"]
