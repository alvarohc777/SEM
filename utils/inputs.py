import utils.CONFIG as CONFIG


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

    base_file_name = "IEEE34_T01_V1.atp"
    # base_file_name = "IEEE34_5s.atp"
    # base_file_name = "IEEE34_No_MG.atp"
    # base_file_name = "IEEE34_NoSwitches.atp"
    # base_file_name = "IEEE34_form1_update_loads.atp"
    # base_file_name = "IEEE34_No_IIDR.atp"
    base_file_path = f"{CWD}\{BASE_FILES_DIR}\{base_file_name}"

    CONFIG.BASE_FILE_NAME = base_file_name
    CONFIG.BASE_FILE_PATH = base_file_path

    # For Fault simulations
    buses = [312, 116]
    Ri = 0.00001

    Rf = 0.00001
    R_step = 0.00001

    ti = 0.05
    tf = 4
    microgrid_state = True

    faults_checkbox = {
        "fault01": True,
        "fault02": True,
        "fault03": True,
        "fault04": True,
        "fault05": True,
        "fault06": True,
        "fault07": True,
        "fault08": True,
        "fault09": True,
        "fault10": True,
        "fault11": True,
    }
    # For new chargeability atp

    # For chargeability simulations

    params["min_load"] = 90
    params["max_load"] = 120
    params["events_amount"] = 160
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

    params["event"] = "fault"
    # params["event"] = "loads"
    # params["event"] = "load_change"
    return params
