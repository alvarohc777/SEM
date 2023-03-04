# For readpl4 Function 
import struct
import mmap


# NumPy Stack
import pandas as pd
import numpy as np

# Measure Performance
import time

# To access os 
import subprocess
import glob
import os

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

    with open("SCENARIOS_ATP\\" + pl4file, "rb") as f:

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
        file_path = currentDirectory + "\\SCENARIOS_ATP\\"
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


def atp_run(filename: str, ext: tuple, current_directory: str, solver: str):
    """Executes passed .atp file.

    Parameters
    ----------
    filename : str
        Name of .atp extension file.
    ext : tuple of str
        Extension of temporal files to remove after the simulation is done.
    current_directory : str
        Path where script is being executed (results folder must be at the same level as PFGUI.py)
    solver : str
        Path to solver (.bat file) containing code to execute atp-emtp
    """

    t1 = time.perf_counter()

    pl4_filename = filename.replace(".atp", ".pl4")
    print(f"Iniciando {filename}")
    atp_file_path = current_directory + "\\SCENARIOS_ATP"
    atp_file_name = atp_file_path + "\\" + filename

    apt_process = subprocess.Popen(
        ["C:\\ATP\\atpdraw\\ATP\\solver.bat", atp_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )

    apt_process.communicate()
    readPL4(pl4_filename)
    files_to_delete = []
    try:
        for file in ext:
            files_to_delete.extend(glob(file))
        for file in files_to_delete:
            os.remove(file)
    except:
        pass

    t2 = time.perf_counter()
    print(f"Terminó {filename} en {round(t2-t1, 3)}(s)")

if __name__=='__main__':
    print(__name__)