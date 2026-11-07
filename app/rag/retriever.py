import asyncio
import logging
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.rag.ingesta import cargar_documentos_politicas

logger = logging.getLogger("intelligence.rag.retriever")

_retriever_instancia = None
_documentos_cache: list[Document] = []


def obtener_recuperador():
    """Retorna o inicializa el recuperador semantico/lexico BM25 con los documentos de data/."""
    global _retriever_instancia, _documentos_cache

    if _retriever_instancia is not None:
        return _retriever_instancia

    _documentos_cache = cargar_documentos_politicas()
    if not _documentos_cache:
        # Documento base de contingencia si la carpeta estuviera vacia
        _documentos_cache = [
            Document(
                page_content="Politica de descuentos: Todo descuento superior al 10% requiere aprobacion HITL.",
                metadata={"fuente": "politicas_base.md", "chunk_id": "base#0"},
            )
        ]

    _retriever_instancia = BM25Retriever.from_documents(_documentos_cache, k=2)
    logger.info(f"Recuperador RAG inicializado con {len(_documentos_cache)} fragmentos indexados.")
    return _retriever_instancia


async def consultar_politicas_rag(consulta: str, top_k: int = 2) -> dict:
    """Busca asincronamente fragmentos relevantes de politicas y normas corporativas."""
    recuperador = obtener_recuperador()
    recuperador.k = top_k

    # Ejecucion no bloqueante mediante to_thread si la llamada es CPU-bound
    documentos = await asyncio.to_thread(recuperador.invoke, consulta)

    fragmentos = []
    fuentes = set()
    for doc in documentos:
        fragmentos.append({
            "contenido": doc.page_content,
            "fuente": doc.metadata.get("fuente", "desconocido"),
            "chunk_id": doc.metadata.get("chunk_id", ""),
        })
        fuentes.add(doc.metadata.get("fuente", "desconocido"))

    return {
        "consulta": consulta,
        "coincidencias": len(fragmentos),
        "fragmentos": fragmentos,
        "fuentes_consultadas": sorted(list(fuentes)),
    }
