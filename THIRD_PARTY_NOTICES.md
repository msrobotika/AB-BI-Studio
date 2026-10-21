# Componentes y avisos de terceros

AB-BI Studio v0.4 distribuye código fuente de la aplicación. Su licencia MIT no sustituye las licencias de las dependencias. Los paquetes Python se descargan de PyPI al instalar; no se incluyen sus ejecutables ni sus ruedas en este ZIP.

Se conservan los textos de licencia y avisos encontrados en las distribuciones instaladas en `third_party/licenses/`, junto con sus autores originales. `third_party/dependency_inventory.json` relaciona cada paquete con sus avisos. La tabla registra el cierre de dependencias de ejecución resuelto en CPython 3.13 sobre Windows durante la revisión del 21 de octubre de 2026.

| Componente | Versión | Licencia declarada |
| --- | --- | --- |
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| et-xmlfile | 2.0.0 | MIT |
| fastapi | 0.157.0 | MIT |
| h11 | 0.16.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| openpyxl | 3.1.5 | MIT |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| pydantic | 2.14.1 | MIT |
| pydantic-core | 2.50.1 | MIT |
| python-multipart | 0.0.32 | Apache-2.0 |
| starlette | 1.9.0 | BSD-3-Clause |
| typing-extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |

FastAPI, openpyxl y varias dependencias usan MIT; Uvicorn, Starlette, click e idna usan BSD-3-Clause; python-multipart y OpenTelemetry API usan Apache-2.0; typing-extensions conserva su licencia PSF-2.0 y sus avisos incluidos. Los textos completos adjuntos son la referencia para las condiciones de cada componente, incluidas las licencias adicionales dentro de esos textos.

Python, su biblioteca estándar y SQLite los proporciona la instalación de Python del usuario; no están incorporados en este archivo. Pytest, HTTPX, Playwright y Chromium solo se usan como herramientas opcionales de desarrollo y pruebas; tampoco se incluyen sus paquetes ni el navegador en la distribución. El frontend dibuja sus gráficos con SVG y no carga bibliotecas gráficas ni tipografías remotas.

Fuentes primarias consultadas: [FastAPI](https://github.com/fastapi/fastapi/blob/master/pyproject.toml), [Uvicorn](https://pypi.org/project/uvicorn/), [python-multipart](https://pypi.org/project/python-multipart/), [openpyxl](https://pypi.org/project/openpyxl/) y los archivos de licencia de los paquetes instalados.

AB-BI Studio es un proyecto independiente. Los nombres Microsoft, Power BI, Tableau, Excel y DAX se utilizan para describir formatos, lenguajes o límites de interoperabilidad. No se incluyen logos ni binarios de esos productos y no se afirma afiliación, homologación ni compatibilidad total. El título de la herramienta de medidas es «Editor DAX», para distinguirla de DAX Studio.

La distribución v0.4 deriva del ZIP v0.3 recuperado del equipo del usuario (SHA-256 `3044449e69223d7ddb904c36b7fdc6c77ec04a43d6fb57c6cd30990f46365b45`). La revisión no reconstruye toda su procedencia anterior ni certifica originalidad completa, derechos de terceros, patentes o marcas. La licencia cubre los derechos que puedan conceder sus titulares; no garantiza ausencia de reclamaciones.
