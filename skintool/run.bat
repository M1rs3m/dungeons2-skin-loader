@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python не найден. Установите Python 3.10+ с https://www.python.org/downloads/ ^(галочка "Add python.exe to PATH"^)
  pause & exit /b 1
)
python -c "import PIL, numpy" >nul 2>nul
if errorlevel 1 (
  echo Ставлю зависимости: Pillow и numpy...
  python -m pip install pillow numpy
)
python gui.py
