from langgraph.graph import StateGraph, START, END
from app.core.state import EstadoOrquestador
from app.graph.supervisor import ejecutar_supervisor
from app.agents.definitions import (
    agente_investigador,
    agente_analista,
    agente_validador,
)
from app.graph.hitl import nodo_aprobacion_humana


def enrutar_supervisor(estado: EstadoOrquestador) -> str:
    """Arista condicional que lee la decision del supervisor."""
    paso = estado.get("siguiente_paso", "investigador")
    if paso == "FIN":
        return END
    return paso


def construir_grafo_orquestador(checkpointer=None):
    """Construye y compila el grafo jerarquico multi-agente con persistencia."""
    builder = StateGraph(EstadoOrquestador)

    # 1. Registrar nodos
    builder.add_node("supervisor", ejecutar_supervisor)
    builder.add_node("investigador", agente_investigador)
    builder.add_node("analista", agente_analista)
    builder.add_node("hitl", nodo_aprobacion_humana)
    builder.add_node("validador", agente_validador)

    # 2. Conectar entrada al supervisor
    builder.add_edge(START, "supervisor")

    # 3. Arista condicional desde supervisor hacia los especialistas o salida
    builder.add_conditional_edges(
        "supervisor",
        enrutar_supervisor,
        {
            "investigador": "investigador",
            "analista": "analista",
            "hitl": "hitl",
            "validador": "validador",
            END: END,
        },
    )

    # 4. Retorno ciclico desde cada nodo hacia el supervisor
    builder.add_edge("investigador", "supervisor")
    builder.add_edge("analista", "supervisor")
    builder.add_edge("hitl", "supervisor")
    builder.add_edge("validador", "supervisor")

    # 5. Compilacion con el checkpointer provisto (ej. AsyncRedisSaver)
    return builder.compile(checkpointer=checkpointer)
