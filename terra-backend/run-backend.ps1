# Run from any working directory: .\run-backend.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$jar = Join-Path $PSScriptRoot 'target\terra-backend-0.0.1-SNAPSHOT.jar'
$settings = Join-Path $PSScriptRoot '.env'
if (-not (Test-Path $jar)) { throw 'Backend JAR missing. Build it once using .\mvnw.cmd clean package.' }
if (-not (Test-Path $settings)) { throw 'Create .env from .env.example and enter your local settings first.' }

$candidates = @()
if ($env:JAVA_HOME) { $candidates += Join-Path $env:JAVA_HOME 'bin\java.exe' }
$onPath = Get-Command java -ErrorAction SilentlyContinue
if ($onPath) { $candidates += $onPath.Source }
foreach ($base in @('Java','Eclipse Adoptium','Microsoft')) {
    $parent = Join-Path $env:ProgramFiles $base
    if (Test-Path $parent) {
        Get-ChildItem $parent -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $candidates += Join-Path $_.FullName 'bin\java.exe'
        }
    }
}
$java = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (-not (Test-Path $candidate)) { continue }
    try {
        $version = (& $candidate --version 2>&1 | Out-String)
        if ($LASTEXITCODE -eq 0 -and $version -match '(?:openjdk|java)\s+(\d+)' -and [int]$matches[1] -ge 25) {
            $java = $candidate
            break
        }
    } catch { continue }
}
if (-not $java) { throw 'Java 25+ was not found. Install a compatible JDK or set JAVA_HOME to it.' }

# This local file is authoritative for keys it defines; remove stale shell exports.
Get-Content $settings | ForEach-Object {
    if ($_ -match '^\s*([A-Z][A-Z0-9_]+)=') {
        [Environment]::SetEnvironmentVariable($matches[1], $null, 'Process')
    }
}
Write-Host 'Starting Terra backend with local .env configuration.'
& $java -jar $jar '--spring.config.import=file:./.env[.properties]'
exit $LASTEXITCODE
