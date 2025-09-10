@echo off
echo Instagram Downloader Installer
echo ============================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Downloading Python installer...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
    echo Installing Python...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

:: Create virtual environment and install dependencies
echo Setting up Instagram Downloader...
python -m venv env
call env\Scripts\activate.bat

:: Install required packages
echo Installing required packages...
python -m pip install --upgrade pip
pip install requests beautifulsoup4 tqdm pillow pyinstaller

:: Build the executable
echo Building Instagram Downloader...
python build_exe.py

:: Create Desktop shortcut
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\Desktop\Instagram Downloader.lnk") >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%CD%\dist\instagram-dl.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%\dist" >> %SCRIPT%
echo oLink.Description = "Instagram Downloader" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo Installation complete!
echo The Instagram Downloader has been installed on your desktop.
echo.
echo You can now:
echo 1. Double-click the "Instagram Downloader" icon on your desktop
echo 2. Or run it from command line: dist\instagram-dl --help
echo.
pause
