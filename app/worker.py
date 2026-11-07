import asyncio
import json
import logging
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from app.core.config import (
    obtener_cliente_redis,
    REDIS_URL,
    QUEUE_NAME,
    PREFIJO_ESTADO,
)
from app.graph.builder import construir_grafo_orquestador

logger = logging.getLogger("intelligence.worker")


async def procesar_tarea_individual(task_id: str):
    """Procesa una tarea individual extrayendola de la cola y ejecutando el grafo multi-agente."""
    clave_estado = f"{PREFIJO_ESTADO}{task_id}"
    redis_client = obtener_cliente_redis()

    try:
        datos_crudos = await redis_client.get(clave_estado)
        if not datos_crudos:
            logger.error(f"No se encontro el estado inicial para la tarea {task_id}")
            return

        estado_tarea = json.loads(datos_crudos)
        consulta = estado_tarea.get("consulta", "")

        # 1. Cambiar estado a 'processing'
        estado_tarea["status"] = "processing"
        await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))

        # 2. Conectar checkpointer persistente en Redis
        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as saver:
            grafo = construir_grafo_orquestador(checkpointer=saver)
            configuracion = {
                "configurable": {"thread_id": task_id},
                "recursion_limit": 20,
            }

            estado_inicial = {
                "messages": [HumanMessage(content=consulta)],
                "siguiente_paso": "investigador",
                "datos_investigacion": {},
                "politicas_rag": {},
                "analisis_computo": {},
                "validacion": {},
                "requiere_aprobacion": False,
                "aprobado_por_humano": False,
                "motivo_aprobacion": "",
                "tarea_completada": False,
                "contador_pasos": 0,
                "historial_delegaciones": [],
                "error": None,
            }

            # 3. Ejecutar grafo asincronamente
            async for _ in grafo.astream(estado_inicial, configuracion):
                pass

            # 4. Inspeccionar estado resultante del grafo
            estado_grafo = await grafo.aget_state(configuracion)

            # Verificar si se detuvo en una interrupcion Human-in-the-Loop (HITL)
            interrupciones = []
            for tarea in estado_grafo.tasks:
                if tarea.interrupts:
                    for intr in tarea.interrupts:
                        interrupciones.append(intr.value)

            if interrupciones:
                logger.info(f"Tarea {task_id} pausada en espera de aprobacion humana (HITL).")
                estado_tarea["status"] = "waiting_approval"
                estado_tarea["detalle_aprobacion"] = interrupciones[0]
                await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))
                return

            # Flujo completado sin interrupcion
            valores = estado_grafo.values
            ultimos_mensajes = valores.get("messages", [])
            texto_resultado = (
                ultimos_mensajes[-1].content
                if ultimos_mensajes
                else "Tarea completada exitosamente."
            )

            estado_tarea["status"] = "completed"
            estado_tarea["result"] = texto_resultado
            estado_tarea["datos_investigacion"] = valores.get("datos_investigacion", {})
            estado_tarea["politicas_rag"] = valores.get("politicas_rag", {})
            estado_tarea["analisis_computo"] = valores.get("analisis_computo", {})
            estado_tarea["validacion"] = valores.get("validacion", {})

            await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))
            logger.info(f"Tarea {task_id} finalizada exitosamente con estado 'completed'.")

    except Exception as error:
        logger.exception(f"Error critico al procesar la tarea {task_id}: {error}")
        estado_tarea["status"] = "failed"
        estado_tarea["error"] = str(error)
        await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))
    finally:
        await redis_client.aclose()


async def reanudar_tarea_aprobada(task_id: str, aprobado: bool, comentario: str) -> dict:
    """Reanuda un hilo de LangGraph detenido en interrupt() con la decision humana enviada."""
    clave_estado = f"{PREFIJO_ESTADO}{task_id}"
    redis_client = obtener_cliente_redis()

    try:
        async with AsyncRedisSaver.from_conn_string(REDIS_URL) as saver:
            grafo = construir_grafo_orquestador(checkpointer=saver)
            configuracion = {
                "configurable": {"thread_id": task_id},
                "recursion_limit": 20,
            }

            comando_reanudacion = Command(
                resume={"aprobado": aprobado, "comentario": comentario}
            )

            # Reanudar ejecucion del grafo
            async for _ in grafo.astream(comando_reanudacion, configuracion):
                pass

            estado_grafo = await grafo.aget_state(configuracion)
            valores = estado_grafo.values
            ultimos_mensajes = valores.get("messages", [])
            texto_resultado = (
                ultimos_mensajes[-1].content
                if ultimos_mensajes
                else "Proceso completado tras aprobacion humana."
            )

            datos_crudos = await redis_client.get(clave_estado)
            estado_tarea = json.loads(datos_crudos) if datos_crudos else {}

            estado_tarea["status"] = "completed" if aprobado else "rejected"
            estado_tarea["result"] = texto_resultado
            estado_tarea["comentario_aprobacion"] = comentario
            estado_tarea["datos_investigacion"] = valores.get("datos_investigacion", {})
            estado_tarea["politicas_rag"] = valores.get("politicas_rag", {})
            estado_tarea["analisis_computo"] = valores.get("analisis_computo", {})
            estado_tarea["validacion"] = valores.get("validacion", {})

            await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))
            logger.info(f"Tarea {task_id} reanudada y finalizada con exito.")
            return estado_tarea

    except Exception as error:
        logger.exception(f"Error al reanudar la tarea {task_id}: {error}")
        datos_crudos = await redis_client.get(clave_estado)
        estado_tarea = json.loads(datos_crudos) if datos_crudos else {}
        estado_tarea["status"] = "failed"
        estado_tarea["error"] = str(error)
        await redis_client.set(clave_estado, json.dumps(estado_tarea, ensure_ascii=False))
        return estado_tarea
    finally:
        await redis_client.aclose()


async def bucle_worker(evento_detener: asyncio.Event):
    """Bucle principal del worker que desencola tareas en Redis con operacion blpop no bloqueante."""
    logger.info(f"Worker en segundo plano iniciado. Escuchando cola '{QUEUE_NAME}'...")
    redis_client = obtener_cliente_redis()

    try:
        while not evento_detener.is_set():
            try:
                # blpop con timeout de 1 segundo para chequear evento_detener
                resultado = await redis_client.blpop([QUEUE_NAME], timeout=1)
                if resultado:
                    _, task_id = resultado
                    logger.info(f"Worker recibio tarea: {task_id}")
                    await procesar_tarea_individual(task_id)
            except Exception as error:
                if not evento_detener.is_set():
                    logger.error(f"Error en bucle_worker: {error}")
                    await asyncio.sleep(1)
    finally:
        await redis_client.aclose()
        logger.info("Worker en segundo plano detenido.")
