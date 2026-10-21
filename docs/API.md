# Filtros y API local

Con la aplicación abierta, visita `/api/docs` en la misma dirección local para ver la referencia interactiva generada por FastAPI. La API está pensada para el uso local de un solo usuario; no constituye un servicio autenticado para Internet.

## Contexto de filtros

El contexto es un objeto de hasta 25 campos `Tabla[Columna]`. Se aceptan nombres de tabla entre comillas simples y se normalizan internamente. Campos distintos se combinan con Y. Un filtro nuevo sobre el mismo campo sustituye al anterior. `CALCULATE` conserva su comportamiento de reemplazo y `REMOVEFILTERS` elimina el contexto del campo o tabla indicado.

```json
{
  "Equipos[Linea]": {"op": "in", "type": "text", "values": ["Línea 01", "Línea 02"]},
  "Lecturas[Produccion_kg]": {"op": "between", "type": "number", "value": 700, "value2": 900}
}
```

| Operadores | Valores |
| --- | --- |
| `eq`, `ne`, `gt`, `gte`, `lt`, `lte` | `value` |
| `contains`, `not_contains`, `starts_with`, `ends_with` | `value`; normalmente texto |
| `between` | `value` y `value2`, extremos incluidos |
| `in`, `not_in` | `values`, lista de 1 a 300 valores |
| `is_blank`, `not_blank` | No requieren un valor |

Los tipos disponibles son `text`, `number`, `date` y `boolean`. El texto se compara sin distinguir mayúsculas; no se eliminan tildes ni espacios automáticamente. Los filtros numéricos aceptan coma o punto decimal **sin separador de miles**: limpia primero los números del origen si hace falta. Las fechas de filtro usan ISO `AAAA-MM-DD`. Vacío incluye nulo y texto formado solo por espacios. Los valores escalares de v0.3 conservan su igualdad anterior.

## Rutas principales

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/health` | Estado y versión |
| GET | `/api/model` | Resumen de tablas, relaciones, medidas y filtros |
| GET | `/api/table/{name}` | Filas de origen sin filtros; hasta 500 por petición |
| POST | `/api/table-query` | Filas con filtros, búsqueda, orden y paginación |
| GET | `/api/profile/{name}` | Calidad y estadísticas de la tabla completa |
| GET | `/api/distinct?field=Tabla[Columna]&search=texto` | Valores únicos; hasta 300 por respuesta, con indicación de truncamiento |
| POST | `/api/filters` | Guardar el contexto de filtros del informe |
| POST | `/api/evaluate` | Evaluar `expression` DAX con `filters` explícitos |
| POST | `/api/dashboard` | Calcular visualizaciones con el contexto indicado |
| POST | `/api/import` | Importar CSV, TSV, JSON o XLSX; multipart, campo `file` |
| POST | `/api/project/import` | Abrir proyecto; multipart, campo `file` |
| GET | `/api/export` | Exportar el modelo y los datos como proyecto |
| POST | `/api/relationship` | Crear una relación N:1 validada |
| DELETE | `/api/relationship/{idx}` | Quitar una relación |
| PUT | `/api/measure` | Crear o sustituir una medida, `name` y `expression` |
| DELETE | `/api/measure/{name}` | Quitar una medida que no utilice un gráfico |
| POST | `/api/visual` | Crear o editar una visualización |
| DELETE | `/api/visual/{visual_id}` | Quitar una visualización |
| POST | `/api/sql` | Ejecutar `query`, de solo lectura, sobre el modelo completo |
| POST | `/api/demo` | Sustituir el proyecto local por la demo |

El laboratorio SQL y el perfil de calidad trabajan sobre el modelo completo. No heredan automáticamente los filtros del informe. La exploración filtrada utiliza `/api/table-query` y pasa el contexto de forma explícita.

## Consultar una tabla

```json
{
  "table": "Lecturas",
  "filters": {"Equipos[Area]": {"op": "contains", "type": "text", "value": "mez"}},
  "search": "2026-09",
  "sort_column": "Produccion_kg",
  "sort_type": "number",
  "sort_direction": "desc",
  "offset": 0,
  "limit": 40
}
```

La respuesta contiene `rows`, `total`, `source_total`, `columns` y `revision`. Al recorrer varias páginas para exportar, pasa la primera `revision` en las peticiones posteriores. Si cambia el proyecto, la respuesta es 409 para evitar mezclar versiones. `limit` se limita a 500.

## Limpieza en dos fases

`POST /api/cleaning/preview` calcula el resultado sin guardarlo:

```json
{
  "table": "datos_para_limpiar",
  "steps": [
    {"op": "trim", "columns": ["Nombre", "Grupo"]},
    {"op": "to_number", "columns": ["Importe"], "locale": "es", "on_error": "keep"}
  ]
}
```

La respuesta incluye contadores, `sample`, `issues` y `token`. Tras revisar, envía el mismo objeto con ese `token` a `POST /api/cleaning/apply`. El servidor vuelve a calcularlo, comprueba que el proyecto no ha cambiado, guarda la copia y aplica los cambios. `GET /api/cleaning/status` muestra historial y posibilidad de deshacer. `POST /api/cleaning/undo` restaura la copia solo si no ha habido cambios posteriores y su integridad es correcta.

Los nombres de operación y parámetros están documentados por los ejemplos y las pruebas de preparación. La guía funcional explica [los 16 pasos y sus límites](LIMPIEZA.md). Las recetas se ejecutan en orden sobre toda la tabla, no sobre el informe filtrado. No se admiten expresiones Python ni sustituciones con regex arbitrarias.

## Errores

- 404: tabla, medida o relación solicitada inexistente, cuando lo indica la ruta.
- 422: formato, regla, expresión, relación o transformación inválida.
- 409: revisión o vista previa caducada, deshacer inseguro o copia alterada.

Conserva los mensajes completos al comunicar un problema, eliminando datos privados. Una vista previa fallida no cambia los datos.
