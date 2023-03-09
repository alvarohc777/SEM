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
import shutil

# To find patterns
import re

# Other
from itertools import repeat
import random

# Multiprocessing
import concurrent.futures

# Global Constants

EVENTS_DIR = "1. Events list"
SCENARIOS_DIR = "2. Scenarios"
CSV_DIR = "3. Archivos CSV"
BASE_FILES_DIR = "Sistemas de prueba"
FAULT_FILES_LIST = "fault_files_list.txt"
LOAD_FILES_LIST = "load_files_list.txt"


SOLVER = r"C:\ATP\atpdraw\ATP\solver.bat"
EXT = (f"{SCENARIOS_DIR}\*.dbg", f"{SCENARIOS_DIR}\*.lis")
CWD = os.getcwd()


def create_directories():
    # Create new events lists directory -> fault_list_
    if os.path.exists(EVENTS_DIR):
        shutil.rmtree(EVENTS_DIR)
    os.mkdir(EVENTS_DIR)

    # Create new atp scenarios directory -> create_copies()
    if os.path.exists(SCENARIOS_DIR):
        shutil.rmtree(SCENARIOS_DIR)
    os.mkdir(SCENARIOS_DIR)

    # # Create new atp scenarios directory -> create_copies()
    if os.path.exists(CSV_DIR):
        shutil.rmtree(CSV_DIR)
    os.mkdir(CSV_DIR)


def fault_list_creator(checked_faults: list, bus_impedance: list):
    """Writes events list in {}FileListATPFault.txt

    Parameters
    ----------
    checked_faults : list
        List of indexes of checked faults
    bus_impedance : list
        List of combination of buses at fault and impedance values
    """

    f = open(f"{EVENTS_DIR}\{FAULT_FILES_LIST}", mode="w+")
    for fault_idx in checked_faults:
        for bus, z in bus_impedance:
            f.write(f"Fault{fault_idx:02}_B{bus}_RF{z}.atp\n")
            f.close


def create_copies(base_file_path: str):
    """Creates copies of base atp file in {SCENARIOS_DIR} directory
    with updated names (according to simulation parameters)

    Parameters
    ----------
    base_file_path : str
        Base atp file.
    """
    with open(f"{EVENTS_DIR}\{FAULT_FILES_LIST}", mode="r") as f:
        for line in f:
            new_name = line.strip("\n")
            target = f"{CWD}\{SCENARIOS_DIR}\{new_name}"
            shutil.copy(base_file_path, target)


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
    with open(f"{EVENTS_DIR}\{FAULT_FILES_LIST}", "r") as f:
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
            with open(f"{SCENARIOS_DIR}\{nombre}") as fatp:
                lines = fatp.readlines()
            lines_copy = lines.copy()
            val = True
            for line_idx, line in enumerate(lines):
                if "C RFA" in line:
                    d_lineA = line_idx + 1
                if "C RFB" in line:
                    d_lineB = line_idx + 1
                if "C RFC" in line:
                    d_lineC = line_idx + 1
                if "C FaultSwA" in line:
                    d_lineSA = line_idx + 1
                if "C FaultSwB" in line:
                    d_lineSB = line_idx + 1
                if "C FaultSwC" in line:
                    d_lineSC = line_idx + 1
                if "C FaultSwGround" in line:
                    d_linesg = line_idx + 1
                if "C SMR2" in line:
                    d_lineswmr = line_idx + 1
                if "C SMR1" in line:
                    d_lineswmr = line_idx + 1
                if "C mainSource" in line:
                    d_mainSource = line_idx + 1
                if "C microGridSource" in line:
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

            lines_copy[
                d_lineSA
            ] = f"{element_lineSA[:2]}{BusA}{element_lineSA[8:14]}{close_time_A}{open_time_A}{element_lineSA[34:]}"
            lines_copy[
                d_lineSB
            ] = f"{element_lineSB[:2]}{BusB}{element_lineSB[8:14]}{close_time_B}{open_time_B}{element_lineSB[34:]}"
            lines_copy[
                d_lineSC
            ] = f"{element_lineSC[:2]}{BusC}{element_lineSC[8:14]}{close_time_C}{open_time_C}{element_lineSC[34:]}"
            lines_copy[
                d_linesg
            ] = f"{element_linesg[:14]}{close_time_gnd}{open_time_gnd}{element_linesg[34:]}"
            with open(f"{SCENARIOS_DIR}\{nombre}", "w") as file:
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


