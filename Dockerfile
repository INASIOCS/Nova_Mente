# NovaMente — imagem única que serve a interface Streamlit OU a API FastAPI.
# Escolha o serviço pela variável de ambiente SERVICE ("ui" ou "api").
#
# Essa escolha permite usar a MESMA imagem para os dois serviços no Railway e,
# mais tarde, para o deploy em uma instância OCI Compute Always Free.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    SERVICE=ui \
    PORT=8080

WORKDIR /app

# Dependências de sistema: build-essential é necessário para parte do stack de
# RAG; curl serve ao healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential

COPY app ./app
COPY ui ./ui
COPY scripts ./scripts
COPY docs ./docs
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh \
    && mkdir -p storage_local

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/_stcore/health" \
     || curl -fsS "http://localhost:${PORT}/saude" \
     || exit 1

CMD ["./entrypoint.sh"]
