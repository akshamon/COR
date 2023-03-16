:: Check if python is installed.
python --version 2>NUL
if errorlevel 1 goto pythonNotInstalled

:: Installs requirements if needed

pip install selenium
python -m pip install selenium
pip install Colorama
pip install opencv-python

cls

:: Launches the test
python src\luna_cor_automation\__init__.py
goto:eof

:pythonNotInstalled
echo Error^: Python is not installed or not configured correctly.
pause