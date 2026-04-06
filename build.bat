@echo off
cd /d "%~dp0"
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Gerando executavel...
pyinstaller --onefile --console --name "InternetChecker" tester.py
echo.
echo Pronto! O executavel esta em: dist\InternetChecker.exe
echo.
pause
