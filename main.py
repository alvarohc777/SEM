# For readpl4 Function
import struct
import mmap

# NumPy Stack
import pandas as pd
import numpy as np
from scipy.stats import truncnorm

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
EVENT_FILES_LIST = "event_files_list.txt"


SOLVER = r"C:\ATP\atpdraw\ATP\solver.bat"
EXT = (f"{SCENARIOS_DIR}\*.dbg", f"{SCENARIOS_DIR}\*.lis")
CWD = os.getcwd()


# For Fault simulation
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

    f = open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", mode="w+")
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
    with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", mode="r") as f:
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
    with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
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
        row.strip("\n") for row in open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r")
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


# End Faults
# ---------------------------------------------------------------------------

# For load variation


# Distribución normal truncada
def get_truncated_normal(
    mean: float = 0, sd: int = 1, low: float = 0, upp: float = 10
) -> np.ndarray:
    """Return array of truncated normal distribution with:
    mean = mean
    standard deviation = sd
    lower limit = low
    upper limit = upp

    Parameters
    ----------
    mean : float, optional
        Truncated distribution Mean, by default 0
    sd : int, optional
        Truncated distribution standard deviation, by default 1
    low : float, optional
        Truncated distribution lower limit, by default 0
    upp : float, optional
        Truncated distribution upper limit, by default 10

    Returns
    -------
    np.ndarray
        Array of truncated normal distribution
    """
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def load_split(
    array: np.ndarray, len_a: int, len_b: int, len_c: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Splits array of normal distribution load percentages into
    three new arrays, one for each phase.

    Parameters
    ----------
    array : np.ndarray
        Array of percentages
    len_a : int
        Amount of loads on phase A
    len_b : int
        Amount of loads on phase B
    len_c : int
        Amount of loads on phase C

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        load percentages split for phase A, B and C, respectively
    """
    a = array[:len_a]
    b = array[len_a : len_a + len_b]
    c = array[len_a + len_b :]
    return a, b, c


def update_loads(Z_array: np.ndarray, lines_copy: list) -> list:
    """Returns list of lines with updated impedances

    Parameters
    ----------
    Z_array : np.ndarray
        Array of indices and impedances (complex number).
        Dimension (m, 2), where
            m = number of impedances
            (,0) = indices column
            (,1) = impedances column
    lines_copy : list
        List with .atp file content

    Returns
    -------
    list
        List of .atp file content with updated impedances
    """
    for Z in Z_array:
        idx = Z[0]
        z = Z[1]

        idx = int(idx)
        R = f"{z.real:.6f}".center(12)
        X = f"{z.imag:.6f}".center(12)
        line = lines_copy[idx]
        new_line = f"{line[:30]}{R}{line[42:46]}{X}{line[58:]}"

        lines_copy[idx] = new_line
    return lines_copy


def load_list_creator(load_percentages: list):
    """Writes load variation list in EVENT_FILES_LIST

    Parameters
    ----------
    load_percentages : list
        List of all load percentage values
    """

    with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", mode="w+") as f:
        for low, high in load_percentages:
            # f.write(f"Load_{percentage:06.2f}.atp\n")
            f.write(f"Load_{low:06.2f}_{high:06.2f}.atp\n")


def base_file_loads(lines: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Creates an array of admitances for each phase, with file line index

    Parameters
    ----------
    base_file_path : str
        List with files lines

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Phase A, B and C admitance matrices of shape (m, 2), where
        (,0) are indices of file lines where each load appears and
        (,1) are the admitance values (complex number)
    """
    # Validación suma admitancias serie
    lines_copy = lines.copy()
    Za = np.empty((0, 2))
    Zb = np.empty((0, 2))
    Zc = np.empty((0, 2))
    for idx, line in enumerate(lines_copy):
        if "C Load" in line:
            if "3f" in line:
                Ra = float(lines_copy[idx + 1][30:42])
                Xa = float(lines_copy[idx + 1][46:58])
                za = Ra + Xa * 1j
                if not np.abs(za) > 1e20:
                    Za = np.append(Za, [[idx + 1, za]], axis=0)

                Rb = float(lines_copy[idx + 2][30:42])
                Xb = float(lines_copy[idx + 2][46:58])
                zb = Rb + Xb * 1j
                if not np.abs(zb) > 1e20:
                    Zb = np.append(Zb, [[idx + 2, zb]], axis=0)

                Rc = float(lines_copy[idx + 3][30:42])
                Xc = float(lines_copy[idx + 3][46:58])
                zc = Rc + Xc * 1j
                if not np.abs(zc) > 1e20:
                    Zc = np.append(Zc, [[idx + 3, zc]], axis=0)
            else:
                R = float(lines_copy[idx + 1][30:42])
                X = float(lines_copy[idx + 1][46:58])
                z = R + X * 1j
                if " A" in line:
                    Za = np.append(Za, [[idx + 1, z]], axis=0)
                if " B" in line:
                    Zb = np.append(Zb, [[idx + 1, z]], axis=0)
                if " C" in line:
                    Zc = np.append(Zc, [[idx + 1, z]], axis=0)

    # Find Y total for each phase
    Ya = 1 / Za[:, 1]
    Yb = 1 / Zb[:, 1]
    Yc = 1 / Zc[:, 1]
    print(Za.shape)
    print(Ya.shape)

    Ya = np.append([Za[:, 0]], [Ya], axis=0).T
    Yb = np.append([Zb[:, 0]], [Yb], axis=0).T
    Yc = np.append([Zc[:, 0]], [Yc], axis=0).T

    return Ya, Yb, Yc


def initial_load_state(YA, YB, YC, lines):
    with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
        for atp_file_name in f:
            lines_copy = lines.copy()
            atp_file_name = atp_file_name.strip("\n")

            cargabilidad_inicial = float(atp_file_name[5:11])
            cargabilidad_final = float(atp_file_name[12:18])
            Ya = np.copy(YA[:, 1])
            Yb = np.copy(YB[:, 1])
            Yc = np.copy(YC[:, 1])
            idx_a = np.copy(YA[:, 0])
            idx_b = np.copy(YB[:, 0])
            idx_c = np.copy(YC[:, 0])

            print(atp_file_name)
            print(cargabilidad_inicial)
            print(cargabilidad_final)

            len_a = Ya.shape[0]
            len_b = Yb.shape[0]
            len_c = Yc.shape[0]
            load_amount = len_a + len_b + len_c

            delta_cargabilidad = cargabilidad_final - cargabilidad_inicial

            initial_load = (
                get_truncated_normal(
                    mean=cargabilidad_inicial, sd=1, low=0, upp=200
                ).rvs(load_amount)
                / 100
            )
            target_load = (
                get_truncated_normal(
                    mean=delta_cargabilidad, sd=1, low=-10, upp=10
                ).rvs(load_amount)
                / 100
            )

            # Variación de Carga por Fase
            initial_a, initial_b, initial_c = load_split(
                initial_load, len_a, len_b, len_c
            )
            target_a, target_b, target_c = load_split(target_load, len_a, len_b, len_c)
            print(f"Cargabilidad inicial: {np.mean(initial_a):.2%}\n")
            # Admitancias por fase iniciales y finales
            Ya_initial, Yb_initial, Yc_initial = (
                Ya * initial_a,
                Yb * initial_b,
                Yc * initial_c,
            )
            Ya_target = Ya_initial * target_a + Ya_initial
            Yb_target = Yb_initial * target_b + Yb_initial
            Yc_target = Yc_initial * target_c + Yc_initial

            # Admitancia total luego de la variación de carga
            Y_initial_total = Ya_initial.sum() + Yb_initial.sum() + Yc_initial.sum()
            Y_target_total = Ya_target.sum() + Yb_target.sum() + Yc_target.sum()

            # Hallar impedancias a partir de las admitancias
            Za_initial = 1 / Ya_initial
            Zb_initial = 1 / Yb_initial
            Zc_initial = 1 / Yc_initial
            Za_target = 1 / Ya_target
            Zb_target = 1 / Yb_target
            Zc_target = 1 / Yc_target

            # Crear nuevo vector de impedancias con índices (concatenar Z_initial/targer con Z)
            Za_ini = np.append([idx_a], [Za_initial], axis=0).T
            Za_tar = np.append([idx_a], [Za_target], axis=0).T
            Zb_ini = np.append([idx_b], [Zb_initial], axis=0).T
            Zb_tar = np.append([idx_b], [Zb_target], axis=0).T
            Zc_ini = np.append([idx_c], [Zc_initial], axis=0).T
            Zc_tar = np.append([idx_c], [Zc_target], axis=0).T

            lines_copy = update_loads(Za_ini, lines_copy)
            lines_copy = update_loads(Zb_ini, lines_copy)
            lines_copy = update_loads(Zc_ini, lines_copy)

            with open(f"{SCENARIOS_DIR}\{atp_file_name}", "w") as file:
                file.writelines(lines_copy)

            # with open("IEEE34_form1_update_loads_prueba.atp", "w+") as f:
            #     lines_copy = update_loads(Za_ini, lines_copy)
            #     lines_copy = update_loads(Zb_ini, lines_copy)
            #     lines_copy = update_loads(Zc_ini, lines_copy)
            #     f.writelines(lines_copy)


# End Load Variation
# ----------------------------------------------------------------------------


# Simulating App Inputs
def fault_inputs() -> dict:
    """Function to receive all simulation parameters inputs

    Returns
    -------
    dict
        Dictionary with simulations parameters
    """
    params = {}

    # Validate or transform data
    base_file_path = f"{CWD}\{BASE_FILES_DIR}\IEEE34_form1_update_loads.atp"

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

    params["load_low"] = 75
    params["load_high"] = 135
    params["events_amount"] = 15
    params["max_load_step"] = 5

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
        load_low = params["load_low"]
        load_high = params["load_high"]
        max_load_step = params["max_load_step"]
        events_amount = params["events_amount"]

        initial_load_values = np.around(
            np.random.uniform(load_low, load_high, events_amount), 2
        )
        target_load_values = target_load_vect(
            initial_load_values, load_high, load_low, max_load_step
        )
        target_load_values = np.around(target_load_values, 2)
        load_values = np.stack((initial_load_values, target_load_values), axis=1)

        #

        load_list_creator(load_values)
        create_copies(params["base_file_path"])
        # Copy lines
        with open(params["base_file_path"], "r+") as f:
            lines = f.readlines()

        Ya, Yb, Yc = base_file_loads(lines)
        initial_load_state(Ya, Yb, Yc, lines)

        # create_copies


def target_load(
    initial_load: np.ndarray, load_high: float, load_low: float, max_load_step: float
) -> float:
    """Takes initual load perctentage and returns target load percentage

    Parameters
    ----------
    initial_load : np.ndarray
        Initial load percentage
    load_high : float
        Upper load percentage limit.
    load_low : float
        Lower load percentage limit.
    max_load_step : float
        Max percentage difference between initial_load and target load

    Returns
    -------
    float
        target load percentage
    """
    max_val = initial_load + max_load_step
    min_val = initial_load - max_load_step
    if initial_load > load_high - max_load_step:
        return np.random.uniform(min_val, load_high)
    elif initial_load < load_low + max_load_step:
        return np.random.uniform(load_low, max_val)
    else:
        return np.random.uniform(min_val, max_val)


target_load_vect = np.vectorize(target_load)


if __name__ == "__main__":
    main()
