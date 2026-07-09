# run_dev.ps1 - Windows equivalent of run_dev.sh
# Builds, starts an AVD (if needed), installs and launches the SafeDrive debug
# app directly into MainActivity, removes stray debug apps from other
# projects, fixes an off-screen emulator window, then tails filtered logcat.
# Usage: .\run_dev.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$PKG = "com.sukhman.safedrive"
$ACTIVITY = ".MainActivity"
$AVD_ARGS = @("-no-snapshot", "-gpu", "swiftshader_indirect")
$LOG_FILTER = "FrameAnalyzer|DistractionEngine|AlertManager|SensorsManager|LocationHelper|MainActivity"

# --- Resolve Android SDK tools ---
$sdkDir = $null
$localProps = Join-Path $PSScriptRoot "local.properties"
if (Test-Path $localProps) {
    $line = Select-String -Path $localProps -Pattern "^sdk\.dir=" | Select-Object -First 1
    if ($line) {
        # local.properties uses Java properties escaping (\: -> :, \\ -> \)
        $sdkDir = ($line.Line -replace "^sdk\.dir=", "") -replace '\\(.)', '$1'
    }
}
if (-not $sdkDir) { $sdkDir = $env:ANDROID_HOME }
if (-not $sdkDir) { $sdkDir = $env:ANDROID_SDK_ROOT }
if (-not $sdkDir -or -not (Test-Path $sdkDir)) {
    Write-Error "Could not resolve Android SDK path. Set sdk.dir in local.properties or ANDROID_HOME."
}

$adb = Join-Path $sdkDir "platform-tools\adb.exe"
$emulator = Join-Path $sdkDir "emulator\emulator.exe"
if (-not (Test-Path $adb)) { Write-Error "adb.exe not found at $adb" }

# --- Ensure a device is up ---
Write-Host "Checking for connected devices..."
$deviceLines = & $adb devices | Select-Object -Skip 1 | Where-Object { $_.Trim() -ne "" }

if (-not $deviceLines) {
    Write-Host "No device/emulator found. Looking for available AVDs..."
    if (-not (Test-Path $emulator)) { Write-Error "No emulator binary found at $emulator" }
    $avdList = & $emulator -list-avds
    if (-not $avdList) {
        Write-Error "No AVDs found. Create one via Android Studio AVD Manager or avdmanager."
    }
    $avdName = ($avdList | Select-Object -First 1).Trim()
    Write-Host "Starting AVD: $avdName"
    # Launched via WMI (not Start-Process) so the emulator process is fully
    # detached from this script's job object - otherwise, if this script's
    # own process later gets force-stopped/timed out by whatever launched
    # it, Windows job-object cleanup can silently kill the emulator too.
    $commandLine = "`"$emulator`" -avd `"$avdName`" $($AVD_ARGS -join ' ')"
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $commandLine } | Out-Null

    Write-Host "Waiting for emulator to boot..."
    & $adb wait-for-device

    $booted = $false
    for ($i = 0; $i -lt 60; $i++) {
        $prop = (& $adb shell getprop sys.boot_completed 2>$null) -replace "`r", ""
        if ($prop -eq "1") { $booted = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $booted) {
        Write-Warning "Emulator did not finish booting in time. Proceeding but device may be unavailable."
    } else {
        Write-Host "Emulator booted."
    }
} else {
    Write-Host "Device(s) detected. Proceeding to build/install."
}

# --- Fix an off-screen emulator window (seen this session: window can spawn
#     with a negative Y position, reported visible/non-minimized by Windows
#     but never actually on screen) ---
Add-Type -AssemblyName System.Windows.Forms

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
namespace RunDev {
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public class Win32Fix {
        [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
        [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    }
}
"@ -ErrorAction SilentlyContinue

$qemuProc = Get-Process -Name "qemu-system-x86_64" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($qemuProc -and $qemuProc.MainWindowHandle -ne 0) {
    $rect = New-Object RunDev.RECT
    [RunDev.Win32Fix]::GetWindowRect($qemuProc.MainWindowHandle, [ref]$rect) | Out-Null
    $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    if ($rect.Top -lt $screen.Top -or $rect.Left -lt $screen.Left -or $rect.Top -gt $screen.Bottom -or $rect.Left -gt $screen.Right) {
        Write-Host "Emulator window is off-screen (Top=$($rect.Top), Left=$($rect.Left)) - moving it into view."
        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top
        [RunDev.Win32Fix]::MoveWindow($qemuProc.MainWindowHandle, 100, 50, $width, $height, $true) | Out-Null
    }
    [RunDev.Win32Fix]::SetForegroundWindow($qemuProc.MainWindowHandle) | Out-Null
}

# --- Build the debug APK ---
Write-Host "Building app (assembleDebug)..."
& .\gradlew.bat ":app:assembleDebug" "--stacktrace"
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed." }

# --- Install the debug APK ---
Write-Host "Installing APK..."
& .\gradlew.bat ":app:installDebug"
if ($LASTEXITCODE -ne 0) { Write-Error "Install failed." }

# --- Remove stray debug apps from other projects sharing this AVD ---
Write-Host "Removing non-SafeDrive third-party packages from the device..."
$thirdParty = & $adb shell pm list packages -3
foreach ($line in $thirdParty) {
    # NOTE: PowerShell variable names are case-insensitive - do not name this $pkg,
    # it would alias the same storage as the script-level $PKG constant below.
    $candidatePackage = ($line -replace "^package:", "").Trim()
    if ($candidatePackage -and $candidatePackage -ne $PKG) {
        Write-Host "  Uninstalling $candidatePackage"
        & $adb uninstall $candidatePackage | Out-Null
    }
}

# --- Launch the app directly (bypasses the home screen/app drawer) ---
Write-Host "Launching $PKG/$ACTIVITY"
& $adb shell am start -n "$PKG/$ACTIVITY"

# --- Grant required permissions (for debug builds) ---
& $adb shell pm grant $PKG android.permission.CAMERA
& $adb shell pm grant $PKG android.permission.RECORD_AUDIO
& $adb shell pm grant $PKG android.permission.ACCESS_FINE_LOCATION

# --- Tail filtered logcat ---
Write-Host "Tailing logcat (Ctrl+C to stop). Filtering tags: $LOG_FILTER"
& $adb logcat -v time | Select-String -Pattern $LOG_FILTER
