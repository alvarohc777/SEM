# From NumPy Stack
import numpy as np

# CONSTANTS
from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST, SCENARIOS_DIR

import utils.CONFIG as CONFIG
from utils import loads, tool_start, simulation_settings

# import modules from utils
import utils.inputs as inputs
import utils.phase_angle as phase_angle
import utils.atp_exec as atp_exec
import utils.tool_start as tool_start
import utils.faults as faults


# Simulating App Inputs
def main():
    params = inputs.inputs()
    tool_start.create_directories()
    BASE_FILE_PATH = CONFIG.BASE_FILE_PATH

    # Copy lines from base file
    with open(BASE_FILE_PATH, "r+") as f:
        lines = f.readlines()

    element_idx = tool_start.element_indices(lines)

    lines = simulation_settings.update_simulation_time(
        lines, params["simulation_time"], element_idx["simulation_time"]
    )

    if params["event"] == "loads":
        # Initial Parameters
        print(CONFIG.BASE_FILE_PATH)

        # Load simulation Parameters
        min_load = params["min_load"]
        max_load = params["max_load"]
        max_load_step = params["max_load_step"]
        events_amount = params["events_amount"]

        initial_load_values = loads.initial_loads_creator(
            min_load, max_load, events_amount
        )
        loads.load_list_creator(initial_load_values)

        Ya, Yb, Yc = loads.base_file_loads(lines)
        with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
            for atp_file_name in f:
                atp_file_name = atp_file_name.strip("\n")
                print(atp_file_name)
                lines_copy = lines.copy()
                lines_copy = phase_angle.source_phase_change(lines_copy, element_idx)
                lines_copy, *_ = loads.initial_load_state(
                    Ya, Yb, Yc, lines_copy, atp_file_name
                )
                with open(f"{SCENARIOS_DIR}\{atp_file_name}", "w+") as file:
                    file.writelines(lines_copy)
    if params["event"] == "load_change":
        # Load simulation Parameters
        min_load = params["min_load"]
        max_load = params["max_load"]
        max_load_step = params["max_load_step"]
        events_amount = params["events_amount"]

        initial_load_values = loads.initial_loads_creator(
            min_load, max_load, events_amount
        )
        target_load_values = loads.target_load_vect(
            initial_load_values, max_load, min_load, max_load_step
        )
        target_load_values = np.around(target_load_values, 2)
        load_values = np.stack((initial_load_values, target_load_values), axis=1)
        loads.load_change_list_creator(load_values)
        YA, YB, YC = loads.base_file_loads(lines)
        with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
            for atp_file_name in f:
                print(f"atp_file_name: {atp_file_name}")
                atp_file_name = atp_file_name.strip("\n")
                lines_copy = lines.copy()
                # lines_copy = phase_angle.source_phase_change(lines_copy, element_idx)
                lines_copy, Ya, Yb, Yc = loads.initial_load_state(
                    YA, YB, YC, lines_copy, atp_file_name
                )
                target_lines = loads.target_load_state(
                    Ya, Yb, Yc, lines_copy, atp_file_name
                )
                lines_copy = loads.load_change(lines_copy, target_lines, params)
                with open(f"{SCENARIOS_DIR}\{atp_file_name}", "w+") as file:
                    file.writelines(lines_copy)
        # atp_exec.atp_files_execution()
    if params["event"] == "fault":
        # Fault simulation parameters
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

        faults.fault_list_creator(checked_faults, bus_impedance)

        # Load simulation Parameters
        min_load = params["min_load"]
        max_load = params["max_load"]
        max_load_step = params["max_load_step"]
        events_amount = len(bus_impedance) * len(checked_faults)

        initial_load_values = loads.initial_loads_creator(
            min_load, max_load, events_amount
        )
        loads.load_list_creator(initial_load_values)
        YA, YB, YC = loads.base_file_loads(lines)
        with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", "r") as f:
            for atp_file_name in f:
                atp_file_name = atp_file_name.strip("\n")
                print(atp_file_name)

                # Modify copied lines
                lines_copy = lines.copy()
                lines_copy = phase_angle.source_phase_change(lines_copy, element_idx)
                lines_copy, *_ = loads.initial_load_state(
                    YA, YB, YC, lines_copy, atp_file_name
                )
                lines_copy = faults.atp_fault_file(
                    lines_copy, params, element_idx, atp_file_name
                )
                with open(f"{SCENARIOS_DIR}\{atp_file_name}", "w") as file:
                    file.writelines(lines_copy)

    atp_exec.atp_files_execution()


if __name__ == "__main__":
    main()
