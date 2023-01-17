@echo off
title SEM
echo Ejecutando herramienta computacional SEM
call SEM\Scripts\activate
echo Inizializando herramienta SEM
python PFGUI.py
echo Herramienta cerrada
pause
