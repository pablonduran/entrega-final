from typing import Literal, TypedDict
from langgraph.graph import MessagesState

DestinoRuta = Literal["investigador", "analista", "validador", "hitl", "FIN"]


class EstadoOrquestador(MessagesState):
    """Esquema de estado tipado global para el orquestador multi-agente."""

    siguiente_paso: DestinoRuta
    datos_investigacion: dict
    politicas_rag: dict
    analisis_computo: dict
    validacion: dict
    requiere_aprobacion: bool
    aprobado_por_humano: bool
    motivo_aprobacion: str
    tarea_completada: bool
    contador_pasos: int
    historial_delegaciones: list[str]
    error: str | None
