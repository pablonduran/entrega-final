"""Suite de pruebas unitarias y de integracion del Sistema Intelligence.

Verifica la ingesta y recuperacion del RAG, los calculos de las herramientas
validadas con Pydantic, la estructura del grafo LangGraph y los contratos de la API.
"""

import asyncio
import unittest
from app.rag.ingesta import cargar_documentos_politicas
from app.rag.retriever import consultar_politicas_rag
from app.agents.tools import (
    buscar_servidores_infraestructura,
    calcular_proyeccion_costos,
)
from app.graph.builder import construir_grafo_orquestador
from app.api.schemas import ConsultaRequest, AprobacionRequest


class TestSistemaIntelligence(unittest.TestCase):

    def test_carga_documentos_rag(self):
        """Verifica que los documentos normativos en data/ se lean y fragmenten."""
        documentos = cargar_documentos_politicas()
        self.assertGreater(len(documentos), 0, "No se cargaron fragmentos de politicas en data/")
        fuentes = {d.metadata.get("fuente") for d in documentos}
        self.assertIn("politicas_sla_descuentos.md", fuentes)
        self.assertIn("normas_arquitectura_cloud.md", fuentes)
        self.assertIn("politica_backups_seguridad.md", fuentes)
        self.assertIn("finops_optimizacion_costos.md", fuentes)

    def test_recuperacion_rag(self):
        """Verifica que el recuperador BM25 devuelva fragmentos relevantes."""
        resultado = asyncio.run(consultar_politicas_rag("descuento anual y aprobacion HITL", top_k=2))
        self.assertGreater(resultado["coincidencias"], 0)
        self.assertGreater(len(resultado["fragmentos"]), 0)
        self.assertIn("politicas_sla_descuentos.md", resultado["fuentes_consultadas"])

    def test_herramienta_buscar_servidores(self):
        """Verifica la herramienta de busqueda de servidores con validacion Pydantic."""
        resultado = buscar_servidores_infraestructura.invoke({"email_cliente": "ana.gomez@hotmail.com"})
        self.assertIn("servidores", resultado)
        self.assertEqual(len(resultado["servidores"]), 2)
        self.assertEqual(resultado["plan"], "Enterprise Cloud")

        resultado_inexistente = buscar_servidores_infraestructura.invoke({"email_cliente": "noexiste@test.com"})
        self.assertIn("error", resultado_inexistente)

    def test_herramienta_calcular_costos(self):
        """Verifica el calculo financiero de costos por hora, mensuales y anuales con descuento."""
        servidores_mock = [
            {"id_servidor": "s1", "nombre": "DB", "tipo": "db.m5", "costo_hora_usd": 0.38},
            {"id_servidor": "s2", "nombre": "Cache", "tipo": "cache.r5", "costo_hora_usd": 0.16},
        ]
        calculo = calcular_proyeccion_costos.invoke({
            "servidores": servidores_mock,
            "porcentaje_descuento": 15.0,
        })

        self.assertEqual(calculo["costo_total_hora_usd"], 0.54)
        self.assertEqual(calculo["costo_mensual_base_usd"], 388.8)
        self.assertEqual(calculo["costo_anual_base_usd"], 4665.6)
        self.assertEqual(calculo["ahorro_anual_usd"], 699.84)
        self.assertEqual(calculo["costo_anual_final_usd"], 3965.76)

    def test_construccion_grafo_langgraph(self):
        """Verifica la compilacion y topologia del grafo jerarquico."""
        grafo = construir_grafo_orquestador()
        nodos_esperados = {"__start__", "supervisor", "investigador", "analista", "hitl", "validador"}
        self.assertTrue(nodos_esperados.issubset(set(grafo.nodes.keys())))

    def test_contratos_pydantic_api(self):
        """Verifica la validacion de modelos de entrada y salida de la API."""
        req_consulta = ConsultaRequest(consulta="Auditoria para ana.gomez@hotmail.com con 15% desc")
        self.assertIn("ana.gomez@hotmail.com", req_consulta.consulta)

        req_aprobacion = AprobacionRequest(aprobado=True, comentario="Autorizado por direccion")
        self.assertTrue(req_aprobacion.aprobado)
        self.assertEqual(req_aprobacion.comentario, "Autorizado por direccion")


if __name__ == "__main__":
    unittest.main()
