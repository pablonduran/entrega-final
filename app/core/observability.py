import logging
import os
from app.core.config import PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME

logger = logging.getLogger("intelligence.observability")
_observabilidad_inicializada = False


def inicializar_observabilidad() -> bool:
    """Inicializa la instrumentacion OpenInference y registro OTLP con Arize Phoenix."""
    global _observabilidad_inicializada
    if _observabilidad_inicializada:
        return True

    try:
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        # Configurar TracerProvider global hacia Arize Phoenix
        tracer_provider = register(
            project_name=PHOENIX_PROJECT_NAME,
            endpoint=PHOENIX_COLLECTOR_ENDPOINT,
            set_global_tracer_provider=True,
        )

        # Instrumentar llamadas de LangChain y LangGraph
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        _observabilidad_inicializada = True
        logger.info(
            f"Observabilidad activa: Arize Phoenix en '{PHOENIX_PROJECT_NAME}' ({PHOENIX_COLLECTOR_ENDPOINT})"
        )
        return True
    except Exception as error:
        logger.warning(f"Aviso al inicializar observabilidad con Arize Phoenix: {error}")
        return False
