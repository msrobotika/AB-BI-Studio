@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "ABBI_PYTHON=py -3") else (set "ABBI_PYTHON=python")
%ABBI_PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo Se necesita Python 3.11 o superior. Instálalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo Preparando entorno virtual de AB-BI Studio...
  %ABBI_PYTHON% -m venv .venv
  if errorlevel 1 (echo No se pudo crear el entorno Python. & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: No se pudieron instalar las dependencias. Comprueba Python y la red.
  pause
  exit /b 1
)
echo.
echo AB-BI Studio 0.4 se abrirá en tu navegador.
echo Mantén esta ventana abierta. Pulsa Ctrl+C para detener el motor.
echo.
.venv\Scripts\python.exe run.py
pause
