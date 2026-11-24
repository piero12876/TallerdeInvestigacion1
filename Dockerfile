FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY requirements.lock .
RUN pip install --no-cache-dir --only-binary :all: --require-hashes -r requirements.lock

COPY backend ./backend
COPY frontend ./frontend
COPY ml ./ml
COPY run.py .

RUN mkdir -p data ml && chown -R appuser:appuser /app

USER appuser

EXPOSE 3939

CMD ["python", "run.py"]
