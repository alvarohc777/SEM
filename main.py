# For readpl4 Function
import struct
import mmap


# NumPy Stack
import pandas as pd
import numpy as np

# Measure Performance
import time

# To access os
import subprocess
import glob
import os
import sys

# To find patterns
import re

# Other
import random


def fault_list_creator(checked_faults: list, bus_impedance: list):
    """Writes events in FileListATPFault.txt

    Parameters
    ----------
    checked_faults : list
        List of indexes of checked faults
    bus_impedance : list
        List of combination of buses at fault and impedance values
    f : _io.textiowrapper
        _description_
    """
    f = open("Lista de fallas\\FileListATPFault.txt", mode="w+")
    for fault_idx in checked_faults:
        for bus, z in bus_impedance:
            f.write(f"Fault{fault_idx:02}_B{bus}_RF{z}.atp\n")
            f.close


def atp_fault_file(TFf: str, TFi: str, grid_checked: bool):
    """This function updates each ATP card's (all cloned from model scenario)
    internal values according to their name. Each name bus at fault, fault type
    and fault resistance.

    Format: FaultXX_BXXX_RFXX.atp.

    Where
        FaultXX -> Fault type.
        BXXX    -> Bus at fault.
        RFXX    -> Fault resistance.

    Parameters
    ----------
    TFf : str
        Fault final time
    TFi : str
        Fault initial time
    grid_checked : bool
        Microgrid Switch State (True: microgrid on / False: microgrid off)
    """
    with open("Lista de fallas\\FileListATPFault.txt", "r") as f:
        for atp_file_name in f:
            # Get parameters from file
            nombre = atp_file_name.rstrip("\n")
            pattern_bus_name = "B(\d{3})"
            pattern_Rfalla = "RF(.*?).atp"
            pattern_TipoFalla = "Fault(.*?)_"
            Rfalla = re.search(pattern_Rfalla, nombre).group(1)
            Tipo_Falla = re.search(pattern_TipoFalla, nombre).group(1)
            bus = re.search(pattern_bus_name, nombre).group(1)

            # Open file and read lines
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

            lines_copy = setgridop(d_lineswmr, lines_copy, grid_checked)
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

            data_dict = {}
            element_linesg = lines_copy[d_linesg]
            element_lineA = lines_copy[d_lineA]
            element_lineB = lines_copy[d_lineB]
            element_lineC = lines_copy[d_lineC]

            # Empty Switches parameters dictionary
            data_dict["FaultSwA"] = {}
            data_dict["FaultSwB"] = {}
            data_dict["FaultSwC"] = {}
            data_dict["FaultSwG"] = {}

            # Default Switches Settings
            data_dict["FaultSwA"]["close_time"] = "1000"
            data_dict["FaultSwA"]["open_time"] = "-1"
            data_dict["FaultSwB"]["close_time"] = "1000"
            data_dict["FaultSwB"]["open_time"] = "-1"
            data_dict["FaultSwC"]["close_time"] = "1000"
            data_dict["FaultSwC"]["open_time"] = "-1"
            data_dict["FaultSwG"]["close_time"] = "1000"
            data_dict["FaultSwG"]["open_time"] = "-1"

            if Tipo_Falla == "01":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "02":
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "03":
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "04":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi

            if Tipo_Falla == "05":
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi

            if Tipo_Falla == "06":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi

            if Tipo_Falla == "07":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "08":
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "09":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            if Tipo_Falla == "10":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi

            if Tipo_Falla == "11":
                data_dict["FaultSwA"]["open_time"] = TFf
                data_dict["FaultSwA"]["close_time"] = TFi
                data_dict["FaultSwB"]["open_time"] = TFf
                data_dict["FaultSwB"]["close_time"] = TFi
                data_dict["FaultSwC"]["open_time"] = TFf
                data_dict["FaultSwC"]["close_time"] = TFi
                data_dict["FaultSwG"]["open_time"] = TFf
                data_dict["FaultSwG"]["close_time"] = TFi

            open_time_A = data_dict["FaultSwA"]["open_time"].center(10)
            close_time_A = data_dict["FaultSwA"]["close_time"].center(10)
            open_time_B = data_dict["FaultSwB"]["open_time"].center(10)
            close_time_B = data_dict["FaultSwB"]["close_time"].center(10)
            open_time_C = data_dict["FaultSwC"]["open_time"].center(10)
            close_time_C = data_dict["FaultSwC"]["close_time"].center(10)
            open_time_gnd = data_dict["FaultSwG"]["open_time"].center(10)
            close_time_gnd = data_dict["FaultSwG"]["close_time"].center(10)

            lines_copy[d_lineSA] = (
                element_lineSA[:2]
                + BusA
                + element_lineSA[8:14]
                + close_time_A
                + open_time_A
                + element_lineSA[34:]
            )
            lines_copy[d_lineSB] = (
                element_lineSB[:2]
                + BusB
                + element_lineSB[8:14]
                + close_time_B
                + open_time_B
                + element_lineSB[34:]
            )
            lines_copy[d_lineSC] = (
                element_lineSC[:2]
                + BusC
                + element_lineSC[8:14]
                + close_time_C
                + open_time_C
                + element_lineSC[34:]
            )
            lines_copy[d_linesg] = (
                element_linesg[:14]
                + close_time_gnd
                + open_time_gnd
                + element_linesg[34:]
            )
            with open("SCENARIOS_ATP\\" + nombre, "w") as file:
                file.writelines(lines_copy)


def setgridop(d_lineswmr: int, lines_copy: list, grid_checked: bool):
    """Sets microgrid switch state (closed or open)

    Parameters
    ----------
    d_lineswmr : int
        Index of line containing information of microgrid switch
    lines_copy : list
        List containing all lines of atp file.
    grid_checked : bool
        Whether microgrid switch is closed or open

    Returns
    -------
    _type_
        _description_
    """
    if grid_checked == True:
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
    if grid_checked == False:
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
    return lines_copy


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


def fault_inputs():
    params = {}

    # Validate or transform data
    buses = [
        802,
        814,
        832,
    ]
    Ri = 0.00001
    Rf = 100
    R_step = 10
    faults_checkbox = {
        "fault01": True,
        "fault02": False,
        "fault03": True,
        "fault04": True,
        "fault05": True,
        "fault06": True,
        "fault07": False,
        "fault08": True,
        "fault09": False,
        "fault10": True,
        "fault11": True,
    }

    # Save params in dictionary
    params["buses"] = list(set(buses))
    params["Ri"] = Ri
    params["Rf"] = Rf
    params["R_step"] = R_step
    params["event"] = "fault"
    params["faults_checkbox"] = faults_checkbox
    return params


# dict.values()
# dict.keys()
# dict.items()
def main():
    params = fault_inputs()

    if params["event"] == "fault":
        buses = params["buses"]
        Ri = params["Ri"]
        Rf = params["Rf"]
        R_step = params["R_step"]
        faults_checkbox = params["faults_checkbox"]

        # Create Bus-Impedance Combinations List
        impedances = np.around(np.arange(Ri, Rf + R_step, R_step), 5)
        bus_impedance = [(bus, z) for bus in buses for z in impedances]
        bus_impedance = ((bus, z) for bus in buses for z in impedances)
        # Create Desired faults list
        checked_faults = [
            idx + 1 for idx, state in enumerate(faults_checkbox.values()) if state
        ]
        fault_list_creator(checked_faults, bus_impedance)
    elif params["event"] == "load":
        print("función no disponible aún")


if __name__ == "__main__":
    main()
    print(__name__)
