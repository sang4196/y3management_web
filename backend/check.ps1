param(
    [ValidateSet('fast', 'db')][string]$Mode = 'fast',
    [string]$EnvFile = ''
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$localUv = Join-Path $PSScriptRoot '../.tools/uv/bin/uv.exe'
if (Test-Path $localUv) { $uvCommand = (Resolve-Path $localUv).Path }
else { $uvCommand = (Get-Command uv -ErrorAction Stop).Source }

if ($Mode -eq 'db') {
    $runArgs = @('run', '--locked')
    if ($EnvFile) { $runArgs += @('--env-file', (Resolve-Path $EnvFile).Path) }
    & $uvCommand @runArgs pytest -m postgres --require-postgres
    exit $LASTEXITCODE
}
if ($EnvFile) { throw 'The fast checks do not load environment files.' }
$checks = @(
    @('ruff', 'check'),
    @('ruff', 'format', '--check'),
    @('mypy'),
    @('pytest', '-m', 'not postgres'),
    @('lint-imports', '--no-cache')
)
foreach ($check in $checks) {
    & $uvCommand run --locked @check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
exit 0
