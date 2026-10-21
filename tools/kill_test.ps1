# Stops only the TEST copy of Dice Rush (..\testgame) - never the real game the user may be playing.
$testDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\testgame"))
Get-CimInstance Win32_Process -Filter "Name = 'Dice Rush.exe'" |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($testDir, [System.StringComparison]::OrdinalIgnoreCase) } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
