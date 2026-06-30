@echo off
chcp 65001 > nul
echo ============================================
echo    KSO SnapTube Turbo V2 - Build Script
echo ============================================
echo.

REM --- تحقق من Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [خطأ] Python غير مثبت! حمله من python.org
    pause & exit /b 1
)

REM --- تثبيت Chocolatey لو مش موجود ---
where choco >nul 2>&1
if errorlevel 1 (
    echo [+] تثبيت Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
       [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
       iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    call refreshenv
)

REM --- تثبيت FFmpeg و Aria2 ---
echo [+] تثبيت FFmpeg و Aria2...
choco install ffmpeg aria2 -y --no-progress
call refreshenv

REM --- إنشاء بيئة افتراضية وتثبيت المتطلبات ---
echo [+] تثبيت متطلبات Python...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

REM --- بناء EXE مع PyInstaller ---
echo [+] بناء EXE مع PyInstaller...
pyinstaller --clean --noconfirm KSO_SnapTube_Turbo_V2.spec

if not exist "dist\KSO_SnapTube_Turbo_V2.exe" (
    echo [خطأ] فشل البناء! راجع الأخطاء أعلاه.
    pause & exit /b 1
)

echo [✓] تم بناء EXE بنجاح: dist\KSO_SnapTube_Turbo_V2.exe

REM --- إنشاء المثبت مع Inno Setup ---
where iscc >nul 2>&1
if errorlevel 1 (
    echo [+] تثبيت Inno Setup...
    choco install innosetup -y --no-progress
    call refreshenv
)

echo [+] إنشاء مثبت Setup.exe...
mkdir installer_output 2>nul
iscc setup.iss

if exist "installer_output\KSO_SnapTube_Turbo_V2_Setup.exe" (
    echo.
    echo ============================================
    echo  [✓] تم الانتهاء بنجاح!
    echo  الملف: installer_output\KSO_SnapTube_Turbo_V2_Setup.exe
    echo ============================================
    explorer installer_output
) else (
    echo [!] تم بناء EXE لكن Inno Setup فشل.
    echo     الملف الجاهز: dist\KSO_SnapTube_Turbo_V2.exe
    explorer dist
)

pause
