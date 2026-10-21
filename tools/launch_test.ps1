param(
    [string]$GameArgs = "",
    [string]$EngineArgs = "",
    [int]$Port = 47811,
    [string]$GameDir = (Join-Path $PSScriptRoot "..\testgame"),
    [string]$Resolution = "1600x900",
    [switch]$Headless
)
# Starts the TEST copy of Dice Rush on a separate Windows virtual desktop ("BDR Test"),
# so the user's visible desktop is never used. The game is driven through the test harness.
$ErrorActionPreference = "Stop"
# VirtualDesktop11.exe (https://github.com/MScholtes/VirtualDesktop) keeps the test game off your own desktop
$vd = Join-Path $PSScriptRoot "vdesk\VirtualDesktop11.exe"
$exe = Join-Path $GameDir "Dice Rush.exe"

if ($Headless) {
    $p = Start-Process -FilePath $exe -WorkingDirectory $GameDir -ArgumentList "--headless -- --bdr-port=$Port $GameArgs" -PassThru -WindowStyle Hidden
    "PID=$($p.Id) HEADLESS"
    exit 0
}

$list = (& $vd /List) -join "`n"
if ($list -notmatch "BDR Test") {
    & $vd /Quiet /New /Name:"BDR Test" | Out-Null
}

$argsLine = "--windowed --position -24000,-24000 --resolution $Resolution $EngineArgs -- --bdr-port=$Port $GameArgs"
$p = Start-Process -FilePath $exe -WorkingDirectory $GameDir -ArgumentList $argsLine -PassThru
$hwnd = [IntPtr]::Zero
for ($i = 0; $i -lt 200; $i++) {
    Start-Sleep -Milliseconds 50
    $p.Refresh()
    if ($p.HasExited) { "EXITED"; exit 1 }
    if ($p.MainWindowHandle -ne [IntPtr]::Zero) { $hwnd = $p.MainWindowHandle; break }
}
if ($hwnd -eq [IntPtr]::Zero) { "NO_WINDOW PID=$($p.Id)"; exit 1 }
& $vd /Quiet /GetDesktop:"BDR Test" /MoveWindowHandle:$($hwnd.ToInt64()) | Out-Null
$onDesk = & $vd /GetDesktopFromWindowHandle:$($hwnd.ToInt64())
"PID=$($p.Id) HWND=$($hwnd.ToInt64()) $onDesk"
