param(
    [string]$Owner,
    [string]$RepoName,
    [ValidateSet('private', 'public')]
    [string]$Visibility,
    [string]$Description = 'Local-first pre-plan checkpoint tooling for discussion-to-brief and workbench proposal workflows.',
    [switch]$SkipPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$localConfigPath = Join-Path $repoRoot 'config\local.toml'

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

if (-not $RepoName) {
    $RepoName = Split-Path -Leaf $repoRoot
}

if (-not $Owner) {
    $Owner = Get-TomlStringValue -ConfigPath $localConfigPath -Key 'owner'
}

if (-not $Visibility) {
    $Visibility = Get-TomlStringValue -ConfigPath $localConfigPath -Key 'visibility'
}

if (-not $Owner) {
    throw 'GitHub owner is required. Set it in config/local.toml or pass -Owner.'
}

if (-not $Visibility) {
    $Visibility = 'private'
}

$remoteUrl = "https://github.com/$Owner/$RepoName.git"
$existingRemote = git -C $repoRoot remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $existingRemote) {
    throw "Remote origin already exists: $existingRemote"
}

$createArgs = @(
    'repo', 'create', "$Owner/$RepoName",
    "--$Visibility",
    '--source', $repoRoot,
    '--remote', 'origin',
    '--description', $Description
)

if (-not $SkipPush) {
    $createArgs += '--push'
}

gh @createArgs

Write-Host "remote_url=$remoteUrl"
