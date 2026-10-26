[CmdletBinding()]
param(
  [Parameter(Mandatory, Position = 0)]
  [ValidateSet("init", "fmt", "validate", "plan", "apply", "reconcile", "connect", "status", "start", "stop", "destroy")]
  [string]$Action,

  [string]$Environment = "aks-learning",

  [string]$VarFile = "components\azure-aks-cluster\terraform.tfvars",

  [switch]$AllowDestructive,

  [switch]$AutoApprove
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentPath = Join-Path $repoRoot "environments\$Environment"
$modulePath = Join-Path $repoRoot "components\azure-aks-cluster"
$varFilePath = if ([System.IO.Path]::IsPathRooted($VarFile)) {
  $VarFile
}
else {
  Join-Path $repoRoot $VarFile
}
$reconcileScript = Join-Path $repoRoot "python\azure_aks_cluster\reconcile.py"

if (-not (Test-Path -LiteralPath $environmentPath -PathType Container)) {
  throw "Environment directory not found: $environmentPath"
}

function Assert-Command {
  param([Parameter(Mandatory)][string]$Name)

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Invoke-ExternalCommand {
  param(
    [Parameter(Mandatory)][string]$Command,
    [Parameter(Mandatory)][string[]]$Arguments,
    [Parameter(Mandatory)][string]$WorkingDirectory
  )

  Push-Location $WorkingDirectory
  try {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
      throw "$Command failed with exit code $LASTEXITCODE."
    }
  }
  finally {
    Pop-Location
  }
}

function Assert-VarFile {
  if (-not (Test-Path -LiteralPath $varFilePath -PathType Leaf)) {
    throw "Missing $varFilePath. Copy components\azure-aks-cluster\terraform.tfvars.example to terraform.tfvars in the same directory and set your values first."
  }
}

function Get-TerraformOutput {
  param([Parameter(Mandatory)][string]$Name)

  Push-Location $environmentPath
  try {
    $value = & terraform output -raw $Name
    if ($LASTEXITCODE -ne 0) {
      throw "Unable to read Terraform output '$Name'. Apply the environment first."
    }
    return $value.Trim()
  }
  finally {
    Pop-Location
  }
}

Assert-Command -Name "terraform"

switch ($Action) {
  "init" {
    Invoke-ExternalCommand -Command "terraform" -Arguments @("init") -WorkingDirectory $environmentPath
  }

  "fmt" {
    Invoke-ExternalCommand -Command "terraform" -Arguments @("fmt") -WorkingDirectory $modulePath
    Invoke-ExternalCommand -Command "terraform" -Arguments @("fmt") -WorkingDirectory $environmentPath
  }

  "validate" {
    Assert-VarFile
    Assert-Command -Name "python"
    Invoke-ExternalCommand -Command "python" -Arguments @($reconcileScript, "--environment", $Environment, "--var-file", $varFilePath, "--validate-only") -WorkingDirectory $repoRoot
  }

  "plan" {
    Assert-VarFile
    Assert-Command -Name "python"
    Invoke-ExternalCommand -Command "python" -Arguments @($reconcileScript, "--environment", $Environment, "--var-file", $varFilePath) -WorkingDirectory $repoRoot
  }

  "apply" {
    Assert-VarFile
    Assert-Command -Name "python"
    $arguments = @($reconcileScript, "--environment", $Environment, "--var-file", $varFilePath, "--apply")
    if ($AllowDestructive) { $arguments += "--allow-destructive" }
    if ($AutoApprove) { $arguments += "--auto-approve" }
    Invoke-ExternalCommand -Command "python" -Arguments $arguments -WorkingDirectory $repoRoot
  }

  "reconcile" {
    Assert-VarFile
    Assert-Command -Name "python"
    $arguments = @($reconcileScript, "--environment", $Environment, "--var-file", $varFilePath, "--apply")
    if ($AllowDestructive) { $arguments += "--allow-destructive" }
    if ($AutoApprove) { $arguments += "--auto-approve" }
    Invoke-ExternalCommand -Command "python" -Arguments $arguments -WorkingDirectory $repoRoot
  }

  "connect" {
    Assert-Command -Name "az"
    Assert-Command -Name "kubectl"
    $resourceGroup = Get-TerraformOutput -Name "resource_group_name"
    $clusterName = Get-TerraformOutput -Name "cluster_name"
    Invoke-ExternalCommand -Command "az" -Arguments @("aks", "get-credentials", "--resource-group", $resourceGroup, "--name", $clusterName, "--overwrite-existing") -WorkingDirectory $environmentPath
    Invoke-ExternalCommand -Command "kubectl" -Arguments @("get", "nodes", "-L", "kubernetes.io/arch") -WorkingDirectory $environmentPath
  }

  "status" {
    Assert-Command -Name "az"
    $resourceGroup = Get-TerraformOutput -Name "resource_group_name"
    $clusterName = Get-TerraformOutput -Name "cluster_name"
    Invoke-ExternalCommand -Command "az" -Arguments @("aks", "show", "--resource-group", $resourceGroup, "--name", $clusterName, "--query", "{name:name,powerState:powerState.code,provisioningState:provisioningState}", "--output", "table") -WorkingDirectory $environmentPath
  }

  "start" {
    Assert-Command -Name "az"
    $resourceGroup = Get-TerraformOutput -Name "resource_group_name"
    $clusterName = Get-TerraformOutput -Name "cluster_name"
    Invoke-ExternalCommand -Command "az" -Arguments @("aks", "start", "--resource-group", $resourceGroup, "--name", $clusterName) -WorkingDirectory $environmentPath
  }

  "stop" {
    Assert-Command -Name "az"
    $resourceGroup = Get-TerraformOutput -Name "resource_group_name"
    $clusterName = Get-TerraformOutput -Name "cluster_name"
    Invoke-ExternalCommand -Command "az" -Arguments @("aks", "stop", "--resource-group", $resourceGroup, "--name", $clusterName) -WorkingDirectory $environmentPath
  }

  "destroy" {
    Assert-VarFile
    Invoke-ExternalCommand -Command "terraform" -Arguments @("init") -WorkingDirectory $environmentPath
    Invoke-ExternalCommand -Command "terraform" -Arguments @("destroy", "-var-file=$varFilePath") -WorkingDirectory $environmentPath
  }
}
