# Preparación y limpieza

## Preparar y limpiar

1. Abre **Preparar y limpiar**, elige una tabla y marca las columnas.
2. Elige una transformación y pulsa **Añadir paso**. Puedes reordenar o quitar pasos. Se permiten 20 pasos por receta.
3. Genera **Vista previa**: se calcula sobre todas las filas de esa tabla, independientemente de los filtros del informe. Verás filas resultantes, eliminaciones, cambios de celdas, conversiones fallidas y hasta 12 ejemplos de filas afectadas.
4. Pulsa **Aplicar al proyecto** después de revisar y confirmar los cambios. El modelo se guarda y las medidas se recalculan sobre los datos preparados.
5. Puedes **Deshacer última limpieza** mientras no haya cambios posteriores en el proyecto. Guardar un filtro o editar una medida después de limpiar inhabilita ese deshacer para evitar sobrescribir trabajo posterior.

Las 16 transformaciones disponibles son: quitar espacios exteriores; unificar espacios; mayúsculas; minúsculas; quitar tildes/diacríticos; reconocer marcadores de vacío; sustituir texto literal; rellenar vacíos; convertir a número; convertir a fecha; convertir a booleano; convertir a texto; quitar duplicados; quitar filas con todas las columnas seleccionadas vacías; quitar filas con alguna columna seleccionada vacía; conservar filas por condición.

En números, elige **coma decimal** (`1.234,56`) o **punto decimal** (`1,234.56`). En fechas, elige día/mes/año, mes/día/año o ISO: no se adivinan fechas ambiguas. Puedes conservar los valores no convertibles, convertirlos en vacío o detener toda la receta. Los rellenos se introducen como texto; añade una conversión posterior si necesitas otro tipo. Quitar diacríticos convierte también `ñ` en `n`.

Al quitar duplicados se conserva la primera fila por combinación exacta de las columnas seleccionadas. La normalización previa es opcional y explícita. Se conserva el esquema de una tabla aunque la receta quite todas sus filas. Las claves del lado uno deben seguir siendo únicas y se rechazan recetas que aumenten las claves sin correspondencia en las relaciones activas. No se renombran ni se eliminan columnas para mantener las referencias del modelo.

**Recetas e historial:** guarda la receta como JSON y ábrela sobre otra tabla con las mismas columnas. Abrir una receta no la aplica. Las aplicaciones quedan registradas dentro del proyecto (hasta 100 entradas; interfaz muestra las últimas 8). Las recetas aún no aplicadas se conservan en esta sesión de la página: guárdalas antes de recargar.

**Copias de seguridad:** antes de aplicar se escribe el proyecto anterior en `data/backups/`. El punto de deshacer se conserva en `data/cleaning_undo.json` y persiste tras reiniciar. Las copias no viajan en el `.abbi`, no se borran automáticamente y contienen datos sin cifrar. Puedes abrir una copia JSON desde Proyecto y archivos para recuperar una versión antigua; exporta primero tu trabajo actual. `ABBI_DATA_DIR` permite elegir otra carpeta de datos local. Una vista previa antigua se rechaza si cambia el proyecto o la receta.


## Probar con el ejemplo

Importa `examples/datos_para_limpiar.csv`. Abre Preparar y limpiar, selecciona `datos_para_limpiar`, abre `examples/receta_limpieza.json` y pulsa Vista previa. Se conservan dos filas: Ana y Luis. La duplicada y la fila vacía se eliminan. El importe no convertible de Luis se conserva, y su fecha inválida se convierte en nulo, conforme a la receta. Revisa las incidencias antes de aplicar.
