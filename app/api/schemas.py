from typing import Any
from pydantic import BaseModel, Field


class ConsultaRequest(BaseModel):
    """Peticion del cliente para iniciar una tarea en el sistema multi-agente."""

    consulta: str = Field(
        ...,
        description="Consulta u orden de analisis de infraestructura y politicas",
        examples=["Analizar la infraestructura de ana.gomez@hotmail.com y calcular el ahorro con un 15% de descuento."],
    )


class TareaCreadaResponse(BaseModel):
    """Respuesta inmediata al encolar una tarea (HTTP 202 Accepted)."""

    task_id: str = Field(description="Identificador unico de la tarea encolada")
    job_id: str = Field(description="Alias de task_id para compatibilidad")
    status: str = Field(default="pending", description="Estado inicial de la tarea")
    mensaje: str = Field(description="Descripcion del resultado de encolado")


class AprobacionRequest(BaseModel):
    """Peticion para enviar la decision del operador humano (HITL)."""

    aprobado: bool = Field(
        default=True,
        description="True para autorizar la operacion comercial o False para rechazarla",
    )
    comentario: str = Field(
        default="Aprobado por el operador",
        description="Nota u observacion de la decision humana",
    )


class EstadoTareaResponse(BaseModel):
    """Respuesta con el estado completo y resultados de la tarea."""

    task_id: str
    job_id: str
    consulta: str
    status: str
    result: str | None = None
    error: str | None = None
    detalle_aprobacion: dict[str, Any] | None = None
    comentario_aprobacion: str | None = None
    datos_investigacion: dict[str, Any] | None = None
    politicas_rag: dict[str, Any] | None = None
    analisis_computo: dict[str, Any] | None = None
    validacion: dict[str, Any] | None = None
