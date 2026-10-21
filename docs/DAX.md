# Referencia del motor DAX

## Modelo DAX — funciones admitidas

- Agregaciones: `SUM`, `AVERAGE`, `MIN`, `MAX`, `COUNT`, `DISTINCTCOUNT`, `COUNTROWS`.
- Contexto: `CALCULATE`, `REMOVEFILTERS` y `ALL` **solo como modificadores dentro de CALCULATE**, `SELECTEDVALUE`, `HASONEVALUE`.
- Iteradores: `SUMX` y `RELATED` dentro del contexto de fila. `RELATED` solo desde el lado muchos al lado uno.
- Escalares: `DIVIDE`, `IF`, `COALESCE`, `ABS`, `ROUND`, `AND`, `OR`, `NOT`.
- Operadores: `+ - * / = <> != < <= > >= && ||` y paréntesis.
- Notación de medida: `[Medida]`; columna: `Tabla[Campo]` o `'Tabla con espacios'[Campo]`; texto: `"Hola"`.

Ejemplo reproducible:

```dax
CALCULATE(
   [Producción total],
   Equipos[Area] = "Mezclas"
)
```

```dax
DIVIDE(
  [Producción total],
  CALCULATE([Producción total], REMOVEFILTERS(Equipos[Linea])),
  0
) * 100
```

**Límites importantes**: no soporta `FILTER`, `SUMMARIZECOLUMNS`, context transition completo, `USERELATIONSHIP`, bidireccionalidad, RLS, `DATESYTD`, calendarios DAX automáticos, queries DAX EVALUATE, DAX Studio ni Power Query M. Una ausencia de valores relacionados puede excluir filas (no se genera la fila BLANK propia del tabular completo). DAX usa `,` como separador de argumentos en este motor; no `;`. La semántica se ha validado con pruebas unitarias de subconjuntos conocidos; los cálculos no deben sustituir validaciones contables/operacionales críticas.

