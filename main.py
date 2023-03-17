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

# CONSTANTS
from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST, SCENARIOS_DIR

import utils.CONFIG as CONFIG
from utils import loads, tool_start
from utils.tool_start import create_directories
import utils.phase_angle as phase_angle
import utils.atp_exec as atp_exec
import utils.tool_start as tool_start
from utils.loads import (
    initial_loads_creator,
    load_list_creator,
    base_file_loads,
    initial_load_state,
)


# Simulating App Inputs
def inputs() -> dict:
    """Function to receive all simulation parameters inputs

    Returns
    -------
    dict
        Dictionary with simulations parameters
    """
    params = {}

    # Validate or transform data
    CWD = CONFIG.CWD
    BASE_FILES_DIR = CONFIG.BASE_FILES_DIR

    base_file_name = "IEEE34.atp"
    base_file_path = f"{CWD}\{BASE_FILES_DIR}\{base_file_name}"

    CONFIG.BASE_FILE_NAME = base_file_name
    CONFIG.BASE_FILE_PATH = base_file_path

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
    # For new chargeability atp

    # For chargeability simulations

    params["min_load"] = 75
    params["max_load"] = 135
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
    params["base_file_name"] = base_file_name

    # params["event"] = "fault"
    params["event"] = "loads"
    return params


def main():
    params = inputs()
    tool_start.create_directories()
    BASE_FILE_PATH = CONFIG.BASE_FILE_PATH
    BASE_FILE_NAME = CONFIG.BASE_FILE_NAME

    # Copy lines from base file
    with open(BASE_FILE_PATH, "r+") as f:
        lines = f.readlines()

    element_idx = tool_start.element_indices(lines)

    if params["event"] == "loads":
        # Initial Parameters
        print(CONFIG.BASE_FILE_PATH)
        min_load = params["min_load"]
        max_load = params["max_load"]
        max_load_step = params["max_load_step"]
        events_amount = params["events_amount"]

        initial_load_values = initial_loads_creator(min_load, max_load, events_amount)
        load_list_creator(initial_load_values)

        Ya, Yb, Yc = base_file_loads(lines)
        with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
            for atp_file_name in f:
                atp_file_name = atp_file_name.strip("\n")
                lines_copy = lines.copy()
                lines_copy = phase_angle.source_phase_change(lines_copy, element_idx)
                lines_copy = initial_load_state(Ya, Yb, Yc, lines_copy, atp_file_name)
                with open(f"{SCENARIOS_DIR}\{atp_file_name}", "w") as file:
                    file.writelines(lines_copy)
        atp_exec.atp_files_execution()


if __name__ == "__main__":
    main()
