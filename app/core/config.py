import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr
import redis.asyncio as aioredis

load_dotenv()

# Rutas del proyecto
DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent.parent
DIRECTORIO_DATA = DIRECTORIO_RAIZ / "data"

# Configuracion de Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = os.getenv("QUEUE_NAME", "cola_tareas_intelligence")
PREFIJO_ESTADO = "tarea:"
REDIS_CLUSTER_MODE = os.getenv("REDIS_CLUSTER_MODE", "false").lower() == "true"

# Observabilidad (Arize Phoenix / OpenInference)
PHOENIX_COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
PHOENIX_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "sistema-intelligence-produccion")

# Configuracion del Servidor API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))


def obtener_cliente_redis() -> aioredis.Redis:
    """Retorna un cliente asincrono de Redis."""
    return aioredis.from_url(REDIS_URL, decode_responses=True)


def obtener_modelo():
    """Instancia y retorna el modelo de lenguaje configurado con tipos estrictos."""
    proveedor = os.getenv("LLM_PROVIDER", "gemini").lower()
    temperatura = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    if proveedor == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        modelo = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
        clave = os.getenv("GEMINI_API_KEY")
        if not clave or clave.startswith("tu_"):
            raise ValueError("Falta configurar GEMINI_API_KEY en el archivo .env")
        return ChatGoogleGenerativeAI(model=modelo, google_api_key=SecretStr(clave))

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic
        modelo = os.getenv("LLM_MODEL", "claude-3-5-haiku-latest")
        clave = os.getenv("ANTHROPIC_API_KEY")
        if not clave or clave.startswith("tu_"):
            raise ValueError("Falta configurar ANTHROPIC_API_KEY en el archivo .env")
        return ChatAnthropic(
            model_name=modelo,
            api_key=SecretStr(clave),
            temperature=temperatura,
            timeout=None,
            stop=None,
        )

    from langchain_openai import ChatOpenAI
    modelo = os.getenv("LLM_MODEL", "gpt-4o-mini")
    clave = os.getenv("OPENAI_API_KEY")
    if not clave or clave.startswith("tu_"):
        raise ValueError("Falta configurar OPENAI_API_KEY en el archivo .env")
    return ChatOpenAI(model=modelo, api_key=SecretStr(clave), temperature=temperatura)
