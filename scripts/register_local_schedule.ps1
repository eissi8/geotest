[CmdletBinding()]
param(
    [string]$TaskName = 'GEO Trace Hourly Monitor',
    [string]$Prefix = 'geotrace',
    [string]$ResourceGroup = 'geotrace-rg',
    [string]$SubscriptionId = '09538c3e-f9a6-49b8-a42c-81eb0b402198'
)

$ErrorActionPreference = 'Stop'
$azureCliDirectory = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
if (-not (Get-Command az -ErrorAction SilentlyContinue) -and (Test-Path $azureCliDirectory)) {
    $env:Path = "$azureCliDirectory;$env:Path"
}
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) {
    throw 'Azure CLI authentication is unavailable. Run az login first.'
}
$userObjectId = az ad signed-in-user show --query id --output tsv
$communicationScope = az resource show `
    --resource-group $ResourceGroup `
    --resource-type 'Microsoft.Communication/communicationServices' `
    --name "$Prefix-communication" `
    --query id `
    --output tsv
if (-not $userObjectId -or -not $communicationScope) {
    throw 'Could not resolve the current Azure user or Communication Services resource.'
}
az role assignment create `
    --assignee-object-id $userObjectId `
    --assignee-principal-type User `
    --role '09976791-48a7-449e-bb21-39d1a415f350' `
    --scope $communicationScope `
    --output none
if ($LASTEXITCODE -ne 0) {
    throw 'Could not grant Azure Communication Services email permission.'
}

$pythonPath = (Get-Command python -ErrorAction Stop).Source
$runnerPath = Join-Path $PSScriptRoot 'run_local_monitor.ps1'
$powerShellPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = @(
    '-NoProfile'
    '-NonInteractive'
    '-ExecutionPolicy Bypass'
    "-File `"$runnerPath`""
    "-Prefix `"$Prefix`""
    "-ResourceGroup `"$ResourceGroup`""
    "-SubscriptionId `"$SubscriptionId`""
    "-PythonPath `"$pythonPath`""
) -join ' '

$action = New-ScheduledTaskAction -Execute $powerShellPath -Argument $arguments
$nextHour = (Get-Date).AddHours(1).Date.AddHours((Get-Date).AddHours(1).Hour)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $nextHour `
    -RepetitionInterval (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Runs the anonymous ChatGPT GEO visibility probe every hour.' `
    -Force | Out-Null

Write-Host "Registered '$TaskName'. First run: $nextHour"