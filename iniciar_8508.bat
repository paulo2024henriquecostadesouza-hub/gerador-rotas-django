@echo off
chcp 65001 >nul
title Gerador de Rotas - CCO :8508

echo.
echo  ============================================
echo   Gerador de Rotas - CCO
echo   Porta fixa: http://10.1.1.27:8508
echo  ============================================
echo.

pushd "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Execute instalar.bat primeiro.
    pause
    popd
    exit /b 1
)

call venv\Scripts\activate.bat

echo [+] Aplicando migracoes...
python manage.py migrate --run-syncdb >nul 2>&1

echo [+] Iniciando servidor em 0.0.0.0:8508 ...
echo.
echo  Acesse em:
echo    Rede local : http://10.1.1.27:8508
echo    Localhost  : http://localhost:8508
echo.

start "" http://10.1.1.27:8508

python manage.py runserver 0.0.0.0:8508

popd
