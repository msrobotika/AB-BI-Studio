# Validación de v0.4

Entorno: Windows, CPython 3.13, dependencias de ejecución de `constraints.txt`, Chromium instalado mediante Playwright. Fecha: 21 de octubre de 2026.

La batería comprende 40 casos: 6 originales de semántica/API, 31 de preparación y filtrado, 1 de selección segura de puerto y 2 recorridos completos de navegador. Se comprueban filtros combinados y propagados, CALCULATE/REMOVEFILTERS, selección de varios valores, conversión numérica y de fechas, errores, duplicados, tablas vacías, esquema disperso, protección de relaciones, exportación, vista previa sin escritura, aplicación/deshacer, vistas previas caducadas, copias alteradas y fallos de persistencia.

Los recorridos de navegador comprueban oscuro/claro, persistencia del tema, donut sin relleno opaco, interacción por categorías, búsqueda/orden/exportación, editor DAX, preparación con datos importados, vista previa/applicación, guardado `.abbi`, deshacer y ausencia de desplazamiento horizontal de la página en móvil. Se revisaron visualmente las capturas oscuras, claras, de limpieza y móvil.

Las pruebas usan carpetas temporales y procesos locales propios. Los datos del usuario no se incorporan al ZIP. Se comprueba la sintaxis de los dos JavaScript. Las dependencias fijadas resuelven sin conflictos en el entorno probado.

Comprobación adicional con datos ficticios: 40.000 filas, dos pasos (espacios y conversión numérica), 80,000 celdas modificadas, vista previa en 4.205 segundos; SUMX con filtro en 0.223 segundos en este equipo. Es una medición puntual, no una garantía para otros modelos ni para el máximo global de 200.000 filas.

Existe una advertencia de obsolescencia en la integración de HTTPX del cliente de pruebas de Starlette. No afecta a los resultados. No se han probado Linux/macOS ni todas las combinaciones posibles de transformaciones, y no se afirma compatibilidad completa con DAX ni que exista una auditoría de seguridad exhaustiva.
