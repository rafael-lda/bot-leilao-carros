# Cria (ou recria) a tarefa agendada do Bot Leilão Carros no Windows.
#
# Uso, no PowerShell, na raiz do projeto:
#     powershell -ExecutionPolicy Bypass -File scripts\agendar_windows.ps1
#
# Roda `python -m bot_leilao varrer` às segundas, quartas e sextas, às 08:00.
# Se o notebook estiver desligado ou dormindo nessa hora, a tarefa roda assim que
# o Windows puder (uma única vez, sem acumular as execuções perdidas).
#
# Para testar agora:   Start-ScheduledTask -TaskName "Bot Leilao Carros"
# Para remover:        Unregister-ScheduledTask -TaskName "Bot Leilao Carros" -Confirm:$false

$ErrorActionPreference = "Stop"

$NomeTarefa = "Bot Leilao Carros"
$Raiz = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $Raiz "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Não achei $Python. Crie o ambiente antes: python -m venv venv ; venv\Scripts\Activate.ps1 ; pip install -e "".[dev]"""
}

# python.exe (e não pythonw.exe): o bot escreve no console, e pythonw não tem saída.
$Acao = New-ScheduledTaskAction -Execute $Python -Argument "-m bot_leilao varrer" -WorkingDirectory $Raiz

$Gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Wednesday, Friday -At "08:00"

$Config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew

# Roda com o seu usuário, só quando você estiver conectado (não pede senha).
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
}

Register-ScheduledTask -TaskName $NomeTarefa -Action $Acao -Trigger $Gatilho -Settings $Config -Principal $Principal `
    -Description "Varre o Vip Leilões e avisa no Telegram os carros novos (Bot Leilão Carros)." | Out-Null

Write-Host ""
Write-Host "Tarefa '$NomeTarefa' criada: segunda, quarta e sexta às 08:00." -ForegroundColor Green
Write-Host "Pasta de trabalho: $Raiz"
Write-Host "Teste agora com:   Start-ScheduledTask -TaskName ""$NomeTarefa"""
Write-Host "Log da execução:   $Raiz\dados\logs\bot-leilao.log"
