#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  INICIANDO THE INTELLIGENCE SYSTEM (ENTREGA FINAL)"
echo "========================================================"

# 1. Verificar archivo .env
if [ ! -f .env ]; then
    echo "[AVISO] No se encontro el archivo .env. Copiando desde .env.example..."
    cp .env.example .env
    echo "Por favor configura tus API keys en .env antes de continuar."
fi

# 2. Intentar levantar via Docker Compose si Docker esta instalado
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "[DOCKER] Iniciando servicios con Docker Compose..."
    docker compose up --build
    exit $?
fi

# 3. Fallback de ejecucion local con Python y Uvicorn
echo "[FALLBACK LOCAL] Docker no disponible. Iniciando en entorno virtual local..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
