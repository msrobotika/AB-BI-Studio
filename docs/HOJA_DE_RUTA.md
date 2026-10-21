# Hoja de ruta

Se mantienen las decisiones de arquitectura local, el modelo semántico y el subconjunto DAX. La lista distingue las funciones disponibles de lo pendiente.

| Prioridad | Función | Estado de v0.4 |
| --- | --- | --- |
| 1 | Importación CSV/TSV, JSON y XLSX multihoja | Disponible |
| 2 | Tablas, detección de columnas y calidad | Disponible |
| 3 | Preparación de datos con recetas reproducibles | 16 operaciones, vista previa, incidencias, respaldo y deshacer |
| 4 | Barras, líneas y sectores tipo donut | Disponible; temas y donut corregidos |
| 5 | KPI, medidas DAX y agrupaciones | Disponible con los límites del motor independiente |
| 6 | Filtros interactivos | Texto, números, fechas, varios valores y vacíos; propagación por relaciones |
| 7 | Constructor visual de informes | Editor de gráficos disponible; composición libre por páginas pendiente |
| 8 | Guardar y recuperar proyectos | `.abbi`, autoguardado, historial y copia previa a limpieza |

## Siguiente fase: sin fecha comprometida

- Motor analítico vectorizado DuckDB opcional/embebido y caché para conjuntos mayores. No está integrado.
- Mayor cobertura DAX: FILTER, VALUES, KEEPFILTERS, ALLSELECTED, inteligencia temporal y transición de contexto, con baterías cruzadas frente a motores de referencia.
- Relaciones bidireccionales controladas, tablas calculadas y agregaciones multitabla.
- Composición por páginas con arrastrar y soltar, mapas, imágenes, formatos de medida y edición de temas. La selección por categoría ya filtra en v0.4; otras interacciones cruzadas siguen pendientes.
- Conectores SQL Server, PostgreSQL y MQTT con almacenamiento de credenciales, permisos y cifrado.
- Instaladores empaquetados y validación de más versiones de Python y sistemas operativos. La distribución actual requiere Python; no es un ejecutable autónomo.

Las solicitudes pueden discutirse mediante incidencias del repositorio. Una función no se considera terminada hasta que tiene comportamiento comprobable, documentación y pruebas adecuadas.
