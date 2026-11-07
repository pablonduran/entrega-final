import json
import logging
import uuid
from fastapi import APIRouter, HTTPException, status
from app.core.config import obtener_cliente_redis, QUEUE_NAME, PREFIJO_ESTADO
from app.api.schemas import (
    ConsultaRequest,
    TareaCreadaResponse,
    AprobacionRequest,
    EstadoTareaResponse,
)
from app.worker import reanudar_tarea_aprobada

logger = logging.getLogger("intelligence.api.routes")
router = APIRouter()


@router.get("/health", tags=["Salud"])
async def health_check():
    """Verifica el estado del servicio y la conexion con Redis."""
    redis_client = obtener_cliente_redis()
    try:
        ping = await redis_client.ping()
        return {"status": "ok", "redis": "connected" if ping else "disconnected"}
    except Exception as error:
        return {"status": "degraded", "redis_error": str(error)}
    finally:
        await redis_client.aclose()


@router.post(
    "/tasks",
    response_model=TareaCreadaResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Tareas"],
)
async def crear_tarea(solicitud: ConsultaRequest):
    """Encola una nueva tarea en Redis y retorna inmediatamente un task_id sin bloquear el hilo principal."""
    task_id = str(uuid.uuid4())
    clave_estado = f"{PREFIJO_ESTADO}{task_id}"

    registro_inicial = {
        "task_id": task_id,
        "job_id": task_id,
        "consulta": solicitud.consulta,
        "status": "pending",
        "result": None,
        "error": None,
    }

    redis_client = obtener_cliente_redis()
    try:
        # 1. Guardar estado inicial como 'pending'
        await redis_client.set(clave_estado, json.dumps(registro_inicial, ensure_ascii=False))

        # 2. Encolar el identificador en la cola FIFO de Redis
        await redis_client.rpush(QUEUE_NAME, task_id)
        logger.info(f"Tarea encolada con ID {task_id}")

        return TareaCreadaResponse(
            task_id=task_id,
            job_id=task_id,
            status="pending",
            mensaje="Tarea encolada exitosamente para procesamiento asincrono.",
        )
    finally:
        await redis_client.aclose()


@router.get("/tasks/{task_id}", tags=["Tareas"])
async def obtener_estado_tarea(task_id: str):
    """Consulta el estado actual de una tarea en Redis mediante sondeo (polling)."""
    clave_estado = f"{PREFIJO_ESTADO}{task_id}"
    redis_client = obtener_cliente_redis()
    try:
        datos_crudos = await redis_client.get(clave_estado)
        if not datos_crudos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontro ninguna tarea con el identificador '{task_id}'.",
            )
        return json.loads(datos_crudos)
    finally:
        await redis_client.aclose()


@router.post("/tasks/{task_id}/approve", tags=["Human-in-the-Loop"])
async def aprobar_tarea(task_id: str, decision: AprobacionRequest):
    """Reanuda la ejecucion de una tarea que se encuentra pausada esperando aprobacion humana (HITL)."""
    clave_estado = f"{PREFIJO_ESTADO}{task_id}"
    redis_client = obtener_cliente_redis()

    try:
        datos_crudos = await redis_client.get(clave_estado)
        if not datos_crudos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontro ninguna tarea con el identificador '{task_id}'.",
            )

        estado = json.loads(datos_crudos)
        if estado.get("status") != "waiting_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La tarea no esta esperando aprobacion. Estado actual: '{estado.get('status')}'.",
            )
    finally:
        await redis_client.aclose()

    # Reanudar la ejecucion asincrona con la decision humana
    resultado_final = await reanudar_tarea_aprobada(
        task_id=task_id,
        aprobado=decision.aprobado,
        comentario=decision.comentario,
    )

    return resultado_final
