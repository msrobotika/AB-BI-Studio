# Lista de publicación — AB-BI-Studio

Esta es una **puerta de calidad**, no una certificación. Completarla antes de marcar una versión como estable o subir ejecutables en Releases.

## Código y derechos

- [ ] Versión coherente en interfaz, README, CHANGELOG, artefactos y etiqueta Git.
- [ ] Código fuente editable y reconstruible desde un commit inmutable, no solo un ZIP.
- [ ] LICENSE, atribuciones y derechos de dependencias, modelos, imágenes y datasets auditados.
- [ ] Ninguna contraseña, clave API, token, ruta privada, muestra de cliente o dato identificable en Git.
- [ ] Sin artefactos temporales ni binarios de compilación fuera de una distribución expresamente autorizada.

## Reproducción y calidad

- [ ] La CI del commit de publicación está aprobada; enlazar el ID de ejecución.
- [ ] Pruebas unitarias, de integración y de interfaz pertinentes ejecutadas y documentadas.
- [ ] Una instalación limpia en el sistema operativo prometido funciona con los prerrequisitos del README.
- [ ] Importaciones y entradas erróneas se rechazan de forma segura, sin resultados engañosos.
- [ ] Capturas reales recogidas desde el programa ejecutado, con instrucciones para regenerarlas.
- [ ] Las capturas corresponden a la versión publicada, y los enlaces del README funcionan.
- [ ] Limitaciones y escenarios sin prueba quedan explícitos (no omitirlos).

## Dominio y seguridad

Verificar importación, filtros, cálculos, persistencia, precisión de cifras y compatibilidad de datasets de prueba sin exponer información de clientes.

- [ ] Diferenciar prueba sintética/local, hardware de laboratorio y validación independiente.
- [ ] No automatizar acciones sobre máquinas ni redes de terceros sin consentimiento, permisos y evaluación de riesgos.
- [ ] Evaluar cambios de dependencias y posibles vulnerabilidades.
- [ ] Documentar cómo revertir una versión.

## Paquete y mantenimiento

- [ ] Archivo de release versionado y suma SHA-256 publicados (para artefactos distribuibles).
- [ ] Notas de versión enlazadas con problemas resueltos, incompatibilidades y limitaciones.
- [ ] README del release apunta a descargas permanentes y no confunde código fuente con binarios.
- [ ] La rama principal se conserva y se revisan los PR con su [plantilla](../.github/PULL_REQUEST_TEMPLATE.md).

**Regla de publicación:** una ejecución de CI verde por sí sola no acredita precisión, seguridad, conformidad IEC, validez clínica ni puesta en marcha industrial.
