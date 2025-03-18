FROM python:3.12.7
LABEL authors="agrytsai"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

RUN adduser --disabled-password --home /app user

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY . .

RUN mkdir -p /files/uploads

RUN adduser \
    --disabled-password \
    --no-create-home \
    fastapiuser

RUN chown -R fastapiuser:fastapiuser /app
RUN chmod -R 777 /app

USER fastapiuser

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
