# AB-BI Studio v0.4.0

Preparación de datos y filtros avanzados, conservando el modelo semántico y el intérprete independiente del subconjunto DAX.

## Cambios principales

- Donuts corregidos: colores diferenciados, leyenda y porcentajes. Temas oscuro/claro y adaptación móvil.
- 16 operaciones de limpieza en recetas reutilizables, con vista previa antes/después, incidencias, historial, copia previa y deshacer.
- Filtros de varios valores, texto, números, fechas, rangos y vacíos, con propagación por relaciones y selección desde gráficos.
- Búsqueda, ordenación, calidad y exportación de todas las filas filtradas.
- Protección contra vistas previas caducadas, copias alteradas y transformaciones que rompan relaciones.
- Dependencias fijadas, licencia MIT, avisos de terceros, ejemplos, capturas reales y documentación de instalación, DAX, API, arquitectura y hoja de ruta.

## Descargar e iniciar

Descarga `AB_BI_Studio_v0_4_COMPLETO.zip`, extrae toda la carpeta y abre `iniciar.bat` en Windows. Requiere Python 3.11+ y conexión para instalar dependencias el primer día. El archivo `.sha256` permite verificar el ZIP; dentro hay un manifiesto por archivo.

Para actualizar, exporta el `.abbi` desde tu versión anterior y ábrelo en Proyecto y archivos de la nueva. Mantén la carpeta anterior hasta comprobar tu trabajo.

## Validación y límites

Se superaron 40 pruebas localmente en Windows/CPython 3.13, incluidos dos recorridos completos de Chromium. Las capturas contienen datos ficticios. GitHub Actions registra por separado los resultados de sus propias ejecuciones.

Aplicación local de un solo usuario; no es un ejecutable autónomo. Los datos y respaldos están sin cifrar. No abre PBIX ni implementa DAX completo. La composición libre de páginas, DuckDB y los conectores remotos siguen pendientes.
