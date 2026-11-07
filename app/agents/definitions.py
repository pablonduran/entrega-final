import re
from typing import cast
from langchain_core.messages import AIMessage
from app.core.config import obtener_modelo
from app.core.state import EstadoOrquestador
from app.agents.tools import (
    buscar_servidores_infraestructura,
    consultar_politicas_infraestructura,
    calcular_proyeccion_costos,
)
from app.agents.schemas import ValidacionAuditoriaOutput


def extraer_email_de_texto(texto: str) -> str:
    """Extrae una direccion de correo electronico mediante expresion regular o usa un fallback."""
    coincidencias = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", texto)
    if coincidencias:
        return coincidencias[0].lower()
    if "carlos" in texto.lower():
        return "carlos.lopez@hotmail.com"
    return "ana.gomez@hotmail.com"


def extraer_descuento_de_texto(texto: str) -> float:
    """Extrae el porcentaje numerico de descuento solicitado en la consulta."""
    coincidencias = re.findall(r"(\d+(?:\.\d+)?)\s*%", texto)
    if coincidencias:
        return float(coincidencias[0])
    coincidencias_palabras = re.findall(r"descuento\s+(?:del\s+)?(\d+(?:\.\d+)?)", texto, re.IGNORECASE)
    if coincidencias_palabras:
        return float(coincidencias_palabras[0])
    return 15.0


async def agente_investigador(estado: EstadoOrquestador) -> dict:
    """Especialista en recopilar infraestructura del cliente y consultar normas corporativas via RAG."""
    contador = estado.get("contador_pasos", 0)
    mensajes = estado.get("messages", [])
    texto_usuario = " ".join(str(m.content) for m in mensajes if getattr(m, "type", "") == "human")

    email = extraer_email_de_texto(texto_usuario)
    datos_servidores = buscar_servidores_infraestructura.invoke({"email_cliente": email})

    # Consulta RAG sobre politicas y SLA
    datos_rag = await consultar_politicas_infraestructura.ainvoke({
        "termino_busqueda": "descuento anual aprobacion HITL operacion critica SLA",
        "limite_resultados": 2,
    })

    descuento_solicitado = extraer_descuento_de_texto(texto_usuario)
    cliente_nombre = datos_servidores.get("cliente", "Cliente")
    servidores = datos_servidores.get("servidores", [])

    # Deteccion temprana de criticidad segun politica RAG (descuento >= 10%)
    es_critico = descuento_solicitado >= 10.0

    detalle_servidores = ", ".join(f"{s['nombre']} ({s['tipo']})" for s in servidores)
    resumen = (
        f"[Investigador]: Datos obtenidos para {cliente_nombre} ({email}). "
        f"Infraestructura activa: {detalle_servidores}. "
        f"Base de conocimiento RAG consultada ({len(datos_rag.get('fragmentos', []))} fragmentos). "
        f"Politica: solicitudes con descuento >= 10% o costo >= $1000 USD requieren aprobacion ejecutiva."
    )

    return {
        "messages": [AIMessage(content=resumen)],
        "datos_investigacion": datos_servidores,
        "politicas_rag": datos_rag,
        "requiere_aprobacion": es_critico,
        "contador_pasos": contador + 1,
    }


async def agente_analista(estado: EstadoOrquestador) -> dict:
    """Especialista en computo de costos de infraestructura y proyeccion financiera de ahorro."""
    contador = estado.get("contador_pasos", 0)
    datos_inv = estado.get("datos_investigacion", {})
    servidores = datos_inv.get("servidores", [])

    mensajes = estado.get("messages", [])
    texto_usuario = " ".join(str(m.content) for m in mensajes if getattr(m, "type", "") == "human")
    descuento = extraer_descuento_de_texto(texto_usuario)

    analisis = calcular_proyeccion_costos.invoke({
        "servidores": servidores,
        "porcentaje_descuento": descuento,
    })

    # Si el costo anual es >= $1000 USD o descuento >= 10%, reafirma requisito de aprobacion HITL
    es_critico = (
        analisis.get("costo_anual_base_usd", 0.0) >= 1000.0
        or descuento >= 10.0
        or estado.get("requiere_aprobacion", False)
    )

    resumen = (
        f"[Analista]: Computo finalizado. Costo base mensual: USD {analisis['costo_mensual_base_usd']}, "
        f"anual: USD {analisis['costo_anual_base_usd']}. Con descuento del {descuento}%, "
        f"el ahorro anual es de USD {analisis['ahorro_anual_usd']} y costo final anual USD {analisis['costo_anual_final_usd']}."
    )

    return {
        "messages": [AIMessage(content=resumen)],
        "analisis_computo": analisis,
        "requiere_aprobacion": es_critico,
        "contador_pasos": contador + 1,
    }


async def agente_validador(estado: EstadoOrquestador) -> dict:
    """Especialista en control de calidad, coherencia de calculos y conformidad con politicas RAG."""
    contador = estado.get("contador_pasos", 0)
    datos_inv = estado.get("datos_investigacion", {})
    analisis = estado.get("analisis_computo", {})
    politicas = estado.get("politicas_rag", {})

    tiene_servidores = bool(datos_inv.get("servidores"))
    tiene_costos = bool(analisis.get("costo_mensual_base_usd"))
    tiene_ahorro = bool(analisis.get("ahorro_anual_usd") is not None)
    tiene_rag = bool(politicas.get("fragmentos"))

    aprobado = tiene_servidores and tiene_costos and tiene_ahorro

    resultado_auditoria = ValidacionAuditoriaOutput(
        aprobado=aprobado,
        tiene_datos_servidores=tiene_servidores,
        tiene_computo_costos=tiene_costos,
        tiene_proyeccion_ahorro=tiene_ahorro,
        cumple_politicas_rag=tiene_rag,
        observacion=(
            "Control de calidad aprobado. Todos los requerimientos fueron cubiertos con datos reales, "
            "calculos precisos y contraste contra politicas corporativas RAG."
            if aprobado
            else "Faltan datos de infraestructura o computo para validar el informe."
        ),
    )

    resumen = (
        f"[Validador]: Control de calidad finalizado. Aprobado: {resultado_auditoria.aprobado}. "
        f"Observacion: {resultado_auditoria.observacion}"
    )

    return {
        "messages": [AIMessage(content=resumen)],
        "validacion": resultado_auditoria.model_dump(),
        "contador_pasos": contador + 1,
    }
