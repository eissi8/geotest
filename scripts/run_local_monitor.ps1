[CmdletBinding()]
param(
    [string]$Prefix = 'geotrace',
    [string]$ResourceGroup = 'geotrace-rg',
    [string]$SubscriptionId = '09538c3e-f9a6-49b8-a42c-81eb0b402198',
    [string]$PythonPath = 'python'
)

$ErrorActionPreference = 'Stop'
$azureCliDirectory = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
if (-not (Get-Command az -ErrorAction SilentlyContinue) -and (Test-Path $azureCliDirectory)) {
    $env:Path = "$azureCliDirectory;$env:Path"
}
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI was not found.'
}
$repositoryRoot = Split-Path $PSScriptRoot -Parent
$logDirectory = Join-Path $repositoryRoot 'logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$logPath = Join-Path $logDirectory "monitor-$((Get-Date).ToString('yyyyMMdd-HHmmss')).log"

Start-Transcript -Path $logPath
try {
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) {
        throw 'Azure CLI authentication is unavailable. Run az login before the next probe.'
    }

    $emailDomainUrl = "https://management.azure.com/subscriptions/$SubscriptionId" +
        "/resourceGroups/$ResourceGroup/providers/Microsoft.Communication" +
        "/emailServices/$Prefix-email/domains/AzureManagedDomain?api-version=2023-03-31"
    $senderDomain = az rest `
        --method get `
        --url $emailDomainUrl `
        --query 'properties.mailFromSenderDomain' `
        --output tsv
    if ($LASTEXITCODE -ne 0 -or -not $senderDomain) {
        throw 'Could not resolve the Azure Communication Services sender domain.'
    }

    $env:ACS_EMAIL_ENDPOINT = "https://$Prefix-communication.communication.azure.com"
    $env:EMAIL_SENDER = "DoNotReply@$senderDomain"
    $env:EMAIL_RECIPIENT = 'junghunlee@microsoft.com'
    $env:PLAYWRIGHT_HEADLESS = 'false'
    $env:CHATGPT_TIMEOUT_SECONDS = '45'

    Push-Location $repositoryRoot
    try {
        & $PythonPath -m geo_monitor.main
        if ($LASTEXITCODE -ne 0) {
            throw "GEO monitor exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    Stop-Transcript
}