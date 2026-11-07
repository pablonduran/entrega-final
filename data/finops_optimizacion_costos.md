# Guia FinOps: Optimizacion de Costes Cloud, Rightsizing y Gobernanza

## 1. Principios del Marco FinOps Corporativo
- La gestion del gasto en la nube se rige por el principio de visibilidad total, responsabilidad compartida y optimizacion continua.
- Todo recurso aprovisionado debe contar obligatoriamente con etiquetas de asignacion de costos (`Cost Allocation Tags`):
  - `Environment`: `production`, `staging` o `development`.
  - `CostCenter`: centro de costo contable asignado.
  - `Owner`: correo electronico del lider tecnico responsable.
  - `Project`: identificador del proyecto o cliente corporativo.

## 2. Metodologia de Redimensionamiento (Rightsizing)
- Auditoria periodica del dimensionamiento de instancias de computo y bases de datos:
  - **Subutilizacion de CPU**: Instancias con consumo promedio de CPU inferior al 15% durante 14 dias consecutivos deben ser degradadas a una familia menor (ej. de `m5.xlarge` a `m5.large`).
  - **Subutilizacion de Memoria**: Servidores de base de datos o cache con ocupacion de RAM inferior al 35% deben evaluarse para consolidacion o reduccion de clase.
  - **Deteccion de Recursos Inactivos (Zombies)**: Volumenes de almacenamiento EBS desvinculados, direcciones IP elasticas sin asociacion y snapshots con antiguedad superior a 90 dias son detectados y eliminados periodicamente para evitar sobrecostos.

## 3. Estrategia de Contratacion y Reduccion de Costos
- **Uso de Instancias Bajo Demanda (On-Demand)**: Reservadas exclusivamente para cargas de trabajo impredecibles, picos estacionales breves o ambientes de pruebas temporales.
- **Instancias Reservadas (RI) y Savings Plans**:
  - Toda infraestructura de produccion con operacion continua garantizada superior a 6 meses debe migrarse a compromisos de reserva de 1 a 3 anos.
  - La combinacion de planes de ahorro (Compute Savings Plans) y descuentos por volumen anual permite reducciones de hasta un 20% en la factura consolidada de computo.
- **Analisis de ROI en Modernizacion**:
  - La migracion de motores relacionales tradicionales a bases de datos gestionadas de alto rendimiento (PostgreSQL con almacenamiento provisionado) reduce hasta un 30% el tiempo de administracion operativa de los ingenieros de sistemas.
