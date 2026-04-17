@echo off
:: install.bat - Windows installation script for Krita Layers2PDF plugin

echo 📁 Installing Krita Layers2PDF plugin...

:: Krita pykrita path
set KRITA_PYKRITA=%APPDATA%\krita\pykrita

:: Create folder if it doesn't exist
if not exist "%KRITA_PYKRITA%" mkdir "%KRITA_PYKRITA%"

:: Copy plugin folder
if exist "layers2pdf" (
    xcopy /E /I /Y layers2pdf "%KRITA_PYKRITA%\layers2pdf"
    
    if not exist "%KRITA_PYKRITA%\layers2pdf" (
        echo ❌ ERROR: Failed to copy 'layers2pdf' folder to %KRITA_PYKRITA%
        echo    Check permissions and disk space.
        pause
        exit /b 1
    )
    echo    ✅ Plugin folder copied
) else (
    echo ❌ ERROR: 'layers2pdf' folder not found!
    echo    Make sure you run this script from the repository root.
    pause
    exit /b 1
)

:: Copy .desktop file to the same location
if exist "layers2pdf.desktop" (
    copy /Y layers2pdf.desktop "%KRITA_PYKRITA%"
    
    if not exist "%KRITA_PYKRITA%\layers2pdf.desktop" (
        echo ❌ ERROR: Failed to copy 'layers2pdf.desktop' to %KRITA_PYKRITA%
        echo    Check permissions and disk space.
        pause
        exit /b 1
    )
    echo    ✅ Desktop file copied
) else (
    echo ❌ ERROR: 'layers2pdf.desktop' file not found!
    echo    Make sure you run this script from the repository root.
    pause
    exit /b 1
)

echo.
echo ✅ Plugin installed successfully!
echo.
echo 📌 Next steps:
echo    1. Restart Krita
echo    2. Go to Settings → Configure Krita → Python Plugin Manager
echo    3. Enable 'Export Layers to PDF' plugin
echo    4. Restart Krita again
echo.
pause
