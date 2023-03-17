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


# End Faults
# ---------------------------------------------------------------------------

# For load variation


# Name generation
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


# End Load Variation
# ----------------------------------------------------------------------------


# dict.values()
# dict.keys()
# dict.items()
def main():
    a = "hola"
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
        print(BASE_FILE_NAME)
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


if __name__ == "__main__":
    main()
