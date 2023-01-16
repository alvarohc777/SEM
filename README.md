# SEM
ATP fault and event simulation automation tool coded in python 

This version of the tool is based on the SEM automation tool developed by: Férnandez, Mildre José and Latorre, Daniela Carolina
as a final project to obtain their Electrical Engineer title in Universidad el Norte, Barranquilla, Colombia. 

### Before Installation

Verify that solver.bat path in PFGUI.py correspond to path where solver is stored in local machine.
Paths must match:
1. PFGUI.py: lines 807, 847
2. SEMSetup.bat: line 13
3. solver.bat: line 1

### Installation

Download the latest release .zip. Extract it under a directory named "/Instalador_SEM/". After this run the SEMSetup.bat, this will install
python (if not installed already), create a virtual environment and all of the project dependencies. After installation, the program will run
ready to be used.


### Run the program

To run the program, inside the created /SEM/ directory, run SEM.bat. This will automatically run PFGUI.py script.


## Spanish

Herramienta de automatización de simulación de fallos y eventos ATP codificada en python. 

Esta versión de la herramienta está basada en la herramienta de automatización SEM desarrollada por: Férnandez, Mildre José y Latorre, Daniela Carolina
como proyecto final para obtener su título de Ingeniero Electricista en la Universidad el Norte, Barranquilla, Colombia. 

### Previo a la instalación

Verifique que la ruta solver.bat en PFGUI.py corresponde a la ruta donde se almacena el solver en la máquina local.
Las rutas deben coincidir:
1. PFGUI.py: líneas 807, 847
2. SEMSetup.bat: línea 13
3. solver.bat: línea 1

### Instalación

Descargue la última versión .zip. Extráelo en un directorio llamado "/Instalador_SEM/". Después de esto ejecute el SEMSetup.bat, esto instalará
python (si no está ya instalado), creará un entorno virtual y todas las dependencias del proyecto. Después de la instalación, el programa se ejecutará
listo para ser utilizado.

## Ejecutar el programa

Para ejecutar el programa, dentro del directorio /SEM/ creado, ejecute SEM.bat. Esto ejecutará automáticamente el script PFGUI.py.


#### Tareas pendientes

- [ ] Revisar la licencia del repo [readPL4](https://github.com/ldemattos/readPL4) y mencionar que se utilizó en la función readPL4() de PFGUI.py.
      Actualizar licencia acorde a lo anterior.
- [ ] Crear un ejecutable de todo el programa. Por alguna razón al agreagar multiprocess, ya no compila correctamente un ejecutable.