def atp_files_execution():
    """Initiates parallel execution for each file"""
    cores = os.cpu_count()
    filenames_gen = (
        row.strip("\n") for row in open(f"{EVENTS_DIR}\{FAULT_FILES_LIST}", "r")
    )
    t1_total = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cores - 3) as executor:
        executor.map(atp_run, filenames_gen)
    t2_total = time.perf_counter()
    print(f"Tiempo de simulación total: {round(t2_total-t1_total, 3)}s\n\n")


def atp_run(filename: str):
    """Executes passed .atp file.

    Parameters
    ----------
    filename : str
        Name of .atp extension file.
    """

    t1 = time.perf_counter()

    pl4_filename = filename.replace(".atp", ".pl4")
    print(f"Iniciando {filename}")
    atp_file_path = f"{CWD}\{SCENARIOS_DIR}"
    atp_file_name = f"{atp_file_path}\{filename}"

    apt_process = subprocess.Popen(
        [SOLVER, atp_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )

    apt_process.communicate()
    readPL4(pl4_filename)

    files_to_delete = []
    try:
        for file in EXT:
            files_to_delete.extend(glob.glob(file))

        for file in files_to_delete:
            os.remove(file)
    except:
        pass

    t2 = time.perf_counter()
    print(f"Terminó {filename} en {round(t2-t1, 3)}(s)")


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

    with open(f"{SCENARIOS_DIR}\{pl4file}", "rb") as f:
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
        file_path = f"{CWD}\{SCENARIOS_DIR}\\"
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
        csv_path = f"{CWD}\{CSV_DIR}"
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


def fault_inputs() -> dict:
    """Function to receive all simulation parameters inputs

    Returns
    -------
    dict
        Dictionary with simulations parameters
    """
    params = {}

    # Validate or transform data
    base_file_path = f"{CWD}\{BASE_FILES_DIR}\IEEE34_form1.atp"

    # For Fault simulations
    buses = [
        802,
        832,
    ]
    Ri = 0.00001
    Rf = 20
    R_step = 20

    ti = 0.05
    tf = 0.1
    microgrid_state = True

    faults_checkbox = {
        "fault01": True,
        "fault02": True,
        "fault03": False,
        "fault04": False,
        "fault05": False,
        "fault06": True,
        "fault07": True,
        "fault08": False,
        "fault09": False,
        "fault10": False,
        "fault11": False,
    }

    # For chargeability simulations

    params["load_i"] = 75
    params["load_f"] = 135
    params["load_step"] = 5

    # Save params in dictionary
    params["buses"] = list(set(buses))
    params["Ri"] = Ri
    params["Rf"] = Rf
    params["R_step"] = R_step
    params["faults_checkbox"] = faults_checkbox

    params["ti"] = ti
    params["tf"] = tf
    params["microgrid_state"] = microgrid_state

    params["base_file_path"] = base_file_path

    # params["event"] = "fault"
    params["event"] = "load"
    return params


# dict.values()
# dict.keys()
# dict.items()
def main():
    params = fault_inputs()

    create_directories()

    if params["event"] == "fault":
        buses = params["buses"]
        Ri = params["Ri"]
        Rf = params["Rf"]
        R_step = params["R_step"]
        faults_checkbox = params["faults_checkbox"]

        # Create Bus-Impedance Combinations List
        impedances = np.around(np.arange(Ri, Rf + R_step, R_step), 5)
        bus_impedance = [(bus, z) for bus in buses for z in impedances]
        # Create Desired faults list
        checked_faults = [
            idx + 1 for idx, state in enumerate(faults_checkbox.values()) if state
        ]

        # Check if at least 1 event is selected
        if not (len(checked_faults) > 0):
            print("No hay fallas")
            return

        fault_list_creator(checked_faults, bus_impedance)

        create_copies(params["base_file_path"])

        ti = params["ti"]
        tf = params["tf"]
        microgrid_state = params["microgrid_state"]
        atp_fault_file(str(tf), str(ti), microgrid_state)

        atp_files_execution()

    elif params["event"] == "load":
        load_i = params["load_i"]
        load_f = params["load_f"]
        load_step = params["load_step"]
        load_percentages = np.around(
            np.arange(load_i, load_f + load_step, load_step), 2
        )
        load_percentages = load_percentages[load_percentages != 100]
        load_list_creator(load_percentages)


def load_list_creator(load_percentages: list):
    """Writes load variation list in FAULT_FILES_LIST

    Parameters
    ----------
    load_percentages : list
        List of all load percentage values
    """

    with open(f"{EVENTS_DIR}\{LOAD_FILES_LIST}", mode="w+") as f:
        for percentage in load_percentages:
            f.write(f"Load_{percentage}.atp\n")


if __name__ == "__main__":
    main()
