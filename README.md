# AB·BI Studio

> **Ficha del proyecto · MS ROBOTIKA**  
> **Estado:** v0.4 · aplicación de análisis y limpieza de datos · **Licencia:** ver archivo [LICENSE](LICENSE)  
> **Evidencia:** [CI](.github/workflows/ci.yml) · [Capturas/documentación](docs/) · [Estado técnico](docs/PROJECT_STATUS.md)  
> **Importante:** El motor DAX implementa un subconjunto propio; compatibilidad no idéntica a Power BI.

**Análisis y preparación de datos en tu equipo, en español y con código abierto.**

AB-BI Studio v0.4 reúne importación CSV/TSV, JSON y Excel multihoja, modelo semántico con relaciones, un intérprete independiente de un subconjunto DAX, informes, filtros interactivos y recetas de limpieza. La aplicación es gratuita bajo [licencia MIT](LICENSE); las dependencias conservan [sus propias licencias](THIRD_PARTY_NOTICES.md).

**[Descargar v0.4](https://github.com/msrobotika/AB-BI-Studio/releases/latest)** · [Instalación](docs/INSTALACION.md) · [Guía de limpieza](docs/LIMPIEZA.md) · [Todas las capturas](docs/CAPTURAS.md)

![AB-BI Studio v0.4: informe en modo oscuro, KPI y donut](docs/ABBI_04_oscuro.png)

## Empezar en Windows

1. Instala **Python 3.11 o superior** desde [python.org](https://www.python.org/downloads/).
2. Descarga y extrae el ZIP completo de Releases.
3. Abre **`iniciar.bat`** dentro de la carpeta extraída.
4. Se abre el navegador. Mantén la consola abierta mientras usas la aplicación.

El primer inicio necesita Internet para instalar dependencias. El motor escucha en `127.0.0.1`; la consola muestra el puerto utilizado. **No abras el HTML directamente.** Desde un clon del repositorio, ejecuta el mismo lanzador en su raíz. Consulta [instalación y problemas habituales](docs/INSTALACION.md) para más detalles.

## Qué incluye v0.4

| Área | Funciones disponibles |
| --- | --- |
| Importación | CSV/TSV, JSON plano y todas las hojas no vacías de XLSX |
| Preparación | 16 transformaciones encadenables, recetas JSON, vista previa antes/después e incidencias de conversión |
| Recuperación | Copia previa a cada limpieza, historial y deshacer mientras no haya cambios posteriores |
| Calidad | Vacíos, duplicados, espacios exteriores, tipos mezclados y estadísticas de columnas |
| Modelo | Relaciones muchos → uno y propagación desde dimensiones hacia hechos |
| Medidas | Subconjunto DAX con SUM, CALCULATE, SUMX, RELATED, DIVIDE y otras funciones documentadas |
| Informes | KPI, barras, líneas, áreas, donut y tablas; filtros al pulsar categorías |
| Filtros | Varios valores, texto, rangos de números/fechas, vacíos y condiciones combinadas por campo |
| Tablas | Búsqueda, ordenación, paginación y CSV con todas las filas filtradas |
| Apariencia | Temas oscuro/claro, donuts corregidos y adaptación móvil |
| SQL | SQLite de solo lectura; resultados limitados a 500 filas |
| Proyectos | Autoguardado local e importación/exportación `.abbi`, con conversión de proyectos antiguos |

## Probar la limpieza

Importa `examples/datos_para_limpiar.csv`. En **Preparar y limpiar**, elige la tabla importada, abre `examples/receta_limpieza.json` y genera una vista previa. Comprueba las filas resultantes y las conversiones fallidas antes de aplicar. La limpieza actúa sobre toda la tabla; los filtros del informe no la limitan. [Guía completa](docs/LIMPIEZA.md).

## Documentación

- [Instalación, actualización y recuperación](docs/INSTALACION.md)
- [Preparación y limpieza de datos](docs/LIMPIEZA.md)
- [Filtros y API local](docs/API.md)
- [Funciones DAX y límites de compatibilidad](docs/DAX.md)
- [Arquitectura y formato de proyecto](docs/ARQUITECTURA.md)
- [Hoja de ruta y funciones pendientes](docs/HOJA_DE_RUTA.md)
- [Capturas de escritorio, claro/oscuro y móvil](docs/CAPTURAS.md)
- [Resultados y alcance de la validación local](docs/VALIDACION_04.md)
- [Cambios de v0.4](CHANGELOG.md), [contribuir](CONTRIBUTING.md) y [seguridad](SECURITY.md)

## Desarrollo y pruebas

En un entorno virtual de desarrollo, desde la raíz:

```text
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest -q
node --check frontend/app.js
node --check frontend/studio.js
```

La revisión local en Windows con CPython 3.13 superó **40 pruebas**, incluidos dos recorridos completos en Chromium. Las pruebas aíslan datos y procesos; las capturas contienen datos ficticios. El flujo de GitHub Actions vuelve a ejecutar la batería y conserva los resultados; consulta cada ejecución para conocer su estado real.

`constraints.txt` fija las dependencias de ejecución comprobadas. Para crear una distribución sin datos, entornos virtuales ni archivos privados:

```text
python scripts/build_distribution.py --output dist
```

## Límites y privacidad

La aplicación es de un solo usuario y trabaja en memoria: hasta 24 tablas, 40.000 filas por tabla y 200.000 en el proyecto. Importaciones de hasta 18 MB; proyectos de hasta 30 MB. Estos límites no garantizan rendimiento para toda carga posible. El [informe de validación](docs/VALIDACION_04.md) recoge una medición puntual con 40.000 filas.

Los proyectos, el autoguardado y las copias contienen datos **sin cifrar**. Se guardan en tu equipo y no deben subirse a incidencias ni al repositorio. Exporta una copia antes de actualizar. No expongas el servidor local a Internet como si fuera un servicio multiusuario.

AB-BI Studio es independiente y no está afiliado a Microsoft ni Tableau. No abre PBIX ni implementa Power Query M o DAX completo. No es una herramienta homologada para decisiones contables u operativas críticas. DuckDB, conectores remotos, inteligencia temporal DAX y composición libre por páginas siguen en la [hoja de ruta](docs/HOJA_DE_RUTA.md).

## Licencias

Consulta [LICENSE](LICENSE), [avisos de terceros](THIRD_PARTY_NOTICES.md) y los textos conservados en `third_party/licenses/`. No se incluyen binarios de productos comerciales ni bibliotecas Python empaquetadas. La revisión de licencias no certifica por sí sola toda la procedencia histórica ni ausencia de reclamaciones.


## Integración con AB-Suite Core (PLC virtual → informes)

El adaptador opcional scripts/ab_suite_telemetry.py recibe por SSE los snapshots de AB-PLC Simulator y los guarda en un CSV compatible con el importador de AB-BI. Ese modo sigue disponible para exportar archivos; también se ofrece una integración experimental de datos en directo dentro del modelo BI mediante un conector separado y autenticado.

Instrucciones de puesta en marcha, campos, seguridad y ejemplo PowerShell: [AB-Suite Core](docs/AB_SUITE_CORE.md). Solo datos de laboratorio y 127.0.0.1.

## Nuevo: AB-Suite Core → SuitePLC en directo (experimental)

Ahora existe un conector opt-in de lectura SSE que añade las muestras virtuales a **una sola tabla SuitePLC del modelo semántico**, sin reimportar el CSV. La interfaz refresca informes y tablas cuando llegan lecturas nuevas. Requiere arrancar AB-BI con ABBI_SUITE_WRITE_TOKEN y ejecutar el receptor desde otra consola con el token de monitor del bus.

[Guía técnica y comandos PowerShell](docs/SUITE_LIVE.md). Sigue siendo un laboratorio local, no un sistema de control industrial.
