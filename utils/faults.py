from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST


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
