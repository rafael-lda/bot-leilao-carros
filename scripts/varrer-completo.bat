@echo off
rem Duplo clique: roda uma varredura do Bot Leilao Carros agora (fora do agendamento),
rem COM todos os leiloeiros ativos, inclusive os pagos (Milan, pelo Apify: ~US$ 0,16 a 0,40).
rem Para o dia a dia sem custo: varrer.bat.
rem Usa o Python do ambiente venv do projeto; nao precisa ativar nada.
chcp 65001 >nul
title Bot Leilao Carros - varredura completa
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
    echo Nao achei venv\Scripts\python.exe nesta pasta. Crie o ambiente antes:
    echo   python -m venv venv
    echo   venv\Scripts\Activate.ps1
    echo   pip install -e ".[dev]"
    pause
    exit /b 1
)
"venv\Scripts\python.exe" -m bot_leilao varrer %*
set CODIGO=%errorlevel%
echo.
if "%CODIGO%"=="0" (echo Varredura concluida. Relatorio na pasta 1OUTPUT.) else (echo A varredura terminou com codigo %CODIGO%. Veja as mensagens acima.)
echo.
pause
