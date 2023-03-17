# CONSTANTS
from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST

# Regular expressions
import re


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


def atp_fault_file(lines_copy, params, element_idx, atp_file_name):
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
    tf : str
        Fault final time
    ti : str
        Fault initial time
    microgrid_state : bool
        Microgrid Switch State (True: microgrid on / False: microgrid off)
    """
    # Get parameters from file
    nombre = atp_file_name.rstrip("\n")
    pattern_bus_name = "B(\d{3})"
    pattern_Rfalla = "RF(.*?)(_|\.atp)"
    pattern_TipoFalla = "Fault(.*?)_"
    Rfalla = re.search(pattern_Rfalla, nombre).group(1)
    Tipo_Falla = re.search(pattern_TipoFalla, nombre).group(1)
    bus = re.search(pattern_bus_name, nombre).group(1)

    # Get parameters from params dict
    ti = str(params["ti"])
    tf = str(params["tf"])
    microgrid_state = params["microgrid_state"]

    # Fault Event Parameters
    d_lineA = element_idx["lineA"]
    d_lineB = element_idx["lineB"]
    d_lineC = element_idx["lineC"]
    d_lineSA = element_idx["lineSA"]
    d_lineSB = element_idx["lineSB"]
    d_lineSC = element_idx["lineSC"]
    d_linesg = element_idx["linesg"]
    d_lineswmr = element_idx["lineswmr"]
    d_lineswmr = element_idx["lineswmr"]

    lines_copy = setgridop(d_lineswmr, lines_copy, microgrid_state)
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
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "02":
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "03":
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "04":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
    if Tipo_Falla == "05":
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
    if Tipo_Falla == "06":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
    if Tipo_Falla == "07":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "08":
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "09":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
    if Tipo_Falla == "10":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
    if Tipo_Falla == "11":
        data_dict["FaultSwA"]["open_time"] = tf
        data_dict["FaultSwA"]["close_time"] = ti
        data_dict["FaultSwB"]["open_time"] = tf
        data_dict["FaultSwB"]["close_time"] = ti
        data_dict["FaultSwC"]["open_time"] = tf
        data_dict["FaultSwC"]["close_time"] = ti
        data_dict["FaultSwG"]["open_time"] = tf
        data_dict["FaultSwG"]["close_time"] = ti
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

    return lines_copy


def setgridop(d_lineswmr: int, lines_copy: list, microgrid_state: bool):
    """Sets microgrid switch state (closed or open)

    Parameters
    ----------
    d_lineswmr : int
        Index of line containing information of microgrid switch
    lines_copy : list
        List containing all lines of atp file.
    microgrid_state : bool
        Whether microgrid switch is closed or open

    Returns
    -------
    _type_
        _description_
    """
    if microgrid_state == True:
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
    if microgrid_state == False:
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
