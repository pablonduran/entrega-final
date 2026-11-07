import logging
from typing import cast
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from app.core.config import obtener_modelo
from app.core.state import EstadoOrquestador, DestinoRuta

logger = logging.getLogger("intelligence.graph.supervisor")


class DecisionDelegacion(BaseModel):
    """Modelo Pydantic para la decision estructurada del Supervisor."""

    siguiente_paso: DestinoRuta = Field(
        description="Agente a delegar ('investigador', 'analista', 'hitl', 'validador') o 'FIN' si esta concluido"
    )
    motivo: str = Field(description="Explicacion breve y directa del motivo de la eleccion")


async def ejecutar_supervisor(estado: EstadoOrquestador) -> dict:
    """Nodo Supervisor central que orquesta el flujo, consulta al LLM y sintetiza el reporte."""
    contador = estado.get("contador_pasos", 0)

    # Limite estricto de pasos para evitar bucles infinitos
    if contador >= 15:
        msg = AIMessage(
            content="[Supervisor]: Se alcanzo el limite de pasos de seguridad. Procediendo al cierre del flujo."
        )
        return {
            "messages": [msg],
            "siguiente_paso": "FIN",
            "tarea_completada": True,
        }

    datos_inv = estado.get("datos_investigacion", {})
    analisis = estado.get("analisis_computo", {})
    val = estado.get("validacion", {})
    requiere_hitl = estado.get("requiere_aprobacion", False)
    aprobado_humano = estado.get("aprobado_por_humano", False)

    modelo = obtener_modelo()

    prompt_supervisor = SystemMessage(
        content=(
            "Sos el Supervisor del Sistema Intelligence de auditoria de infraestructura cloud. "
            "Tu tarea es evaluar el estado de la tarea y decidir que especialista debe intervenir: "
            "1. 'investigador': si aun no se investigaron los servidores del cliente ni las politicas RAG. "
            "2. 'analista': si ya tenemos investigacion pero falta calcular costos y ahorros. "
            "3. 'hitl': si la operacion es critica (costo >= $1000 USD o desc >= 10%) y aun no tiene aprobacion humana. "
            "4. 'validador': si tenemos datos y calculos, pero aun no fueron auditados. "
            "5. 'FIN': si la validacion fue aprobada y corresponde emitir el informe final. "
            "Responde estrictamente con la estructura solicitada."
        )
    )

    historial_texto = []
    for m in estado["messages"]:
        rol = "Usuario" if getattr(m, "type", "") == "human" else "Agente"
        historial_texto.append(f"{rol}: {m.content}")

    texto_resumen = (
        "Historial reciente:\n"
        + "\n".join(historial_texto[-4:])
        + f"\n\nEstado de datos actual:\n"
        + f"- Investigacion completada: {bool(datos_inv.get('servidores'))}\n"
        + f"- Computo de costos completado: {bool(analisis.get('costo_mensual_base_usd'))}\n"
        + f"- Requiere aprobacion HITL: {requiere_hitl} (Aprobado: {aprobado_humano})\n"
        + f"- Validacion aprobada: {bool(val.get('aprobado'))}\n\n"
        + "¿A que especialista corresponde delegar ahora o corresponde FIN?"
    )
    mensaje_evaluacion = HumanMessage(content=texto_resumen)

    modelo_estructurado = modelo.with_structured_output(DecisionDelegacion)
    resultado_raw = await modelo_estructurado.ainvoke([prompt_supervisor, mensaje_evaluacion])
    decision = cast(DecisionDelegacion, resultado_raw)

    destino: DestinoRuta = decision.siguiente_paso

    # Salvaguarda logica determinista
    if not datos_inv.get("servidores"):
        destino = "investigador"
    elif not analisis.get("costo_mensual_base_usd"):
        destino = "analista"
    elif requiere_hitl and not aprobado_humano:
        destino = "hitl"
    elif not val.get("aprobado"):
        destino = "validador"
    else:
        destino = "FIN"

    historial = list(estado.get("historial_delegaciones", []))
    historial.append(f"supervisor->{destino}")

    # Si el flujo finaliza, sintetizar informe final
    if destino == "FIN":
        cliente_nombre = datos_inv.get("cliente", "el cliente")
        cliente_email = datos_inv.get("email", "")
        plan = datos_inv.get("plan", "Standard")
        servidores = datos_inv.get("servidores", [])
        detalle_servidores = ", ".join(f"{s['nombre']} ({s['tipo']})" for s in servidores)

        costo_mensual = analisis.get("costo_mensual_base_usd", 0.0)
        costo_anual = analisis.get("costo_anual_base_usd", 0.0)
        descuento = analisis.get("porcentaje_descuento_aplicado", 0.0)
        ahorro = analisis.get("ahorro_anual_usd", 0.0)
        costo_final = analisis.get("costo_anual_final_usd", 0.0)

        estado_hitl = (
            "aprobada por el operador humano (HITL)"
            if aprobado_humano
            else "sin requerimiento de aprobacion adicional"
        )

        respuesta_sintetizada = (
            f"Informe tecnico y financiero para {cliente_nombre} ({cliente_email}), con plan {plan}. "
            f"Infraestructura activa: {detalle_servidores}. "
            f"El costo operativo base es de USD {costo_mensual} mensuales, totalizando USD {costo_anual} al ano. "
            f"Con el descuento del {descuento}% por compromiso anual ({estado_hitl}), "
            f"el ahorro anual es de USD {ahorro}, dejando un costo anual final de USD {costo_final}."
        )

        mensaje_final = AIMessage(content=respuesta_sintetizada)
        return {
            "messages": [mensaje_final],
            "siguiente_paso": "FIN",
            "tarea_completada": True,
            "contador_pasos": contador + 1,
            "historial_delegaciones": historial,
        }

    mensaje_delegacion = AIMessage(
        content=f"[Supervisor]: Delegando siguiente tarea a '{destino}'. Motivo: {decision.motivo}"
    )

    return {
        "messages": [mensaje_delegacion],
        "siguiente_paso": destino,
        "tarea_completada": False,
        "contador_pasos": contador + 1,
        "historial_delegaciones": historial,
    }
