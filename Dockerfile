FROM python:3.12-slim

# Evitar generacion de archivos .pyc y forzar buffer de stdout/stderr inmediato
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codigo fuente y datos de la aplicacion
COPY . .

EXPOSE 8000

# Iniciar servidor FastAPI y worker en segundo plano mediante el lifespan
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
