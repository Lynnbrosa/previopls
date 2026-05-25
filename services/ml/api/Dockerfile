FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r app && useradd -r -g app -u 1001 app

COPY --chown=app:app app/ ./app/
COPY --chown=app:app models/ ./models/

# Gera um modelo padrão se não houver pkl real disponível.
# Em produção, monte um volume ou faça COPY com o ml_model.pkl exportado do notebook.
RUN if [ ! -f /app/models/ml_model.pkl ]; then \
        python -m app.build_default_model; \
    fi \
 && chown -R app:app /app/models

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
