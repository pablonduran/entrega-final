import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from app.core.config import REDIS_URL
from app.core.observability import inicializar_observabilidad
from app.rag.retriever import obtener_recuperador
from app.worker import bucle_worker
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("intelligence.main")

evento_detener_worker = asyncio.Event()
tarea_worker_background = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de FastAPI: inicializa observabilidad, esquemas en Redis, RAG y el worker."""
    global tarea_worker_background

    logger.info("=== INICIANDO SISTEMA INTELLIGENCE DE PRODUCCION ===")

    # 1. Inicializar observabilidad con Arize Phoenix
    inicializar_observabilidad()

    # 2. Inicializar base de conocimiento RAG (BM25 y documentos)
    try:
        obtener_recuperador()
        logger.info("Modulo RAG precargado exitosamente.")
    except Exception as error:
        logger.warning(f"Aviso al precargar el modulo RAG: {error}")

    # 3. Configurar indices de AsyncRedisSaver para LangGraph en Redis
    try:
        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as saver:
            await saver.asetup()
        logger.info("Esquemas de AsyncRedisSaver verificados correctamente en Redis.")
    except Exception as error:
        logger.warning(f"Aviso al configurar AsyncRedisSaver en Redis: {error}")

    # 4. Iniciar el worker en segundo plano
    evento_detener_worker.clear()
    tarea_worker_background = asyncio.create_task(bucle_worker(evento_detener_worker))

    yield

    # Shutdown limpio
    logger.info("Deteniendo servicios del Sistema Intelligence...")
    evento_detener_worker.set()
    if tarea_worker_background:
        tarea_worker_background.cancel()
        try:
            await tarea_worker_background
        except asyncio.CancelledError:
            pass
    logger.info("=== SISTEMA INTELLIGENCE DETENIDO DE FORMA SEGURA ===")


app = FastAPI(
    title="The Intelligence System - AI Engineering",
    description=(
        "Sistema Intelligence de grado de produccion que integra RAG corporativo, "
        "orquestacion multi-agente con Supervisor, persistencia en Redis (AsyncRedisSaver), "
        "observabilidad activa con Arize Phoenix y flujo Human-in-the-Loop."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    from app.core.config import API_HOST, API_PORT

    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=False)
