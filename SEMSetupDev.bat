@echo off
title Instalación herramienta computacional SEM
echo Verificando versión de python
py -3.9 --version
if Errorlevel 1 START /w python-3.9.0-amd64.exe
echo Creando entorno virtual SEM
mkdir ..\SEM
xcopy ..\SEM_Repo ..\SEM /E/H/C/I
cd ..\SEM
md "ARCHIVOS CSV" InterfazQt "Lista de fallas" SCENARIOS_ATP "Sistemas de prueba"
move "*.acp" "Sistemas de prueba"
move "*.atp" "Sistemas de prueba"
move solver.bat C:\ATP\atpdraw\ATP
move SEM.ui InterfazQt
py -3.9 -m venv SEM
call SEM\Scripts\activate
echo Instalando dependencias
pip install -r requirements.txt
echo Inizializando herramienta SEM
python PFGUI.py
pause