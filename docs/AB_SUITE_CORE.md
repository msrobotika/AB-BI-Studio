# AB-BI Studio ← AB-Suite Core

Conector **de solo lectura** para convertir los eventos del PLC virtual de MS ROBOTIKA en un CSV importable por AB-BI Studio.

## 1. Iniciar el sistema de simulación

En el repositorio AB-PLC-Simulator, con Node.js 20+:

    npm run suite:core

El comando imprime la URL de la HMI, el puerto del bus Core y un token temporal para el monitor. Abre la URL de la HMI en tu PC y pulsa RUN + MARCHA.

## 2. Crear el CSV desde el bus

En otra consola PowerShell, en la carpeta AB-BI-Studio (Python 3.11+):

    $env:AB_SUITE_TOKEN = "<TOKEN_MONITOR_MOSTRADO_POR_SUITE_CORE>"
    python scripts/ab_suite_telemetry.py --url http://127.0.0.1:4175 --out ab_suite_plc_telemetry.csv

Este proceso se suscribe a eventos SSE autenticados y registra solo plc.snapshot emitidos por ab-plc-simulator.

Campos: sequence, received_at, simulated_ms, scenario, mode, scan, Q0_0, Q0_1, Q0_2, AI0, counter_C0, process_value, process_unit y active_faults.

Detén la captura con Ctrl+C. Los datos son de **simulación**, no mediciones reales de una planta.

## 3. Importar en AB-BI Studio

Abre AB-BI Studio y selecciona Importar archivo → CSV. Elige ab_suite_plc_telemetry.csv. Puedes crear KPIs de piezas entregadas, nivel del depósito, scan, señales de salida y fallos virtuales.

**No hay streaming integrado dentro del panel de AB-BI**: el adaptador actual guarda un CSV; los datos nuevos requieren actualizar o volver a importar el archivo desde AB-BI. No se reescribe su motor de análisis ni se accede a SQLite interno.

## Seguridad, trazabilidad y límites

- Solo se admite localhost (127.0.0.1). Nunca se guardan credenciales en el CSV.
- El historial del bus es volátil y tiene retención acotada. Si hay un error HTTP 409, la secuencia requerida expiró; el script se detiene en vez de omitir datos silenciosamente.
- Cada fila conserva sequence (orden del bus), received_at (UTC del servidor) y simulated_ms (tiempo lógico de la CPU). No confundirlos.
- El script vuelve a leer las secuencias del CSV ya guardadas antes de retomar para evitar duplicar filas.
- AB-BI Studio limita la importación a 40.000 filas por tabla; divide los archivos por sesión si se supera.
- Python estándar, sin bibliotecas de terceros. Los valores de proceso son didácticos.
- Ninguna función de escritura a PLC, Modbus o maquinaria real.

Código: scripts/ab_suite_telemetry.py y pruebas tests/test_ab_suite_telemetry.py.

Contrato productor: https://github.com/msrobotika/AB-Suite-Core-arquitectura-de-integraci-n

## Ingesta directa sin reimportación CSV

Existe además el modo experimental de inserción de filas en el modelo de AB-BI, con un receptor SSE opcional y una tabla dedicada SuitePLC. Se mantiene desactivado sin consentimiento (token local) y se documenta por separado en [Suite Live](SUITE_LIVE.md). La opción CSV anterior continúa disponible.
