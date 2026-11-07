import asyncio
from langchain_core.tools import tool
from app.agents.schemas import (
    BuscarServidoresInput,
    ConsultarPoliticasInput,
    CalcularCostosInput,
)
from app.rag.retriever import consultar_politicas_rag

# Catalogo corporativo de clientes e infraestructura activa
CATALOGO_SERVIDORES = {
    "ana.gomez@hotmail.com": {
        "cliente": "Ana Gomez",
        "email": "ana.gomez@hotmail.com",
        "plan": "Enterprise Cloud",
        "servidores": [
            {
                "id_servidor": "srv-prod-db",
                "nombre": "Base de datos PostgreSQL Principal",
                "tipo": "db.m5.xlarge",
                "vcpu": 4,
                "ram_gb": 16,
                "almacenamiento_gb": 500,
                "costo_hora_usd": 0.38,
            },
            {
                "id_servidor": "srv-cache-redis",
                "nombre": "Cluster Redis Cache",
                "tipo": "cache.r5.large",
                "vcpu": 2,
                "ram_gb": 13,
                "almacenamiento_gb": 50,
                "costo_hora_usd": 0.16,
            },
        ],
    },
    "carlos.lopez@hotmail.com": {
        "cliente": "Carlos Lopez",
        "email": "carlos.lopez@hotmail.com",
        "plan": "Standard Startup",
        "servidores": [
            {
                "id_servidor": "srv-app-api",
                "nombre": "Servidor API FastAPI",
                "tipo": "t3.medium",
                "vcpu": 2,
                "ram_gb": 4,
                "almacenamiento_gb": 80,
                "costo_hora_usd": 0.08,
            }
        ],
    },
}


@tool(args_schema=BuscarServidoresInput)
def buscar_servidores_infraestructura(email_cliente: str) -> dict:
    """Consulta la infraestructura de servidores cloud contratada por un cliente segun su email.

    Devuelve la lista detallada de servidores activos, especificaciones tecnicas (vCPU, RAM, disco)
    y el costo por hora en dolares de cada maquina.
    """
    email_limpio = email_cliente.strip().lower()
    if email_limpio in CATALOGO_SERVIDORES:
        return CATALOGO_SERVIDORES[email_limpio]
    return {
        "error": f"No se encontro infraestructura registrada para el email {email_cliente}.",
        "servidores": [],
    }


@tool(args_schema=ConsultarPoliticasInput)
async def consultar_politicas_infraestructura(
    termino_busqueda: str, limite_resultados: int = 2
) -> dict:
    """Consulta la base de conocimiento corporativa via RAG sobre politicas de SLA, descuentos y arquitectura.

    Recupera fragmentos oficiales para validar limites comerciales, requerimientos de aprobacion
    humana (HITL) y normas de alta disponibilidad.
    """
    return await consultar_politicas_rag(termino_busqueda, top_k=limite_resultados)


@tool(args_schema=CalcularCostosInput)
def calcular_proyeccion_costos(
    servidores: list[dict], porcentaje_descuento: float = 0.0
) -> dict:
    """Calcula el costo operativo por hora, mensual (720 horas) y anual (8640 horas) de la infraestructura.

    Aplica el porcentaje de descuento indicado sobre el compromiso anual y retorna el ahorro resultante.
    """
    costo_hora_total = sum(float(s.get("costo_hora_usd", 0.0)) for s in servidores)
    costo_mensual_base = round(costo_hora_total * 720.0, 2)
    costo_anual_base = round(costo_hora_total * 8640.0, 2)

    factor_descuento = float(porcentaje_descuento) / 100.0
    ahorro_anual = round(costo_anual_base * factor_descuento, 2)
    costo_anual_final = round(costo_anual_base - ahorro_anual, 2)
    costo_mensual_final = round(costo_anual_final / 12.0, 2)

    return {
        "costo_total_hora_usd": round(costo_hora_total, 4),
        "costo_mensual_base_usd": costo_mensual_base,
        "costo_anual_base_usd": costo_anual_base,
        "porcentaje_descuento_aplicado": round(float(porcentaje_descuento), 2),
        "ahorro_anual_usd": ahorro_anual,
        "costo_anual_final_usd": costo_anual_final,
        "costo_mensual_final_usd": costo_mensual_final,
    }
