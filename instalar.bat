@echo off
chcp 65001 >nul
title Instalando Gerador de Rotas - CCO

echo.
echo  ============================================
echo   Gerador de Rotas - CCO
echo   Instalacao de dependencias
echo  ============================================
echo.

pushd "%~dp0"

REM Verifica se Python esta disponivel
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale o Python 3.10+ e tente novamente.
    pause
    popd
    exit /b 1
)

REM Cria ambiente virtual se nao existir
if not exist "venv" (
    echo [1/4] Criando ambiente virtual...
    python -m venv venv
) else (
    echo [1/4] Ambiente virtual ja existe.
)

REM Ativa o ambiente virtual
echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Atualiza pip
echo [3/4] Atualizando pip...
python -m pip install --upgrade pip --quiet

REM Instala dependencias
echo [4/4] Instalando dependencias (pode demorar alguns minutos)...
pip install -r requirements.txt

echo.
echo  ============================================
echo   Configuracao inicial do Django
echo  ============================================
echo.

REM Copia .env se nao existir
if not exist ".env" (
    echo [+] Criando arquivo .env a partir do exemplo...
    copy .env.example .env
    echo.
    echo  IMPORTANTE: Abra o arquivo .env e configure:
    echo   - SECRET_KEY (gere uma chave segura)
    echo   - GOOGLE_MAPS_API_KEY (sua chave da API Google Maps)
    echo.
) else (
    echo [+] Arquivo .env ja existe.
)

REM Migracoes do banco de dados
echo [+] Aplicando migracoes do banco de dados...
python manage.py makemigrations
python manage.py migrate

REM Cria superusuario opcional
echo.
set /p CREATE_SUPER="Deseja criar um superusuario para o admin Django? (s/n): "
if /i "%CREATE_SUPER%"=="s" (
    python manage.py createsuperuser
)

echo.
echo  ============================================
echo   Instalacao concluida com sucesso!
echo   Execute iniciar_8508.bat para iniciar o sistema.
echo  ============================================
echo.

popd
pause
