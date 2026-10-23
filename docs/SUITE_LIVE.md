# AB-BI Studio · telemetría Suite Core en directo (experimental)

AB-BI incorpora un canal opcional para escribir filas virtuales en **una sola tabla** del modelo semántico, sin crear nuevas tablas en cada lectura ni volver a importar CSV.

La fuente es únicamente AB-Suite Core en loopback. Un proceso de Python se suscribe por SSE y envía lotes autenticados al backend BI. El navegador **nunca ve los tokens** y actualiza automáticamente su vista del modelo cada 5 segundos cuando se visualizan informes, tablas o modelos.

## Tres terminales en el mismo ordenador

**A. Arranca la simulación** desde AB-PLC Simulator (Node.js 20+):

    npm install
    npm run suite:core

Abre la URL privada de HMI que imprime Core, pulsa RUN y MARCHA, y copia en un lugar seguro el token efímero MONITOR.

**B. Arranca AB-BI**, tras generar un token local de escritura (PowerShell, Python 3.11+):

    $secret = python -c "import secrets; print(secrets.token_hex(32))"
    $env:ABBI_SUITE_WRITE_TOKEN = $secret
    .\iniciar.bat

Guarda el valor de $secret para el siguiente terminal. El backend BI escucha de forma predeterminada en 127.0.0.1:8765.

**C. Arranca el receptor** en otra consola PowerShell desde AB-BI:

    $env:ABBI_SUITE_WRITE_TOKEN = "<MISMO_SECRETO_QUE_TERMINAL_B>"
    $env:AB_SUITE_TOKEN = "<TOKEN_MONITOR_CORE>"
    python scripts/ab_suite_live.py --bus-url http://127.0.0.1:4175 --bi-url http://127.0.0.1:8765

Abre el dashboard AB-BI y selecciona la tabla SuitePLC en el explorador. El contador Suite Live indica las lecturas recibidas. La tabla recibe automáticamente filas de la CPU virtual; el dashboard solo muestra KPIs de SuitePLC cuando el usuario cree las medidas/visualizaciones correspondientes.

Para detener: Ctrl+C en el terminal C. No afecta al motor del PLC ni a la máquina.

## Control de acceso

La ingesta está **desactivada por defecto**: sin ABBI_SUITE_WRITE_TOKEN de 32+ caracteres, el backend rechaza las escrituras. El script nunca transmite ese secreto al navegador; solo lo envía al backend local mediante X-ABBI-Suite-Token. El token del bus se envía únicamente a AB-Suite Core por Authorization. El script rechaza URLs fuera de 127.0.0.1 y redirecciones HTTP.

## Semántica y trazabilidad

- Tabla: SuitePLC. Campos: session_id, sequence, received_at, simulated_ms, scenario, mode, scan, Q0_0, Q0_1, Q0_2, AI0, counter_C0, process_value, process_unit y active_faults.
- La sesion del bus se identifica con los primeros 24 dígitos hexadecimales del SHA256 de su token MONITOR (no se guarda el token).
- El consumidor reanuda tras el último sequence confirmado y persistido; una repetición se deduplica.
- El servidor valida cada lote, calcula un candidato de modelo y solo lo conserva después de pasar los límites del motor semántico. Ante error de persistencia, restaura el estado anterior.
- Lotes configurables: 1–50 filas. Límites del BI: 40.000 filas por tabla y 200.000 por proyecto. No se eliminan datos automáticamente para aparentar continuidad.
- La UI refresca su vista aproximadamente cada 5 segundos; **no** son gráficos ni acciones de PLC en tiempo real determinista.
- Si el cursor de Core caduca, la lectura devuelve error 409: no se salta la pérdida. La fuente es sintética y no proviene de una planta real.

## Alternativa CSV

El antiguo script scripts/ab_suite_telemetry.py sigue disponible para quien prefiera guardar un CSV explícito e importarlo posteriormente en AB-BI. Ambos métodos reutilizan el mismo contrato de eventos y no duplican el motor BI.

**No usar para decisiones de seguridad funcional, control industrial ni rechazo automático de producto.**
