import shutil
import os
from utils.CONFIG import EVENTS_DIR, SCENARIOS_DIR, CSV_DIR


def create_directories():
    """Creates directories for tool"""
    # Create new events lists directory -> fault_list_
    if os.path.exists(EVENTS_DIR):
        shutil.rmtree(EVENTS_DIR)
    os.mkdir(EVENTS_DIR)

    # Create new atp scenarios directory -> create_copies()
    if os.path.exists(SCENARIOS_DIR):
        shutil.rmtree(SCENARIOS_DIR)
    os.mkdir(SCENARIOS_DIR)

    # # Create new CSV scenarios directory -> create_copies()
    if os.path.exists(CSV_DIR):
        shutil.rmtree(CSV_DIR)
    os.mkdir(CSV_DIR)


def element_indices(lines: list) -> dict:
    """Finds all elements of interest in file

    Parameters
    ----------
    lines : list
        atp file lines

    Returns
    -------
    dict
        Dictionary containing all elements of interest and
        indices found in file.

    """
    element_idx = {}
    for line_idx, line in enumerate(lines):
        if "C RFA" in line:
            element_idx["lineA"] = line_idx + 1
        if "C RFB" in line:
            element_idx["lineB"] = line_idx + 1
        if "C RFC" in line:
            element_idx["lineC"] = line_idx + 1
        if "C FaultSwA" in line:
            element_idx["lineSA"] = line_idx + 1
        if "C FaultSwB" in line:
            element_idx["lineSB"] = line_idx + 1
        if "C FaultSwC" in line:
            element_idx["lineSC"] = line_idx + 1
        if "C FaultSwGround" in line:
            element_idx["linesg"] = line_idx + 1
        if "C SMR2" in line:
            element_idx["lineswmr"] = line_idx + 1
        if "C SMR1" in line:
            element_idx["lineswmr"] = line_idx + 1
        if "C mainSource" in line:
            element_idx["mainSource"] = line_idx + 1
        if "C microGridSource" in line:
            element_idx["microGridSource"] = line_idx + 1
        if "C switch load tri" in line:
            element_idx["load_switch_tri"] = lines[line_idx : line_idx + 4].copy()
        if "C switch load mono" in line:
            element_idx["load_switch_mono"] = lines[line_idx : line_idx + 2].copy()
        # if "C switch load tri" in line:
        #     element_idx["load_switch_tri"] = lines[line_idx : line_idx + 4].copy()
        # elif "C switch load mono" in line:
        #     element_idx["load_switch_mono"] = lines[line_idx : line_idx + 2].copy()

    return element_idx
