# Contribuir

Gracias por ayudar a mejorar AB-BI Studio. Antes de proponer una función, revisa la [hoja de ruta](docs/HOJA_DE_RUTA.md) y los [límites DAX](docs/DAX.md).

## Cambios

1. Describe el problema y un ejemplo reproducible con datos ficticios.
2. Trabaja en una rama y conserva el motor semántico, las relaciones y los proyectos existentes.
3. Añade pruebas que verifiquen comportamiento y errores relevantes, especialmente si modificas filtros, importación, medidas o persistencia.
4. Ejecuta las pruebas y la comprobación de sintaxis indicadas en el README. Los tests de navegador usan datos y procesos temporales.
5. Actualiza la documentación y el changelog. Si cambia la interfaz, regenera las capturas relevantes.
6. Abre un pull request explicando el problema, el comportamiento final y cómo lo has comprobado.

## Datos y derechos

No incluyas `.abbi` reales, `data/`, copias de seguridad, contraseñas, archivos de entorno ni datos personales. Usa conjuntos sintéticos mínimos. No copies código, logos ni recursos de terceros sin una licencia compatible y sus avisos. Los cambios propios se proponen bajo la licencia del proyecto; conserva los avisos ajenos.

## Construir una distribución

`python scripts/build_distribution.py --output dist` crea el ZIP, su huella SHA-256 y un manifiesto interno. Solo incorpora rutas explícitas del proyecto. No incorpora datos locales ni entornos virtuales. Comprueba el ZIP, ejecuta las pruebas y revisa las licencias antes de adjuntarlo a una publicación.
