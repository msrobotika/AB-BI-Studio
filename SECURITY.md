# Seguridad

AB-BI Studio v0.4 es una aplicación local de un solo usuario. No se ha sometido a una auditoría exhaustiva de seguridad. No se ofrece un plazo de soporte ni una homologación de producción.

## Informar de un problema

Si el repositorio muestra Security → Report a vulnerability, utiliza ese canal privado. Si no está disponible, abre una incidencia solicitando un canal privado de contacto **sin incluir detalles explotables, credenciales ni datos reales**. No se debe asumir que la opción de comunicación privada está habilitada hasta comprobarlo.

Incluye la versión, el sistema operativo, los pasos mínimos y datos ficticios. Un fallo que pueda alterar archivos o datos debe notificarse con cuidado; no publiques pruebas contra sistemas ajenos.

## Modelo de uso

- El lanzador escucha en `127.0.0.1`. No lo expongas por NAT o proxies como servicio multiusuario.
- `.abbi`, autoguardado y copias de seguridad contienen datos sin cifrar. Protege las carpetas con las medidas de tu equipo.
- La limpieza se revisa antes de aplicar y conserva una copia local. Deshacer no sobrescribe cambios posteriores.
- El parser DAX no ejecuta expresiones como Python. SQL usa una copia SQLite de solo lectura con límites de respuesta y ejecución.
- Las importaciones y proyectos tienen límites de tamaño, tablas, filas y columnas. Eso no elimina todo riesgo al procesar archivos no confiables.
- Las dependencias están fijadas para reproducir la versión comprobada. Antes de actualizar, revisa sus avisos y vuelve a ejecutar las pruebas.

Las mejoras de seguridad y su alcance se documentarán en el changelog y en cada publicación.
