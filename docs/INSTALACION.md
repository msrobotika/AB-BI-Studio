# Instalación, actualización y solución de problemas

## Windows

1. Instala Python 3.11 o superior desde [python.org](https://www.python.org/downloads/). En el instalador clásico, activa Add Python to PATH.
2. Descarga el ZIP completo de [Releases](https://github.com/msrobotika/AB-BI-Studio/releases/latest) y extrae toda la carpeta.
3. Haz doble clic en `iniciar.bat`. Se crea un entorno virtual y se instalan las dependencias fijadas. El primer inicio necesita Internet.
4. Se abre el navegador cuando el motor v0.4 responde. La consola muestra la dirección local. Déjala abierta mientras uses la aplicación.
5. Detén el motor con Ctrl+C en la consola.

La dirección habitual es `http://127.0.0.1:8765`. Si hay otra instancia, el lanzador elige un puerto libre hasta 8784. `AB_BI_PORT` permite indicar otro puerto entre 1024 y 65535. No abras `frontend/index.html` directamente.

## Linux y macOS

Necesitan Python 3.11+ y venv. Estos sistemas no se han validado localmente en esta revisión; el procedimiento previsto es:

```bash
chmod +x iniciar.sh
./iniciar.sh
```

Para ejecutar desde un clon del repositorio, usa los mismos lanzadores en su raíz. La prueba automatizada de GitHub Actions registra sus resultados por separado; configurar una plataforma en CI no equivale a afirmar que ya ha pasado.

## Actualizar desde v0.3

1. Exporta tu proyecto `.abbi` desde la aplicación anterior.
2. Extrae la nueva versión en otra carpeta, sin sustituir el directorio anterior.
3. Inicia la versión nueva y usa Proyecto y archivos → Abrir proyecto.
4. Comprueba las tablas, relaciones y medidas y guarda una nueva exportación.

No copies el entorno `.venv` de una versión a otra. El formato de proyecto sigue siendo versión 3; los filtros avanzados se deben utilizar en v0.4. El editor clásico mantiene datos separados.

## Recuperar una copia de limpieza

Deshacer está disponible hasta que haya cambios posteriores. Las copias completas anteriores se conservan como JSON en `data/backups/`; puedes abrir una desde Proyecto y archivos. Exporta tu trabajo actual antes de recuperar una copia antigua. Las copias están en claro y no se incluyen al exportar `.abbi`.

## Problemas habituales

| Síntoma | Qué comprobar |
| --- | --- |
| La consola se cierra o falta Python | Abre `iniciar.bat` y comprueba Python 3.11+; revisa el mensaje antes de cerrar |
| No se instalan dependencias | Conexión a PyPI y permisos de escritura en la carpeta de la aplicación |
| Se ve la versión anterior | Usa la dirección que imprime la nueva consola; puede usar otro puerto |
| No conecta al motor | Mantén abierta la consola y abre su dirección local, no el HTML |
| CSV con acentos incorrectos | Guarda el origen como UTF-8; se admite UTF-8 con BOM |
| Número no convertible | Elige coma o punto decimal según el origen; revisa las incidencias en la vista previa |
| Fecha inválida o ambigua | Elige día/mes/año, mes/día/año o ISO explícitamente |
| La limpieza rompe una relación | Conserva el tipo de las claves o ajusta la relación antes; no se permiten nuevas claves sin correspondencia |
| No se puede deshacer | Ya hay cambios posteriores o la copia no coincide; conserva el trabajo actual antes de abrir un respaldo manual |

## Verificar el ZIP

El archivo `.sha256` de cada publicación contiene la huella del ZIP. Dentro del ZIP, `MANIFEST.sha256` enumera las huellas de sus archivos. Para comprobar la descarga en PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 .\AB_BI_Studio_v0_4_COMPLETO.zip
```

Compara el resultado con el `.sha256` de la misma publicación. La huella comprueba integridad; no es una firma criptográfica del autor.
