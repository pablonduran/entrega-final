from pydantic import BaseModel, Field, EmailStr


class BuscarServidoresInput(BaseModel):
    """Esquema de validacion de entrada para la busqueda de infraestructura de un cliente."""

    email_cliente: str = Field(
        ...,
        description="Direccion de correo electronico valida del cliente a consultar",
        examples=["ana.gomez@hotmail.com"],
    )


class ConsultarPoliticasInput(BaseModel):
    """Esquema de validacion de entrada para consultar las politicas y SLA corporativos via RAG."""

    termino_busqueda: str = Field(
        ...,
        description="Terminos clave o pregunta sobre SLA, limites de descuento o arquitectura cloud",
        examples=["descuento anual y aprobacion HITL"],
    )
    limite_resultados: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Numero maximo de fragmentos a recuperar del RAG",
    )


class ServidorIndividual(BaseModel):
    id_servidor: str = Field(description="Identificador unico del servidor")
    nombre: str = Field(description="Nombre descriptivo del servicio")
    tipo: str = Field(description="Tipo de instancia cloud")
    costo_hora_usd: float = Field(ge=0.0, description="Costo operativo por hora en USD")


class CalcularCostosInput(BaseModel):
    """Esquema de validacion de entrada para el calculo financiero de infraestructura."""

    servidores: list[dict] = Field(
        ...,
        description="Lista de servidores con sus especificaciones y costo por hora",
    )
    porcentaje_descuento: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Porcentaje de descuento comercial solicitado",
    )


class ValidacionAuditoriaOutput(BaseModel):
    """Esquema de salida de auditoria y control de calidad del Validador."""

    aprobado: bool = Field(description="Indica si la informacion y los calculos superan la auditoria")
    tiene_datos_servidores: bool = Field(description="Confirmacion de presencia de datos de infraestructura")
    tiene_computo_costos: bool = Field(description="Confirmacion de computo de costos base y anuales")
    tiene_proyeccion_ahorro: bool = Field(description="Confirmacion del calculo del ahorro proyectado")
    cumple_politicas_rag: bool = Field(description="Indica si se revisaron las politicas corporativas RAG")
    observacion: str = Field(description="Resumen explicativo de la auditoria")
