# Politica Corporativa de Descuentos Comerciales, FinOps y SLA Cloud

## 1. Niveles de Servicio y SLA Garantizado
- **Nivel Mission Critical (Tier 1)**: Garantia de disponibilidad mensual del 99.999% (maximo 26 segundos de indisponibilidad no planificada al mes). Incluye redundancia activo-activo multirregion, tiempo de respuesta de ingenieria menor a 5 minutos y compensaciones contractuales inmediatas.
- **Plan Enterprise Cloud (Tier 2)**: Garantia de disponibilidad mensual del 99.99% (maximo 4.3 minutos de indisponibilidad al mes). Incluye soporte prioritario 24/7/365 con tiempo de respuesta menor a 15 minutos, asignacion directa de un Technical Account Manager (TAM) y conmutacion por error automatica multizona (Multi-AZ failover).
- **Plan Standard Startup (Tier 3)**: Garantia de disponibilidad mensual del 99.9% (maximo 43.8 minutos de indisponibilidad al mes). Soporte tecnico en horario de operaciones comerciales (8x5) con tiempo de respuesta promedio inferior a 4 horas.

## 2. Penalizaciones y Creditos por Incumplimiento de SLA
- Si la disponibilidad mensual cae por debajo del 99.99% en Enterprise Cloud:
  - Disponibilidad entre 99.0% y 99.98%: se acredita automaticamente el 10% del total de la facturacion mensual.
  - Disponibilidad entre 95.0% y 98.99%: credito del 25% de la factura mensual.
  - Disponibilidad inferior al 95.0%: credito del 50% de la factura mensual y derecho a rescision contractual sin penalidades.

## 3. Politica de Descuentos por Compromiso y Reserva de Capacidad
- La empresa premia el compromiso financiero a largo plazo mediante una matriz de descuentos sobre instancias reservadas:
  - **Compromiso a 1 ano (Pago Mensual o Adelantado)**: Descuento base aplicable de hasta el 10% sobre la tarifa bajo demanda (On-Demand).
  - **Compromiso a 2 anos (Convertible o Estandar)**: Descuento comercial negociable entre el 11% y el 18%.
  - **Compromiso a 3 anos o superior**: Descuento corporativo maximo autorizado del 20% sobre computo y bases de datos.
  - Descuentos superiores al 20% quedan estrictamente prohibidos a nivel de catalogo general y requieren aprobacion de la Junta Directiva.

## 4. Gobernanza Financiera y Regla Human-in-the-Loop (HITL)
- **Criterios de Clasificacion de Operacion Critica**:
  1. Solicitud de descuento comercial igual o superior al 10% sobre la tarifa base.
  2. Facturacion o valor de contrato proyectado igual o superior a USD 1,000 anuales.
  3. Reconfiguracion de instancias de base de datos con eliminacion de replicas de lectura.
- **Protocolo de Bloqueo y Aprobacion Humana**:
  - Toda operacion clasificada como critica no podra ser aprobada ni ejecutada de forma autonoma por agentes de inteligencia artificial.
  - El sistema pausara de manera obligatoria el flujo de trabajo mediante un checkpoint persistente en Redis, notificando el estado `waiting_approval`.
  - La reanudacion requiere la firma digital o aprobacion de un Director de Cuenta o Gerente Financiero (HITL) a traves del endpoint correspondiente de la API.
