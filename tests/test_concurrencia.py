import asyncio
import time
import httpx
import numpy as np

URL_BASE = "http://127.0.0.1:8000"

CONSULTAS_PRUEBA = [
    "Analizar infraestructura de servidores de ana.gomez@hotmail.com y calcular ahorro con 15% de descuento anual segun politicas corporativas.",
    "Consultar servidores cloud de carlos.lopez@hotmail.com y calcular costo anual con 10% de descuento y verificacion SLA.",
    "Revision tecnica y financiera para ana.gomez@hotmail.com proyectando 20% de descuento anual y auditoria de alta disponibilidad.",
    "Evaluar costos de servidores de carlos.lopez@hotmail.com con 5% de descuento corporativo y politicas de backups.",
    "Auditoria integral de servidores de ana.gomez@hotmail.com aplicando 15% de descuento por compromiso anual y revision de politicas RAG.",
]


async def monitorear_tarea(client: httpx.AsyncClient, task_id: str, indice: int) -> dict:
    """Realiza sondeo (polling) de una tarea hasta que termine o requiera aprobacion."""
    inicio = time.perf_counter()
    while True:
        res = await client.get(f"{URL_BASE}/tasks/{task_id}")
        datos = res.json()
        estado = datos.get("status")

        if estado == "waiting_approval":
            # Auto-aprobar para completar el flujo end-to-end de prueba
            print(f"[{indice}] Tarea {task_id[:8]} en espera de aprobacion (HITL). Aprobando...")
            await client.post(
                f"{URL_BASE}/tasks/{task_id}/approve",
                json={"aprobado": True, "comentario": "Aprobado por el operador en prueba de carga"},
            )

        if estado in ("completed", "rejected", "failed"):
            duracion = time.perf_counter() - inicio
            print(f"[{indice}] Tarea {task_id[:8]} finalizo con estado: {estado} ({duracion:.2f}s)")
            return {
                "indice": indice,
                "task_id": task_id,
                "status": estado,
                "duracion_segundos": duracion,
                "resultado": datos.get("result"),
                "error": datos.get("error"),
            }

        await asyncio.sleep(2)


async def enviar_peticion_concurrente(
    client: httpx.AsyncClient, consulta: str, indice: int
) -> dict:
    """Envia una solicitud POST /tasks y monitorea su resolucion asincrona."""
    inicio_post = time.perf_counter()
    res = await client.post(f"{URL_BASE}/tasks", json={"consulta": consulta})
    tiempo_post = (time.perf_counter() - inicio_post) * 1000

    if res.status_code != 202:
        print(f"[{indice}] Error al encolar: {res.status_code} - {res.text}")
        return {
            "indice": indice,
            "status": "error_encolado",
            "duracion_segundos": 0.0,
        }

    task_id = res.json()["task_id"]
    print(f"[{indice}] Solicitud encolada en {tiempo_post:.1f}ms -> ID: {task_id}")
    return await monitorear_tarea(client, task_id, indice)


async def main():
    print("=================================================================")
    print("INICIANDO PRUEBA DE CARGA CON 5 PETICIONES CONCURRENTES (SISTEMA FINAL)")
    print("=================================================================\n")

    inicio_global = time.perf_counter()
    async with httpx.AsyncClient(timeout=600.0) as client:
        tareas = [
            enviar_peticion_concurrente(client, consulta, i + 1)
            for i, consulta in enumerate(CONSULTAS_PRUEBA)
        ]
        resultados = await asyncio.gather(*tareas)

    tiempo_total = time.perf_counter() - inicio_global
    duraciones = [r["duracion_segundos"] for r in resultados if r.get("duracion_segundos", 0) > 0]
    completadas = sum(1 for r in resultados if r.get("status") == "completed")

    print("\n=================================================================")
    print("RESULTADOS DE LA PRUEBA DE CONCURRENCIA")
    print("=================================================================")
    print(f"Peticiones completadas: {completadas} / {len(CONSULTAS_PRUEBA)}")
    print(f"Tiempo total de la prueba: {tiempo_total:.2f}s")

    if duraciones:
        p50 = np.percentile(duraciones, 50)
        p90 = np.percentile(duraciones, 90)
        p95 = np.percentile(duraciones, 95)
        promedio = np.mean(duraciones)
        minimo = np.min(duraciones)
        maximo = np.max(duraciones)

        print(f"Latencia promedio: {promedio:.2f}s")
        print(f"Latencia p50 (mediana): {p50:.2f}s")
        print(f"Latencia p90: {p90:.2f}s")
        print(f"Latencia p95: {p95:.2f}s")
        print(f"Latencia minima: {minimo:.2f}s")
        print(f"Latencia maxima: {maximo:.2f}s")
    print("=================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
