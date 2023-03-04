from PyQt5 import QtWidgets, QtGui, uic, QtCore
from PyQt5.QtWidgets import QFileDialog, QCheckBox
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mmap
import struct
import pandas as pd
import numpy as np
import os
import math
import cmath
import shutil
import re
import sys
import random
from subprocess import Popen, PIPE
import subprocess
import concurrent.futures
from itertools import repeat
import time
from glob import glob


def readPL4(pl4file: str):
    """This function extracts signals from a PL4 file and saves
    it as a CSV file. Function found at: https://github.com/ldemattos/readPL4.
    'Describe and read ATP's (Alternative Transients Program) PL4 binary data file format by means of reverse engineering.'

    Parameters
    ----------
    pl4file : str
        Name of .pl4 file
    """
    miscData = {"deltat": 0.0, "nvar": 0, "pl4size": 0, "steps": 0, "tmax": 0.0}

    with open("SCENARIOS_ATP\\" + pl4file, "rb") as f:
        pl4 = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # Read DELTAT
        miscData["deltat"] = struct.unpack("<f", pl4[40:44])[0]
        DT = miscData["deltat"]

        # Read number of vars
        miscData["nvar"] = struct.unpack("<L", pl4[48:52])[0] / 2
        nv = int(miscData["nvar"])

        # Read PL4 disk size
        miscData["pl4size"] = struct.unpack("<L", pl4[56:60])[0] - 1

        # Compute the number of simulation miscData['steps'] from the PL4's file size
        miscData["steps"] = (miscData["pl4size"] - 5 * 16 - miscData["nvar"] * 16) / (
            (miscData["nvar"] + 1) * 4
        )
        step = int(miscData["steps"])

        miscData["tmax"] = (miscData["steps"] - 1) * miscData["deltat"]

        # generate pandas dataframe to store PL4's header
        dfHEAD = pd.DataFrame(columns=["TYPE", "FROM", "TO"])

        for i in range(0, nv):
            pos = 5 * 16 + i * 16
            h = struct.unpack("3x1c6s6s", pl4[pos : pos + 16])
            dfHEAD = dfHEAD.append(
                {"TYPE": int(h[0]), "FROM": h[1], "TO": h[2]}, ignore_index=True
            )
            dfHEAD["TYPE"] = dfHEAD["TYPE"].apply(lambda x: "V-node" if x == 4 else x)
            dfHEAD["TYPE"] = dfHEAD["TYPE"].apply(lambda x: "E-bran" if x == 7 else x)
            dfHEAD["TYPE"] = dfHEAD["TYPE"].apply(lambda x: "V-bran" if x == 8 else x)
            dfHEAD["TYPE"] = dfHEAD["TYPE"].apply(lambda x: "I-bran" if x == 9 else x)

        data = np.memmap(
            f,
            dtype=np.float32,
            mode="r",
            shape=(step, nv + 1),
            offset=5 * 16 + nv * 16,
        )
        currentDirectory = os.getcwd()
        file_path = currentDirectory + "\\SCENARIOS_ATP\\"
        initial = time.time()
        archivopl4 = pl4file

        # ------------ CONVERT DATA TO CSV--------------#
        header_1 = dfHEAD.iloc[:, 0].to_list()
        header_2 = dfHEAD.iloc[:, 1].to_list()
        header_3 = dfHEAD.iloc[:, 2].to_list()

        header_1.insert(0, "time".ljust(6))
        header_2.insert(0, "".ljust(6))
        header_3.insert(0, "".ljust(6))

        header = pd.MultiIndex.from_arrays([header_1, header_2, header_3])
        data = pd.DataFrame(data, columns=header)

        csv_path = currentDirectory + "\\ARCHIVOS CSV"
        path_array = csv_path.split("\\")
        s = ""

        for x in path_array:
            s = s + x
            try:
                os.stat(s)
            except Exception as e:
                os.mkdir(s)

            s = s + "\\"
        csv_name = csv_path + "\\" + archivopl4.split(".")[0] + ".csv"
        data.to_csv(csv_name, sep=";", index=False)
        final = time.time()


