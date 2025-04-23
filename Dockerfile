FROM python:3.13.1-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

COPY ./src ./src

COPY ./alembic ./alembic

COPY alembic.ini .

RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app","--host", "0.0.0.0", "--port", "8000"]
