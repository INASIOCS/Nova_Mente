#!/bin/sh
# Entrypoint do NovaMente.
#
# SERVICE=ui   -> interface Streamlit (padrão; é o que o avaliador abre)
# SERVICE=api  -> API REST FastAPI
#
# A porta vem de $PORT, como exigem Railway e a maioria dos PaaS.

set -e

PORT="${PORT:-8080}"
SERVICE="${SERVICE:-ui}"

echo "NovaMente: iniciando serviço '${SERVICE}' na porta ${PORT}"

case "${SERVICE}" in
  api)
    exec uvicorn app.api.main:app --host 0.0.0.0 --port "${PORT}"
    ;;
  ui)
    exec streamlit run ui/app.py \
      --server.port "${PORT}" \
      --server.address 0.0.0.0 \
      --server.headless true \
      --browser.gatherUsageStats false
    ;;
  *)
    echo "SERVICE inválido: '${SERVICE}'. Use 'ui' ou 'api'." >&2
    exit 1
    ;;
esac
