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

    # base_file_name = "IEEE34.atp"
    base_file_name = "IEEE34_5s.atp"
    # base_file_name = "IEEE34_No_MG.atp"
    # base_file_name = "IEEE34_NoSwitches.atp"
    # base_file_name = "IEEE34_form1_update_loads.atp"
    # base_file_name = "IEEE34_No_IIDR.atp"
    base_file_path = f"{CWD}\{BASE_FILES_DIR}\{base_file_name}"

    CONFIG.BASE_FILE_NAME = base_file_name
    CONFIG.BASE_FILE_PATH = base_file_path

    # For Fault simulations
    buses = [
        802,
    ]
    Ri = 0.00001

    Rf = 20
    R_step = 20

    ti = 0.03
    tf = 0.06
    microgrid_state = True

    faults_checkbox = {
        "fault01": True,
        "fault02": False,
        "fault03": False,
        "fault04": False,
        "fault05": False,
        "fault06": False,
        "fault07": False,
        "fault08": False,
        "fault09": False,
        "fault10": False,
        "fault11": False,
    }
    # For new chargeability atp

    # For chargeability simulations

    params["min_load"] = 40
    params["max_load"] = 200
    params["events_amount"] = 5
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
    # params["event"] = "loads"
    params["event"] = "load_change"
    return params
