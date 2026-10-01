param([switch]$Debug, [switch]$Check)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

try {
    $sourceRoot = $PSScriptRoot
    $pointerPath = Join-Path $PSScriptRoot 'REPO.pointer.json'
    if (Test-Path -LiteralPath $pointerPath) {
        $pointer = Get-Content -LiteralPath $pointerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($pointer.schema -ne 'ellmos-repo-pointer-v1' -or
            $pointer.repo_id -ne 'doc-bricks/DokuReader' -or
            $pointer.profile -ne 'plan-d-code' -or
            $pointer.authority.git -ne 'local-checkout-plus-github' -or
            $pointer.local_locator.windows_default -isnot [string] -or
            $pointer.local_locator.windows_default -notmatch '^[A-Za-z]:[\\/]') {
            throw 'Der Plan-D-Pointer für DokuReader ist ungültig.'
        }
        $sourceRoot = [IO.Path]::GetFullPath($pointer.local_locator.windows_default)
    }
    $mainPath = Join-Path $sourceRoot 'DokuReader.py'
    $bootstrap = Join-Path $sourceRoot 'launch_source.py'
    if (-not (Test-Path -LiteralPath $mainPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $bootstrap -PathType Leaf)) {
        throw "Der aktuelle DokuReader-Quellcode fehlt: $sourceRoot"
    }

    $consolePython = Join-Path $sourceRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $consolePython -PathType Leaf)) {
        $command = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue |
            Where-Object { $_.Source -notmatch '\\WindowsApps\\' } | Select-Object -First 1
        if ($null -eq $command) {
            throw 'Python wurde nicht gefunden. Bitte Python und requirements.txt installieren.'
        }
        $consolePython = $command.Source
    }
    # Probe the actual interpreter without importing site or running the app.
    $probe = New-Object System.Diagnostics.Process
    try {
        $probe.StartInfo.FileName = $consolePython
        $probe.StartInfo.Arguments = '-I -S -B -c "import sys,json; print(json.dumps(dict(executable=sys.executable,version=list(sys.version_info[:3]))))"'
        $probe.StartInfo.UseShellExecute = $false
        $probe.StartInfo.CreateNoWindow = $true
        $probe.StartInfo.RedirectStandardOutput = $true
        $probe.StartInfo.RedirectStandardError = $true
        $probe.Start() | Out-Null
        if (-not $probe.WaitForExit(5000)) {
            $probe.Kill()
            if (-not $probe.WaitForExit(2000)) { throw 'Die Python-Startprüfung konnte nicht beendet werden.' }
            throw 'Die Python-Startprüfung hat das Zeitlimit erreicht.'
        }
        if ($probe.ExitCode -ne 0) { throw 'Der gewählte Python-Interpreter ist nicht ausführbar.' }
        $pythonInfo = $probe.StandardOutput.ReadToEnd() | ConvertFrom-Json
        if ($pythonInfo.version[0] -lt 3 -or ($pythonInfo.version[0] -eq 3 -and $pythonInfo.version[1] -lt 10)) {
            throw 'DokuReader benötigt Python 3.10 oder neuer.'
        }
        $consolePython = $pythonInfo.executable
    } finally {
        $probe.Dispose()
    }
    $python = $consolePython
    if (-not $Debug) {
        $windowPython = Join-Path (Split-Path -Parent $consolePython) 'pythonw.exe'
        if (Test-Path -LiteralPath $windowPython -PathType Leaf) {
            $consoleVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($consolePython).ProductVersion
            $windowVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($windowPython).ProductVersion
            if ($consoleVersion -eq $windowVersion) { $python = $windowPython }
        }
    }
    if ($Check) {
        @{ source_root = $sourceRoot; python = $python; bootstrap = $bootstrap; debug = [bool]$Debug } |
            ConvertTo-Json -Compress
        exit 0
    }
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'
    if ($Debug) {
        & $python $bootstrap --debug
        exit $LASTEXITCODE
    }
    Start-Process -FilePath $python -ArgumentList ('"' + $bootstrap + '"') -WorkingDirectory $sourceRoot -WindowStyle Hidden
    exit 0
} catch {
    $message = $_.Exception.Message
    if ($Check -or $Debug) {
        [Console]::Error.WriteLine($message)
    } else {
        try {
            $localBase = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
            if ([string]::IsNullOrWhiteSpace($localBase)) { throw 'Lokaler Logpfad fehlt.' }
            $logDirectory = Join-Path $localBase 'DokuReader\logs'
            [IO.Directory]::CreateDirectory($logDirectory) | Out-Null
            $logPath = Join-Path $logDirectory 'starter-error.log'
            [IO.File]::WriteAllText($logPath, $message, (New-Object System.Text.UTF8Encoding($false)))
            $message += "`n`nProtokoll: $logPath"
        } catch {
            $message += "`nDas lokale Startprotokoll konnte nicht angelegt werden."
        }
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.MessageBox]::Show($message, 'DokuReader – Startfehler', 'OK', 'Error') | Out-Null
        exit 2 # Message already shown; WSH must not show a second dialog.
    }
    exit 1
}