def atp_run(filename: str, ext: tuple, current_directory: str, solver: str):
    """Executes passed .atp file.

    Parameters
    ----------
    filename : str
        Name of .atp extension file.
    ext : tuple of str
        Extension of temporal files to remove after the simulation is done.
    current_directory : str
        Path where script is being executed (results folder must be at the same level as PFGUI.py)
    solver : str
        Path to solver (.bat file) containing code to execute atp-emtp
    """

    t1 = time.perf_counter()

    pl4_filename = filename.replace(".atp", ".pl4")
    print(f"Iniciando {filename}")
    atp_file_path = current_directory + "\\SCENARIOS_ATP"
    atp_file_name = atp_file_path + "\\" + filename

    apt_process = subprocess.Popen(
        ["C:\\ATP\\atpdraw\\ATP\\solver.bat", atp_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )

    apt_process.communicate()
    readPL4(pl4_filename)
    files_to_delete = []
    try:
        for file in ext:
            files_to_delete.extend(glob(file))
        for file in files_to_delete:
            os.remove(file)
    except:
        pass

    t2 = time.perf_counter()
    print(f"Terminó {filename} en {round(t2-t1, 3)}(s)")


def fault_list_creator(checked_faults: list, bus_impedance_list: list):
    """Writes events in FileListATPFault.txt

    Parameters
    ----------
    checked_faults : list
        List of indexes of checked faults
    bus_impedance_list : list
        List of combination of buses at fault and impedance values
    f : _io.textiowrapper
        _description_
    """
    f = open("Lista de fallas\\FileListATPFault.txt", mode="w+")
    for fault_idx in checked_faults:
        for bus, z in bus_impedance_list:
            f.write(f"Fault{fault_idx:02}_B{bus}_RF{z}.atp\n")
            print(f"Fault{fault_idx:02}_B{bus}_RF{z}.atp\n")
            f.close


# -------------------Ventana Principal----------#
class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi("InterfazQt\\SEM.ui", self)
        self.setWindowTitle("Simulador de Eventos en Microrredes")
        self.setWindowIcon(QIcon("Images\\Uninorte.png"))

        # ---------- Link to SEM User manual----------#
        path = "User Manual\\Manual SEM.pdf"
        url = bytearray(QUrl.fromLocalFile(path).toEncoded()).decode()
        color = QColor("white")
        text = "<a href={} style='color:{}'><font face=MS Shell Dlg 2 size= 12> Manual de Usuario</a>".format(
            url, color.name()
        )
        self.manuallb.setText(text)
        self.manuallb.setOpenExternalLinks(True)
        self.show()

        # ------------Elements of the fault Windows--------------#
        global fault_checkbox
        fault_checkbox = [
            self.Check01,
            self.Check02,
            self.Check03,
            self.Check04,
            self.Check05,
            self.Check06,
            self.Check07,
            self.Check08,
            self.Check09,
            self.Check10,
            self.Check11,
        ]

        # ------------- Adding Images -------------------#
        self.label.setPixmap(QPixmap("Images\\logoSEM"))
        self.IconLabel.setPixmap(QPixmap("Images\\iconSEM"))

        # ------------ Adding images to buttons--------- #
        icon = QIcon("Images\\Faultsym.png")
        self.FaultButton.setIcon(icon)
        self.FaultButton.setIconSize(QSize(30, 30))

        icon1 = QIcon("Images\\Gensym.png")
        self.GenButton.setIcon(icon1)
        self.GenButton.setIconSize(QSize(30, 30))

        icon2 = QIcon("Images\\Home.png")
        self.HomeButton.setIcon(icon2)
        self.HomeButton.setIconSize(QSize(30, 30))

        icon4 = QIcon("Images\\Sesym.png")
        self.SETBTN.setIcon(icon4)
        self.SETBTN.setIconSize(QSize(30, 30))

        # --------------- Connecting buttons to slots-----------#
        self.FaultButton.clicked.connect(self.ButtonPressed)
        self.HomeButton.clicked.connect(self.ButtonPressed)
        self.GenButton.clicked.connect(self.ButtonPressed)
        self.SETBTN.clicked.connect(self.ButtonPressed)
        self.ATPbutton.clicked.connect(self.SearchATP)
        self.Svfaultbtn.clicked.connect(self.CheckBoxChangedAction)
        self.Svfaultbtn.clicked.connect(self.save_fault)
        self.Svfaultbtn.clicked.connect(self.read_new_files)
        self.ExecBtn.clicked.connect(self.ATP_files_execution)
        # self.execgenbtn.clicked.connect(self.generacion)
        self.createdemand.clicked.connect(self.esc_demanda)

        # ---------- Hide all don't needed windows-------------------#
        self.FaultPage.hide()
        self.IconLabel.hide()
        self.GenPage.hide()
        self.SetPage.hide()

    def ButtonPressed(self):
        button = self.sender().objectName()
        # buttons = self.sender()

        if button == "FaultButton":
            self.HomePage.hide()
            self.FaultPage.show()
            self.IconLabel.show()
            self.GenPage.hide()
            self.SetPage.hide()

            self.Check01.setChecked(True)
            # buses = self.Bustext.setPlainText(str(632))
            # Rinic = self.Rinicial.setPlainText(str(0.01))
            # Delta = self.Rpaso.setPlainText(str(.01))
            # Rfin = self.Rfinal.setPlainText(str(0.1))
            # Tfallainicial = self.Tfallai.setPlainText(str(0.05))
            # Tfallafinal = self.Tfallaf.setPlainText(str(.1))
            buses = self.Bustext.setPlainText(str(632))
            Rinic = self.Rinicial.setPlainText(str(0.00001))
            Delta = self.Rpaso.setPlainText(str(0.00001))
            Rfin = self.Rfinal.setPlainText(str(0.00002))
            Tfallainicial = self.Tfallai.setPlainText(str(0.05))
            Tfallafinal = self.Tfallaf.setPlainText(str(0.1))

        if button == "HomeButton":
            self.HomePage.show()
            self.FaultPage.hide()
            self.IconLabel.hide()
            self.GenPage.hide()
            self.SetPage.hide()

        if button == "GenButton":
            self.HomePage.hide()
            self.FaultPage.hide()
            self.GenPage.show()
            self.IconLabel.show()
            self.SetPage.hide()

        if button == "SETBTN":
            self.HomePage.hide()
            self.FaultPage.hide()
            self.IconLabel.show()
            self.GenPage.hide()
            self.SetPage.show()

    # --------------- VENTANA DE FALLAS------------#
    def CheckBoxChangedAction(self):
        buses = self.Bustext.toPlainText()
        buses = buses.strip().split(" ")
        Rinic = self.Rinicial.toPlainText()
        Delta = self.Rpaso.toPlainText()
        Rfin = self.Rfinal.toPlainText()
        Tfallainicial = self.Tfallai.toPlainText()
        TFallafinal = self.Tfallaf.toPlainText()

        if (
            len(buses) < 1
            or len(Rinic) < 1
            or len(Delta) < 1
            or len(Rfin) < 1
            or len(Tfallainicial) < 1
            or len(TFallafinal) < 1
        ):
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
            msgBox.setText("Fallo al ingresar los datos")
            msgBox.setDetailedText(
                "Detalles:\n Se deben ingresar todos los parámetros."
            )
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setWindowIcon(QIcon("Images\\Uninorte.png"))
            msgBox.setWindowTitle("SEM")
            msgBox.exec_()
        else:
            Ri = float(Rinic)
            D = float(Delta)
            Rf = float(Rfin)

        impedances = np.around(np.arange(Ri, Rf + D, D), 5)
        # Create list
        bus_impedance_list = [(bus, z) for bus in buses for z in impedances]
        checked_faults = [
            idx + 1
            for idx, checkbox in enumerate(fault_checkbox)
            if checkbox.isChecked()
        ]
        # Create FileListATPFault.txt
        fault_list_creator(checked_faults, bus_impedance_list)

    def save_fault(self, fname):
        currentDirectory = os.getcwd()

        validacion_checkbox = True
        validación_buses = True
        contador = 0
        for x in fault_checkbox:
            check = x.isChecked()
            if check == False:
                contador += 1
        if contador == 11:
            validacion_checkbox = False

        if not validacion_checkbox:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
            msgBox.setText("Fallo al ingresar los datos")
            msgBox.setDetailedText(
                "Detalles:\n Al menos un tipo de falla debe ser seleccionado."
            )
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setWindowIcon(QIcon("Images\\Uninorte.png"))
            msgBox.setWindowTitle("SEM")
            msgBox.exec_()
        with open("Lista de fallas\\FileListATPFault.txt", mode="r") as f:
            contador = 0
            datos = []
            shutil.rmtree(currentDirectory + "\\SCENARIOS_ATP")
            os.mkdir("SCENARIOS_ATP")
            for linea in f:
                contador += 1
                nombre = linea.rstrip("\n")
                fuente = self.fname
                name = os.path.split(fuente)[1]
                destino = currentDirectory + "\\SCENARIOS_ATP"
                shutil.copy(fuente, destino)
                # Cambiando nombre de los archivos
                oldname = os.path.join(destino, name)
                newname = os.path.join(destino, nombre)
                os.rename(oldname, newname)

    def read_new_files(self):
        TFf = self.Tfallaf.toPlainText()
        TFi = self.Tfallai.toPlainText()

        with open("Lista de fallas\\FileListATPFault.txt", "r") as f:
            for linea in f:
                nombre = linea.rstrip("\n")
                bus = nombre[9] + nombre[10] + nombre[11]
                # if nombre[16] == ".":
                #     Rfalla = nombre[15]
                # else:
                #     Rfalla = nombre[15]+nombre[16]
                # Tipo_Falla = nombre[5]+nombre[6]

                patronRfalla = "RF(.*?).atp"
                patronTipoFalla = "Fault(.*?)_"
                Rfalla = re.search(patronRfalla, nombre).group(1)
                Tipo_Falla = re.search(patronTipoFalla, nombre).group(1)

                with open("SCENARIOS_ATP\\" + nombre) as fatp:
                    lines = fatp.readlines()
                lines_copy = lines.copy()
                val = True
                for line_idx, line in enumerate(lines):
                    if "C " + "RFA" == line.strip("\n"):
                        d_lineA = line_idx + 1
                    if "C " + "RFB" == line.strip("\n"):
                        d_lineB = line_idx + 1
                    if "C " + "RFC" == line.strip("\n"):
                        d_lineC = line_idx + 1
                    if "C " + "FaultSwA" == line.strip("\n"):
                        d_lineSA = line_idx + 1
                    if "C " + "FaultSwB" == line.strip("\n"):
                        d_lineSB = line_idx + 1
                    if "C " + "FaultSwC" == line.strip("\n"):
                        d_lineSC = line_idx + 1
                    if "C " + "FaultSwGround" == line.strip("\n"):
                        d_linesg = line_idx + 1
                    if "C " + "SMR2" == line.strip("\n"):
                        d_lineswmr = line_idx + 1
                    if "C " + "SMR1" == line.strip("\n"):
                        d_lineswmr = line_idx + 1
                    if "C mainSource" in line.strip("\n"):
                        d_mainSource = line_idx + 1
                    if "C microGridSource" in line.strip("\n"):
                        d_microGridSource = line_idx + 1

                self.setgridop(d_lineswmr, lines_copy)
                data_dict = {}
                data_dict["Nodo"] = {}
                data_dict["Nodo"] = bus
                data_dict["Rfalla"] = {}
                data_dict["Rfalla"] = Rfalla
                Bus = data_dict["Nodo"]
                RF = data_dict["Rfalla"]
                RF = RF.center(6)
                BusA = "N" + Bus + "A"
                BusA = BusA.center(6)
                BusB = "N" + Bus + "B"
                BusB = BusB.center(6)
                BusC = "N" + Bus + "C"
                BusC = BusC.center(6)
                element_lineSA = lines_copy[d_lineSA]
                element_lineSB = lines_copy[d_lineSB]
                element_lineSC = lines_copy[d_lineSC]
                element_lineA = lines_copy[d_lineA]
                element_lineB = lines_copy[d_lineB]
                element_lineC = lines_copy[d_lineC]
                lines_copy[d_lineA] = element_lineA[:26] + RF + element_lineA[32:]
                lines_copy[d_lineB] = element_lineB[:26] + RF + element_lineB[32:]
                lines_copy[d_lineC] = element_lineC[:26] + RF + element_lineC[32:]

                random_phase = True
                if random_phase:
                    phase_int = random.randint(0, 180)
                    phase_dec = round(random.random(), 5)
                    source_phase = phase_int + phase_dec
                    phi_a = str(round(source_phase, 5))
                    phi_b = str(round(source_phase - 120, 5))
                    phi_c = str(round(source_phase - 240, 5))
                    try:
                        print("chkpoint phase")
                        phase_line_a = lines_copy[d_mainSource]
                        phase_line_b = lines_copy[d_mainSource + 1]
                        phase_line_c = lines_copy[d_mainSource + 2]
                        lines_copy[
                            d_mainSource
                        ] = f"{phase_line_a[:30]}{phi_a:>10}{phase_line_a[40:]}"
                        lines_copy[
                            d_mainSource + 1
                        ] = f"{phase_line_b[:30]}{phi_b:>10}{phase_line_b[40:]}"
                        lines_copy[
                            d_mainSource + 2
                        ] = f"{phase_line_c[:30]}{phi_c:>10}{phase_line_c[40:]}"
                    except NameError:
                        print("There is no source with mainSource in comment")
                    try:
                        phase_line = lines_copy[d_microGridSource]
                        lines_copy[
                            d_microGridSource
                        ] = f"{phase_line[:30]}{str(round(source_phase+0.17, 5)):>10}{phase_line[40:]}"
                    except NameError:
                        print(
                            "There is no microgrid source with microGridSource in comment"
                        )
                if Tipo_Falla == "01":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = TFf
                    data_dict["FaultSwA"]["close_time"] = TFi
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = "1000"
                    data_dict["FaultSwB"]["open_time"] = "-1"
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = "1000"
                    data_dict["FaultSwC"]["open_time"] = "-1"
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwA"]["open_time"]
                    Clswg = data_dict["FaultSwA"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeA + optimeA + element_linesg[34:]
                    )

                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "02":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = "-1"
                    data_dict["FaultSwA"]["close_time"] = "1000"
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = TFi
                    data_dict["FaultSwB"]["open_time"] = TFf
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = "1000"
                    data_dict["FaultSwC"]["open_time"] = "-1"
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwB"]["open_time"]
                    Clswg = data_dict["FaultSwB"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeB + optimeB + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)
                if Tipo_Falla == "03":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = "-1"
                    data_dict["FaultSwA"]["close_time"] = "1000"
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = "1000"
                    data_dict["FaultSwB"]["open_time"] = "-1"
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = TFi
                    data_dict["FaultSwC"]["open_time"] = TFf
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeC + optimeC + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "04":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = TFf
                    data_dict["FaultSwA"]["close_time"] = TFi
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = TFi
                    data_dict["FaultSwB"]["open_time"] = TFf
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = "1000"
                    data_dict["FaultSwC"]["open_time"] = "-1"
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeC + optimeC + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "05":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = "-1"
                    data_dict["FaultSwA"]["close_time"] = "1000"
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = TFi
                    data_dict["FaultSwB"]["open_time"] = TFf
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = TFi
                    data_dict["FaultSwC"]["open_time"] = TFf
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeA + optimeA + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "06":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = TFf
                    data_dict["FaultSwA"]["close_time"] = TFi
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = "1000"
                    data_dict["FaultSwB"]["open_time"] = "-1"
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = TFi
                    data_dict["FaultSwC"]["open_time"] = TFf
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeB + optimeB + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "07":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = TFf
                    data_dict["FaultSwA"]["close_time"] = TFi
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = TFi
                    data_dict["FaultSwB"]["open_time"] = TFf
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = "1000"
                    data_dict["FaultSwC"]["open_time"] = "-1"
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeA + optimeA + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "08":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = "-1"
                    data_dict["FaultSwA"]["close_time"] = "1000"
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = TFi
                    data_dict["FaultSwB"]["open_time"] = TFf
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = TFi
                    data_dict["FaultSwC"]["open_time"] = TFf
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeC + optimeC + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "09":
                    data_dict = {}
                    data_dict["FaultSwA"] = {}
                    data_dict["FaultSwA"]["open_time"] = TFf
                    data_dict["FaultSwA"]["close_time"] = TFi
                    data_dict["FaultSwB"] = {}
                    data_dict["FaultSwB"]["close_time"] = "1000"
                    data_dict["FaultSwB"]["open_time"] = "-1"
                    data_dict["FaultSwC"] = {}
                    data_dict["FaultSwC"]["close_time"] = TFi
                    data_dict["FaultSwC"]["open_time"] = TFf
                    OpenTA = data_dict["FaultSwA"]["open_time"]
                    CloseTA = data_dict["FaultSwA"]["close_time"]
                    OpenTB = data_dict["FaultSwB"]["open_time"]
                    CloseTB = data_dict["FaultSwB"]["close_time"]
                    OpenTC = data_dict["FaultSwC"]["open_time"]
                    CloseTC = data_dict["FaultSwC"]["close_time"]
                    Opswg = data_dict["FaultSwC"]["open_time"]
                    Clswg = data_dict["FaultSwC"]["close_time"]
                    optimeA = OpenTA.center(10)
                    cltimeA = CloseTA.center(10)
                    optimeB = OpenTB.center(10)
                    optimeC = OpenTC.center(10)
                    cltimeB = CloseTB.center(10)
                    cltimeC = CloseTC.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltimeA
                        + optimeA
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltimeB
                        + optimeB
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltimeC
                        + optimeC
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeC + optimeC + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "10":
                    data_dict = {}
                    data_dict["FaultSw"] = {}
                    data_dict["FaultSw"]["open_time"] = TFf
                    data_dict["FaultSw"]["close_time"] = TFi
                    data_dict["FaultSwG"] = {}
                    data_dict["FaultSwG"]["close_time"] = "1000"
                    data_dict["FaultSwG"]["open_time"] = "-1"
                    Opent = data_dict["FaultSw"]["open_time"]
                    Closet = data_dict["FaultSw"]["close_time"]
                    Opswg = data_dict["FaultSwG"]["open_time"]
                    Clswg = data_dict["FaultSwG"]["close_time"]
                    optime = Opent.center(10)
                    cltime = Closet.center(10)
                    optimeg = Opswg.center(10)
                    cltimeg = Clswg.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltime
                        + optime
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltime
                        + optime
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltime
                        + optime
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltimeg + optimeg + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

                if Tipo_Falla == "11":
                    data_dict = {}
                    data_dict["FaultSw"] = {}
                    data_dict["FaultSw"]["open_time"] = TFf
                    data_dict["FaultSw"]["close_time"] = TFi
                    Opent = data_dict["FaultSw"]["open_time"]
                    Closet = data_dict["FaultSw"]["close_time"]
                    optime = Opent.center(10)
                    cltime = Closet.center(10)
                    element_linesg = lines_copy[d_linesg]
                    element_lineA = lines_copy[d_lineA]
                    element_lineB = lines_copy[d_lineB]
                    element_lineC = lines_copy[d_lineC]
                    lines_copy[d_lineSA] = (
                        element_lineSA[:2]
                        + BusA
                        + element_lineSA[8:14]
                        + cltime
                        + optime
                        + element_lineSA[34:]
                    )
                    lines_copy[d_lineSB] = (
                        element_lineSB[:2]
                        + BusB
                        + element_lineSB[8:14]
                        + cltime
                        + optime
                        + element_lineSB[34:]
                    )
                    lines_copy[d_lineSC] = (
                        element_lineSC[:2]
                        + BusC
                        + element_lineSC[8:14]
                        + cltime
                        + optime
                        + element_lineSC[34:]
                    )
                    lines_copy[d_linesg] = (
                        element_linesg[:14] + cltime + optime + element_linesg[34:]
                    )
                    with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                        file.writelines(lines_copy)

    def ATP_files_execution(self):
        cores = os.cpu_count()
        current_directory = os.getcwd()
        solver = "C:\\ATP\\atpdraw\\ATP\\solver.bat"
        ext = ("SCENARIOS_ATP\\*.dbg", "SCENARIOS_ATP\\*.lis")
        filenames_gen = (
            row.strip("\n")
            for row in open("Lista de fallas\\FileListATPFault.txt", "r")
        )
        t1_total = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=cores - 3) as executor:
            executor.map(
                atp_run,
                filenames_gen,
                repeat(ext),
                repeat(current_directory),
                repeat(solver),
            )

        t2_total = time.perf_counter()
        print(f"Tiempo de simulación total {round(t2_total-t1_total, 3)}s\n\n")

    # ---------Ventana de cargas---------------------#
    def executedyg(self, atp_file):
        currentDirectory = os.getcwd()
        solver = "C:\\ATP\\atpdraw\\ATP\\solver.bat"
        intime = time.time()
        self.pl4_file = atp_file.replace(".atp", ".pl4")
        print("Scenario " + atp_file + " Started")
        atp_file_path = currentDirectory + "\\SCENARIOS_NOFAULT_ATP"
        atp_file_name = atp_file_path + "\\" + atp_file

        code = [solver, atp_file_name]

        p = Popen(code, stdout=PIPE, stdin=PIPE, shell=True)
        output, errors = p.communicate()

        p.wait()

        print("Scenario " + atp_file + " Completed")

        finalt = time.time()
        print("Simulation Time: ", finalt - intime, "\n\n")

    def esc_demanda(self):
        currentDirectory = os.getcwd()
        var = 1
        vaux = str(var)
        # -------------loads-------------#
        loads = self.elementload.toPlainText()
        Pactivaload = self.paload.toPlainText()
        Preactivaload = self.prload.toPlainText()
        cargas = loads.split("\n")
        PAL = Pactivaload.split("\n")
        PRL = Preactivaload.split("\n")
        PAL = np.array(PAL)
        PRL = np.array(PRL)
        Vfase = self.voltajeload.toPlainText()
        Vfase = float(Vfase)
        # ------------gens----------------------#
        generador = self.elementgen.toPlainText()
        vfasea = self.tengena.toPlainText()
        vfaseb = self.tengenb.toPlainText()
        vfaseb = self.tengenc.toPlainText()
        pactiva = self.pagen.toPlainText()
        preactiva = self.prgen.toPlainText()
        gens = generador.split("\n")
        PotActiva = pactiva.split("\n")
        PotReactiva = preactiva.split("\n")
        P = np.array(PotActiva)
        Q = np.array(PotReactiva)
        Sgen = []
        Rload = []
        Lload = []
        # -------------- create files--------------#
        shutil.rmtree(currentDirectory + "\\SCENARIOS_NOFAULT_ATP")
        os.mkdir("SCENARIOS_NOFAULT_ATP")
        fuente = self.fname
        name = os.path.split(fuente)[1]
        destino = currentDirectory + "\\SCENARIOS_NOFAULT_ATP"
        shutil.copy(fuente, destino)
        nombre = "NF_CASE" + vaux + "_" + name
        # Cambiando nombre del archivo
        oldname = os.path.join(destino, name)
        newname = os.path.join(destino, nombre)
        os.rename(oldname, newname)

        for i in range(0, len(cargas), 1):
            if cargas[i][7] == "D":
                cond = "tri"
                V = Vfase
                S = complex(float(PAL[i]) * 1000, float(PRL[i]) * 1000)
                Z = np.conj(V * V / S)
                R = round(Z.real, 3)
                R = str(R)
                R = R[:6]
                R = R.center(6)
                X = Z.imag
                pi = math.pi
                L = X / (2 * pi * 60)
                Lmh = round(L * 1000, 3)
                Lmh = str(Lmh)
                Lmh = Lmh[:6]
                Lmh = Lmh.center(6)
            if cargas[i][7] == "Y":
                cond = "tri"
                V = Vfase / (math.sqrt(3))
                S = complex(float(PAL[i]) * 1000, float(PRL[i]) * 1000)
                print(S)
                z = (V * V) / S
                Z = np.conj(z)
                R = round(Z.real, 3)
                R = str(R)
                R = R[:6]
                R = R.center(6)
                X = Z.imag
                pi = math.pi
                L = X / (2 * pi * 60)
                Lmh = round(L * 1000, 3)
                Lmh = str(Lmh)
                Lmh = Lmh[:6]
                Lmh = Lmh.center(6)
            if len(cargas[i]) == 10:
                cond = "mono"
                V = Vfase
                S = complex(float(PAL[i]) * 1000, float(PRL[i]) * 1000)
                Z = np.conj(V * V / S)
                R = round(Z.real, 3)
                R = str(R)
                R = R[:6]
                R = R.center(6)
                X = Z.imag
                pi = math.pi
                L = X / (2 * pi * 60)
                Lmh = round(L * 1000, 3)
                Lmh = str(Lmh)
                Lmh = Lmh[:6]
                Lmh = Lmh.center(6)
            Rload.append(R)
            Lload.append(Lmh)
            with open("SCENARIOS_NOFAULT_ATP\\" + nombre) as fatp:
                lines = fatp.readlines()
            lines_copy = lines.copy()

            for line_idx, line in enumerate(lines):
                if "C " + "SMR2" == line.strip("\n"):
                    d_lineswmr2 = line_idx + 1
                if "C " + "SMR1" == line.strip("\n"):
                    d_lineswmr = line_idx + 1
                if "C " + cargas[i] == line.strip("\n"):
                    d_lineload = line_idx + 1
            self.setgridop(d_lineswmr, lines_copy)
            if cond == "tri":
                for val in range(3):
                    element_lineload = lines_copy[d_lineload + val]
                    lines_copy[d_lineload + val] = (
                        element_lineload[:26]
                        + Rload[i]
                        + Lload[i]
                        + element_lineload[38:]
                    )
            if cond == "mono":
                element_lineload = lines_copy[d_lineload]
                lines_copy[d_lineload] = (
                    element_lineload[:26] + Rload[i] + Lload[i] + element_lineload[38:]
                )
            with open("SCENARIOS_NOFAULT_ATP\\" + nombre, "w") as file:
                file.writelines(lines_copy)
        for i in range(0, len(gens)):
            if gens[i][0] == "P":
                condg = "PV"
                Sc = complex(float(P[i]), float(Q[i]))
                SPV = cmath.polar(Sc)[0]
                SPV = SPV / 1000
                SPV = round(SPV, 3)
                Sg = str(SPV)
                Sg = Sg.center(6)
                Sgen.append(Sg)
            with open("SCENARIOS_NOFAULT_ATP\\" + nombre) as fatp:
                lines = fatp.readlines()
            lines_copy = lines.copy()
            for line_idx, line in enumerate(lines):
                if "C " + gens[i] == line.strip("\n"):
                    d_linegen = line_idx + 1
            if condg == "PV":
                va = 11
                element_linepv = lines_copy[d_linegen + va]
                lines_copy[d_linegen + va] = (
                    element_linepv[:9] + Sgen[i] + element_linepv[14:]
                )
            with open("SCENARIOS_NOFAULT_ATP\\" + nombre, "w") as file:
                file.writelines(lines_copy)

        self.executedyg(nombre)

        var = var + 1

    # ------------ Ventana de configuración-------------------#
    def SearchATP(self):
        global atpfile

        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle("Open ATP project")
        dialog.setNameFilter("(*.atp)")
        direc = QtCore.QDir("C:/SimulacionesATP")
        dialog.setDirectory(direc)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        filename = None
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            filename = dialog.selectedFiles()
        if filename:
            self.fname = str(filename[0])
            self.lineEdit.setText(self.fname)
            atpfile = open(self.fname)
            lines = atpfile.readlines()

    def setgridop(self, d_lineswmr, lines_copy):
        if self.ongridcheck.isChecked() == True:
            data_dict = {}
            data_dict["SMR"] = {}
            data_dict["SMR"]["close_time"] = "-1"
            data_dict["SMR"]["open_time"] = "1000"
            OpenMR = data_dict["SMR"]["open_time"]
            CloseMR = data_dict["SMR"]["close_time"]
            opmr = OpenMR.center(10)
            clmr = CloseMR.center(10)

            for val in range(3):
                element_linesMR = lines_copy[d_lineswmr + val]
                lines_copy[d_lineswmr + val] = (
                    element_linesMR[:14] + clmr + opmr + element_linesMR[34:]
                )
        if self.offgridcheck.isChecked() == True:
            data_dict = {}
            data_dict["SMR"] = {}
            data_dict["SMR"]["close_time"] = "1000"
            data_dict["SMR"]["open_time"] = "-1"
            OpenMR = data_dict["SMR"]["open_time"]
            CloseMR = data_dict["SMR"]["close_time"]
            opmr = OpenMR.center(10)
            clmr = CloseMR.center(10)

            for val in range(3):
                element_linesMR = lines_copy[d_lineswmr + val]
                lines_copy[d_lineswmr + val] = (
                    element_linesMR[:14] + clmr + opmr + element_linesMR[34:]
                )

    # ----------------Datos de salida-------------------------------#


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MyWindow()
    app.exec_()


if __name__ == "__main__":
    main()


# Project Designed by: Mildre Fernández and Daniela Latorre. 2021 #
