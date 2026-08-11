[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z][a-z0-9-]{2,11}$')]
    [string]$Prefix,

    [string]$ResourceGroup = "$Prefix-rg",
    [string]$Location = 'eastus'
)

$ErrorActionPreference = 'Stop'
$azureCliDirectory = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
if (-not (Get-Command az -ErrorAction SilentlyContinue) -and (Test-Path $azureCliDirectory)) {
    $env:Path = "$azureCliDirectory;$env:Path"
}
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI was not found. Install it before running this script.'
}
$imageTag = (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss')
$template = Join-Path $PSScriptRoot 'main.bicep'

az group create --name $ResourceGroup --location $Location --output none

$foundation = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $template `
    --parameters prefix=$Prefix deployJob=false imageTag=$imageTag `
    --query properties.outputs `
    --output json | ConvertFrom-Json

$registryName = $foundation.registryName.value
az acr build `
    --registry $registryName `
    --image "geo-monitor:$imageTag" `
    --file (Join-Path $PSScriptRoot '..\Dockerfile') `
    (Join-Path $PSScriptRoot '..')

$deployment = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $template `
    --parameters prefix=$Prefix deployJob=true imageTag=$imageTag `
    --query properties.outputs `
    --output json | ConvertFrom-Json

Write-Host "Job: $($deployment.jobName.value)"
Write-Host "Image: $($deployment.imageName.value)"
Write-Host "Sender: $($deployment.emailSender.value)"
Write-Host 'Schedule: hourly at minute 0 (UTC)'