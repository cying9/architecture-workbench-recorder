param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('propose', 'apply')]
    [string]$Mode,

    [string]$Transcript,
    [string]$Workbench,
    [string]$Proposal,
    [string]$OutputName = 'manual-checkpoint',
    [string]$OutputDir,
    [string]$ArchiveRoot,
    [string]$Backend = 'rule-based',
    [string]$ExtractorCommand
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$cliPath = Join-Path $repoRoot 'source_code\awr\cli.py'
$defaultsPath = Join-Path $repoRoot 'config\defaults.toml'
$localConfigPath = Join-Path $repoRoot 'config\local.toml'

if (-not (Test-Path $cliPath)) {
    throw "CLI not found: $cliPath"
}

function Get-TomlStringValue {
    param(
        [string]$ConfigPath,
        [string]$Key
    )

    if (Test-Path $ConfigPath) {
        $pattern = '^\s*' + [regex]::Escape($Key) + '\s*=\s*"([^"]+)"\s*$'
        $match = Select-String -Path $ConfigPath -Pattern $pattern | Select-Object -First 1
        if ($match) {
            return $match.Matches[0].Groups[1].Value
        }
    }

    return $null
}

function Resolve-ConfigPathValue {
    param(
        [string]$Value,
        [string]$BasePath
    )

    if (-not $Value) {
        return $null
    }

    if ([System.IO.Path]::IsPathRooted($Value)) {
        return $Value
    }

    return Join-Path $BasePath $Value
}

function Get-SharedPreplanRoot {
    param(
        [string]$DefaultsPath,
        [string]$LocalConfigPath,
        [string]$RepoRoot
    )

    $localValue = Get-TomlStringValue -ConfigPath $LocalConfigPath -Key 'shared_preplan_root'
    if ($localValue) {
        return Resolve-ConfigPathValue -Value $localValue -BasePath $RepoRoot
    }

    $defaultValue = Get-TomlStringValue -ConfigPath $DefaultsPath -Key 'shared_preplan_root'
    if ($defaultValue) {
        return Resolve-ConfigPathValue -Value $defaultValue -BasePath $RepoRoot
    }

    return Join-Path $RepoRoot 'runtime\preplan'
}

if ($Mode -eq 'propose') {
    if (-not $Transcript -or -not $Workbench) {
        throw 'Both -Transcript and -Workbench are required for propose mode.'
    }

    if (-not $OutputDir) {
        $resolvedArchiveRoot = if ($ArchiveRoot) {
            $ArchiveRoot
        }
        else {
            Get-SharedPreplanRoot -DefaultsPath $defaultsPath -LocalConfigPath $localConfigPath -RepoRoot $repoRoot
        }
        $dateBucket = Get-Date -Format 'yyyy-MM-dd'
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $OutputDir = Join-Path $resolvedArchiveRoot ("checkpoints\{0}\{1}-{2}" -f $dateBucket, $stamp, $OutputName)
    }

    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

    $command = @(
        'python',
        $cliPath,
        'propose',
        '--transcript', $Transcript,
        '--workbench', $Workbench,
        '--backend', $Backend,
        '--output-dir', $OutputDir
    )
    if ($ExtractorCommand) {
        $command += @('--extractor-command', $ExtractorCommand)
    }
}
else {
    if (-not $Proposal -or -not $Workbench) {
        throw 'Both -Proposal and -Workbench are required for apply mode.'
    }

    $command = @(
        'python',
        $cliPath,
        'apply',
        '--proposal', $Proposal,
        '--workbench', $Workbench
    )
}

& $command[0] $command[1..($command.Count - 1)]
