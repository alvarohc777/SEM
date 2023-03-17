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
