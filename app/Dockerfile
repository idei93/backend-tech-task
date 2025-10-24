FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.5

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
