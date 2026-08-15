# set_pagefile.ps1
try {
    $cs = Get-CimInstance Win32_ComputerSystem
    Set-CimInstance -InputObject $cs -Property @{AutomaticManagedPagefile=$false}
    $pf = Get-CimInstance Win32_PageFileSetting
    if ($pf) {
        Set-CimInstance -InputObject $pf -Property @{InitialSize=16384; MaximumSize=32768}
        Write-Host "✅ Pagefile successfully updated to 16GB - 32GB!"
    } else {
        Write-Host "⚠️ PageFileSetting object not found."
    }
} catch {
    Write-Host "Error setting pagefile: $_"
}
