@echo off
title Iniciando Email Automation Web
echo ==========================================
echo   INICIANDO O SISTEMA DE AUTOMACAO
echo ==========================================
echo.
echo Abrindo o navegador...
start "" http://localhost:8000
echo.
echo Iniciando o servidor Python...
:: Tenta ativar o ambiente virtual se ele existir
if exist venv (call venv\Scripts\activate)
python -m uvicorn app.main:app
pause