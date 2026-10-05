# Revisión de código — 2026-10-05

## Alcance

Base: último merge `319bd84` (PR #3). Extremo revisado: `e9db0ac`.
Son 11 commits y 90 archivos modificados: planificación, confirmaciones,
mantenimiento, resumen de Inicio, exportación/eliminación, migraciones,
cliente móvil, pruebas y documentación. Las capturas existentes son evidencia
histórica; esta revisión no sustituye pruebas de uso en dispositivos.

## Hallazgos corregidos

| Prioridad | Hallazgo | Cambio y efecto |
| --- | --- | --- |
| P2 | La generación consultaba versiones por cada plan y podía repetir la consulta para una vista futura. | `PlanningRepository.monthly_changes_for_plans` obtiene las versiones en una consulta después de bloquear las plantillas. `PlanningService` reutiliza el resultado en ambas fases. |
| P3 | Inicio y exportación construían una lista adicional de filas antes de construir el resultado. | Se itera directamente sobre el resultado SQLAlchemy, evitando esa lista intermedia. La respuesta completa y el buffering del driver siguen existiendo; no es exportación por streaming. |
| P3 | Cada llamada a `financialDate` construía un `Intl.DateTimeFormat` con la misma configuración. | Se reutiliza una instancia por módulo; fechas y zona financiera conservan su significado. |
| P3 | Los README describían el antiguo Inicio con cinco cuentas y negaban correcciones ya implementadas. | Se actualizó el estado de la aplicación, correcciones y controles de datos conforme a las reglas aprobadas. |

Para cuatro planes que necesitan recuperar meses y consultar un mes futuro,
las consultas de versiones pasan de ocho a una. Para un mes ya cubierto siguen
siendo cero. Esto reduce viajes a PostgreSQL durante esa operación; no demuestra
un porcentaje de mejora de latencia global o de FPS del cliente.

## Evaluación de calidad

Las operaciones financieras mantienen Decimal y monedas explícitas. La vista
de Inicio conserva su diagnóstico limitado, separado de dinero seguro para
gastar. Los filtros de propietario están presentes en las operaciones revisadas.
Confirmaciones/correcciones mantienen transacciones, identidad de reintentos,
bloqueos de filas y snapshots históricos. La lectura del resumen y la exportación
mantienen una única sentencia para obtener componentes consistentes.

La optimización no elimina los bloqueos: primero se adquieren las plantillas
en el orden existente y después se leen sus versiones. El orden de versiones
por mes efectivo e ID se conserva, incluyendo varias ediciones del mismo mes.
No cambia el esquema, las reglas financieras ni las dependencias.

Se conserva la separación explícita entre ingresos y compromisos en modelos,
esquemas y endpoints. Su semejanza no justifica una abstracción general que
complique tipos y contratos. Tampoco se añade caché de saldos o estados: su
invalidación introduciría un riesgo de mostrar dinero duplicado o desactualizado.

## Límites y trabajo pendiente

- La exportación sigue armando el JSON completo en memoria, y el cliente crea
  una cadena JSON adicional. Una exportación grande necesitará medición y un
  diseño específico antes de implementar streaming o límites.
- La recuperación mensual sigue siendo proporcional a los meses omitidos.
  Fechas iniciales extremadamente antiguas pueden generar muchas ocurrencias.
  Restringir esas fechas requiere una decisión de producto; no se cambia aquí.
- Los formularios móviles contienen JSX compacto y numerosos estados locales.
  Las pruebas del cliente cubren validación y llamadas API, pero no montan los
  componentes ni verifican interacción, teclado o rendimiento en dispositivos.
- Las dependencias tienen trabajo de seguridad registrado en `release-review.md`.
  Esta revisión no actualiza paquetes ni revalida los avisos contra fuentes externas.
- Operación pública, recuperación de contraseña, protección contra abuso y
  retención de backups mantienen los pendientes documentados del proyecto.

## Verificación

- PostgreSQL 17 temporal, separado de la base de la aplicación, con credenciales
  y datos sintéticos. Migraciones desde cero y eliminación del contenedor al terminar.
- 274 pruebas backend aprobadas; cobertura total reportada: 99%.
- Cuatro casos nuevos verifican cantidad de consultas, ingreso/compromiso,
  uno/cuatro planes, fechas cortas, versiones del mismo mes, planes sin versiones,
  recuperación y consulta futura, y ausencia de lecturas para meses cubiertos.
- Las pruebas existentes de concurrencia, exportación, propiedad, confirmación,
  corrección y preservación de migraciones también pasan.
- Ruff lint y formato; mypy estricto sobre 87 archivos: aprobados.
- 28 pruebas del cliente, ESLint y TypeScript: aprobados.
- Alembic confirma head y ausencia de diferencias entre modelos y esquema.
- `git diff --check`: aprobado. No se agregan secretos ni datos personales.

No se ejecutó una nueva compilación Android/iOS ni una medición de latencia
en dispositivos. Las mejoras de eficiencia se sustentan en la reducción de
consultas y de construcciones intermedias, no en tiempos de producción estimados.

Ejercicio: si hay cuatro planes pendientes de recuperar y una consulta futura,
¿por qué leer sus versiones en una consulta después de bloquear las plantillas
mantiene la consistencia sin necesitar una caché global?
