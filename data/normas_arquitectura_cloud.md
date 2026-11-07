# Normas de Arquitectura Cloud, Computo e Infraestructura de Servidores

## 1. Familias de Computo Homologadas
- **Proposito General (`m5`, `m6i`)**: Equilibradas en vCPU y memoria (proporcion 1:4). Indicadas para capas intermedias, microservicios backend y brokers de mensajeria livianos.
- **Optimizadas para Memoria (`r5`, `r6g`, `db.m5.xlarge`, `cache.r5.large`)**: Proporcion de 1:8 entre vCPU y RAM. Obligatorias para motores de bases de datos relacionales, clusters de cache en memoria y orquestadores con alta tasa de operaciones concurrentes.
- **Optimizadas para Computo (`c5`, `c6i`)**: Para procesamiento por lotes, compilacion, inferencia matematica intensiva y transcoding.
- **Ráfaga de Computo (`t3`, `t4g`)**: Para ambientes de desarrollo, staging y microservicios con carga estacional moderada.

## 2. Estandares de Bases de Datos Relacionales (PostgreSQL)
- Toda aplicacion que procese transacciones financieras, informacion sensible o historiales debe emplear motores PostgreSQL administrados en instancias `db.m5.xlarge` o superior (minimo 4 vCPU y 16 GB de RAM).
- En cuentas con plan Enterprise Cloud:
  - Configuracion Multi-AZ activa obligatoria con replicacion sincrona en modo Hot Standby.
  - Al menos una replica de lectura dedicada (`Read Replica`) para desviar consultas analiticas y reportes, protegiendo el nodo maestro de bloqueos.
  - Almacenamiento SSD provisionado (io2) con un minimo de 500 GB y garantia de al menos 3,000 IOPS base escalables automaticamente hasta 20,000 IOPS.
  - Pooler de conexiones transaccional obligatorio (PgBouncer) con limite de 100 conexiones por pool para evitar agotamiento de descriptores de socket.

## 3. Capa de Aceleracion, Cache y Checkpoints (Redis)
- El almacenamiento en memoria temporal, la cola asincrona FIFO y los checkpoints de LangGraph se gestionan mediante clusters Redis en nodos `cache.r5.large` (minimo 2 vCPU y 13 GB de RAM).
- Politica de desalojo de memoria (`maxmemory-policy`): configurada en `volatile-lru` o `allkeys-lru` con umbral de seguridad al 75% de la memoria fisica instalada.
- Resiliencia y disponibilidad:
  - Snapshots RDB automatizados cada 15 minutos complementados con Append-Only File (AOF) en modo `everysec`.
  - Replicacion asincrona en al menos dos zonas de disponibilidad (Multi-AZ) con failover automatico en menos de 15 segundos sin interrupcion de servicio.
  - Latencia objetivo: percentil p99 inferior a 10 milisegundos en lecturas y escrituras.

## 4. Servidores de Aplicacion, Microservicios y APIs Asincronas (FastAPI)
- Los servicios web desarrollados con FastAPI y Uvicorn deben desplegarse en instancias contenerizadas (Docker y Kubernetes EKS).
- Dimensionamiento minimo de produccion: 2 vCPU y 4 GB de RAM (`t3.medium` para servicios secundarios, `m5.large` para orquestadores principales).
- Politica de escalado automatico (Horizontal Pod Autoscaler - HPA):
  - Umbral de disparo: utilizacion media de CPU superior al 70% o latencia de endpoint p95 superior a 250 milisegundos durante 3 minutos consecutivos.
  - Rango de escalado: minimo 2 pods para alta disponibilidad, maximo 10 pods por zona.
- Healthcheck probes obligatorios: `/health` como liveness probe y readiness probe con validacion de conectividad a Redis antes de recibir trafico de red.
