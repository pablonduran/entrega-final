import logging
from langgraph.types import interrupt
from langchain_core.messages import AIMessage
from app.core.state import EstadoOrquestador

logger = logging.getLogger("intelligence.graph.hitl")


async def nodo_aprobacion_humana(estado: EstadoOrquestador) -> dict:
    """Nodo Human-in-the-Loop (HITL) que pausa la ejecucion para aprobacion externa.

    Se activa cuando una operacion es clasificada como critica (descuento >= 10%
    o costo anual >= $1000 USD segun politicas corporativas).
    """
    contador = estado.get("contador_pasos", 0)
    datos_inv = estado.get("datos_investigacion", {})
    analisis = estado.get("analisis_computo", {})

    cliente = datos_inv.get("cliente", "Cliente")
    descuento = analisis.get("porcentaje_descuento_aplicado", 0.0)
    costo_anual = analisis.get("costo_anual_base_usd", 0.0)

    # Solo interrumpe si requiere aprobacion y todavia no fue aprobado por humano
    if estado.get("requiere_aprobacion") and not estado.get("aprobado_por_humano"):
        payload_interrupcion = {
            "mensaje": (
                f"Se requiere aprobacion comercial para el descuento del {descuento}% "
                f"sobre costo anual de USD {costo_anual}."
            ),
            "cliente": cliente,
            "costo_anual_base_usd": costo_anual,
            "porcentaje_descuento": descuento,
            "accion_critica": "Aplicacion de descuento y contratacion anual de infraestructura cloud",
        }

        logger.info(f"Pausando grafo en HITL para cliente {cliente} ({descuento}% desc).")
        # interrupt() pausa el grafo en Redis y espera Command(resume=...)
        decision_humana = interrupt(payload_interrupcion)

        # Procesar respuesta recibida tras reanudar
        aprobado = False
        comentario = ""
        if isinstance(decision_humana, dict):
            aprobado = bool(decision_humana.get("aprobado", True))
            comentario = decision_humana.get("comentario", "Aprobado por el operador")
        elif isinstance(decision_humana, bool):
            aprobado = decision_humana
            comentario = "Aprobado" if aprobado else "Rechazado"

        msg = (
            f"[HITL]: Decision humana registrada: {'APROBADO' if aprobado else 'RECHAZADO'}. "
            f"Comentario: {comentario}"
        )

        return {
            "messages": [AIMessage(content=msg)],
            "aprobado_por_humano": aprobado,
            "motivo_aprobacion": comentario,
            "contador_pasos": contador + 1,
        }

    return {"contador_pasos": contador + 1}
