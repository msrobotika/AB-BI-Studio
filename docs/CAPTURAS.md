# Capturas de AB-BI Studio v0.4

Capturas reales generadas en Chromium por las pruebas de navegador, con datos de demostración ficticios. Las pantallas muestran la aplicación local; no contienen datos privados del usuario.

## Informe en modo oscuro

Donut con segmentos diferenciados, leyenda, valores y porcentajes.

![Informe y donut en modo oscuro](ABBI_04_oscuro.png)

## Informe en modo claro

![Informe en modo claro](ABBI_04_claro.png)

## Preparación y vista previa

Receta de seis pasos, filas resultantes y comparación antes/después. Las dos conversiones inválidas del ejemplo se muestran de forma explícita.

![Preparación y vista previa](ABBI_04_limpieza.png)

## Adaptación móvil

[Informe móvil](ABBI_04_movil.png) · [Preparación móvil](ABBI_04_limpieza_movil.png)

<img src="ABBI_04_movil.png" alt="Informe en pantalla de 390 píxeles" width="320">
<img src="ABBI_04_limpieza_movil.png" alt="Preparación en pantalla de 390 píxeles" width="320">

## Regeneración

Las pruebas de `tests/test_browser.py` regeneran estas cinco imágenes. Usa datos temporales aislados y su propio servidor local. Las capturas `ABBI_03_*.png` se conservan solo como referencia histórica y no representan la interfaz actual.
