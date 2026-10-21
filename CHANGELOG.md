# Cambios

## 0.4.0 — 21 de octubre de 2026

- Corrige el relleno de los segmentos del donut que ocultaba sus colores.
- Añade leyendas con porcentaje, mensajes para valores negativos/cero y contraste por tema.
- Añade tema claro, preferencia de tema y foco visible para teclado.
- Corrige el trazado de barras negativas y permite filtrar al pulsar gráficos y leyendas.
- Añade filtros de varios valores, texto, números, fechas, intervalos y vacíos con propagación por relaciones y uso en DAX.
- Normaliza referencias de campos de tablas con espacios, manteniendo CALCULATE y REMOVEFILTERS.
- Añade búsqueda, ordenación y exportación CSV de las filas filtradas, con detección de cambios durante la exportación.
- Añade 16 transformaciones encadenables con vista previa sobre toda la tabla, muestra antes/después y tratamiento explícito de conversiones fallidas.
- Añade recetas JSON, historial, copia local antes de aplicar y deshacer con verificación de integridad.
- Impide aplicar vistas previas antiguas, sobrescribir cambios posteriores al deshacer y aumentar claves sin correspondencia.
- Conserva columnas de tablas vacías y detecta columnas dispersas más allá de las primeras 200 filas.
- Cachea el conjunto de columnas del motor para evitar búsquedas completas repetidas dentro de SUMX.
- Amplía el perfil de calidad con duplicados, espacios y tipos mezclados.
- Mantiene relaciones, subconjunto DAX, SQL de solo lectura, importadores y formato de proyecto v3.
- Fija versiones de ejecución y añade licencia MIT, avisos de terceros, ejemplos y guía.
- Usa un puerto local alternativo si hay otra instancia abierta, para evitar abrir por error la versión anterior.
- Sustituye las antiguas pruebas de navegador con puente interno por pruebas HTTP reales, temporales y aisladas.

El ZIP v0.3 original se conserva. La publicación usa un repositorio exclusivo de AB-BI Studio.

### Documentación de la publicación

- Guía principal con capturas reales y enlaces a instalación, limpieza, filtros/API, DAX, arquitectura y hoja de ruta.
- Guías para contribuir, comunicar vulnerabilidades y construir el ZIP con huellas de integridad.
- Flujo de pruebas en GitHub Actions y resultados locales documentados por separado.
