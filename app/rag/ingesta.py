import logging
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import DIRECTORIO_DATA

logger = logging.getLogger("intelligence.rag.ingesta")


def cargar_documentos_politicas() -> list[Document]:
    """Carga y fragmenta todos los documentos tecnicos y de politicas en data/."""
    documentos_totales = []

    if not DIRECTORIO_DATA.exists():
        logger.warning(f"El directorio de datos '{DIRECTORIO_DATA}' no existe.")
        return documentos_totales

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n- ", "\n\n", "\n", " "],
    )

    archivos_md = list(DIRECTORIO_DATA.glob("*.md"))
    for archivo in archivos_md:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido = f.read()

            nombre_fuente = archivo.name
            chunks = splitter.split_text(contenido)
            for idx, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk.strip(),
                    metadata={
                        "fuente": nombre_fuente,
                        "chunk_id": f"{nombre_fuente}#{idx}",
                    },
                )
                documentos_totales.append(doc)
            logger.info(f"Cargado {nombre_fuente}: {len(chunks)} fragmentos.")
        except Exception as error:
            logger.error(f"Error al leer '{archivo}': {error}")

    return documentos_totales
