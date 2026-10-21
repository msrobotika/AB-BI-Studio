# Arquitectura

AB-BI Studio usa un servidor Python de un solo usuario en el equipo, una interfaz HTML/CSS/JavaScript y gráficos SVG. No requiere una cuenta, una base de datos externa ni servicios gráficos remotos. Los datos de aplicación no se suben a GitHub.

```text
backend/
  server.py       API FastAPI, importación, SQL, persistencia y copias
  semantic.py     Parser/AST DAX, evaluación y relaciones N:1
  filtering.py    Predicados tipados compartidos
  cleaning.py     Recetas deterministas y vista previa sin escritura
frontend/
  index.html      Interfaz principal
  app.js          Navegación, modelo, medidas, proyectos y clientes API
  studio.js       Gráficos, filtros, explorador y preparación
  style.css       Estilos, temas y adaptación móvil
  legacy_v02.html Editor clásico independiente
examples/         CSV ficticio y receta de limpieza
scripts/          Creación reproducible de la distribución
third_party/      Inventario y textos de licencia de dependencias
```

## Decisiones conservadas

- FastAPI y Uvicorn sirven la aplicación en `127.0.0.1`. El lanzador prueba los puertos 8765–8784 y abre el que utiliza esta instancia.
- El modelo completo reside en memoria, con hasta 24 tablas, 40.000 filas por tabla y 200.000 filas totales. La importación se limita a 18 MB por archivo y la apertura de proyectos a 30 MB.
- Las relaciones activas son muchos → uno; los filtros se propagan desde las dimensiones a los hechos. Se rechazan claves duplicadas en el lado uno y ciclos. No se implementa un modelo tabular completo.
- El lenguaje DAX se analiza en un AST. Las expresiones no se ejecutan con `eval` de Python. Véase [la referencia y sus límites](DAX.md).
- Las consultas SQL usan una copia SQLite en memoria, en modo de solo lectura, con un máximo de 500 filas de respuesta. Los filtros del informe no se inyectan en SQL.
- Los gráficos se generan con SVG sin bibliotecas gráficas externas. Los valores introducidos se escapan antes de mostrarlos.

## Persistencia y limpieza

`data/workspace.json` contiene el modelo en claro. El guardado usa un archivo temporal y reemplazo del archivo. `ABBI_DATA_DIR` permite elegir otra carpeta local. Las escrituras del servidor se serializan con un bloqueo del proceso; esto no proporciona soporte multiusuario.

La preparación es una función determinista compartida por vista previa y aplicación. La vista previa no modifica el proyecto. Su token representa el modelo y la receta; al aplicar, se recalcula y se rechaza una vista previa caducada. Se conserva el esquema aunque no queden filas. Se validan las relaciones y se rechaza una receta que aumente las claves sin correspondencia.

Antes de aplicar se escribe el proyecto anterior en `data/backups/`. El punto de deshacer registra la huella del proyecto aplicado y de la copia anterior. Solo se restaura si ambas coinciden, para evitar sobrescribir trabajo posterior o cargar una copia alterada. Las copias contienen datos y no se publican. El historial del proyecto conserva hasta 100 aplicaciones de recetas; las copias no se purgan automáticamente.

## Formato y compatibilidad

La versión de la aplicación es 0.4.0. El formato `.abbi` sigue siendo versión 3: añade `column_schema` y `cleaning_history` como metadatos. Los filtros avanzados deben utilizarse con la aplicación v0.4. Se importan proyectos v0.1/v0.2 mediante la conversión a una tabla. No se abren PBIX ni Power Query M.

DuckDB, almacenamiento columnar, conectores remotos y composición libre por páginas siguen en la [hoja de ruta](HOJA_DE_RUTA.md); no se anuncian como disponibles.
