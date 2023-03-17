import utils.CONFIG
from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST, SCENARIOS_DIR

# Matrices and stats
from scipy.stats import truncnorm
import numpy as np

# Regular expressions
import re

from pathlib import Path


def initial_loads_creator(
    min_load: float, max_load: float, events_amount
) -> np.ndarray:
    return np.around(np.random.uniform(min_load, max_load, events_amount), 2)


def load_list_creator(load_percentages: list):
    """Writes load variation list in EVENT_FILES_LIST

    Parameters
    ----------
    load_percentages : list
        List of all load percentage values
    """
    list_path = Path(f"{EVENTS_DIR}\{EVENT_FILES_LIST}")

    loads = []
    for load in load_percentages:
        loads.append(f"L{load:06.2f}.atp\n")
    new_lines = loads.copy()
    if list_path.is_file():
        new_lines = []
        with open(list_path, "r+") as f:
            lines = f.readlines()
        for line, load in zip(lines, loads):
            line = line.strip("\n")[:-4]
            new_lines.append(f"{line}_{load}")

    with open(list_path, "w+") as f:
        for line in new_lines:
            f.write(line)


def base_file_loads(lines: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Creates an array of admitances for each phase, with file line index

    Parameters
    ----------
    base_file_path : str
        List with files lines

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Phase A, B and C admitance matrices of shape (m, 2), where
        (,0) are indices of file lines where each load appears and
        (,1) are the admitance values (complex number)
    """
    # Validación suma admitancias serie
    lines_copy = lines.copy()
    Za = np.empty((0, 2))
    Zb = np.empty((0, 2))
    Zc = np.empty((0, 2))
    for idx, line in enumerate(lines_copy):
        if "C Load" in line:
            if "3f" in line:
                Ra = float(lines_copy[idx + 1][30:42])
                Xa = float(lines_copy[idx + 1][46:58])
                za = Ra + Xa * 1j
                if not np.abs(za) > 1e20:
                    Za = np.append(Za, [[idx + 1, za]], axis=0)

                Rb = float(lines_copy[idx + 2][30:42])
                Xb = float(lines_copy[idx + 2][46:58])
                zb = Rb + Xb * 1j
                if not np.abs(zb) > 1e20:
                    Zb = np.append(Zb, [[idx + 2, zb]], axis=0)

                Rc = float(lines_copy[idx + 3][30:42])
                Xc = float(lines_copy[idx + 3][46:58])
                zc = Rc + Xc * 1j
                if not np.abs(zc) > 1e20:
                    Zc = np.append(Zc, [[idx + 3, zc]], axis=0)
            else:
                R = float(lines_copy[idx + 1][30:42])
                X = float(lines_copy[idx + 1][46:58])
                z = R + X * 1j
                if " A" in line:
                    Za = np.append(Za, [[idx + 1, z]], axis=0)
                if " B" in line:
                    Zb = np.append(Zb, [[idx + 1, z]], axis=0)
                if " C" in line:
                    Zc = np.append(Zc, [[idx + 1, z]], axis=0)

    # Find Y total for each phase
    Ya = 1 / Za[:, 1]
    Yb = 1 / Zb[:, 1]
    Yc = 1 / Zc[:, 1]

    Ya = np.append([Za[:, 0]], [Ya], axis=0).T
    Yb = np.append([Zb[:, 0]], [Yb], axis=0).T
    Yc = np.append([Zc[:, 0]], [Yc], axis=0).T

    return Ya, Yb, Yc


# Distribución normal truncada
def get_truncated_normal(
    mean: float = 0, sd: int = 1, low: float = 0, upp: float = 10
) -> np.ndarray:
    """Return array of truncated normal distribution with:
    mean = mean
    standard deviation = sd
    lower limit = low
    upper limit = upp

    Parameters
    ----------
    mean : float, optional
        Truncated distribution Mean, by default 0
    sd : int, optional
        Truncated distribution standard deviation, by default 1
    low : float, optional
        Truncated distribution lower limit, by default 0
    upp : float, optional
        Truncated distribution upper limit, by default 10

    Returns
    -------
    np.ndarray
        Array of truncated normal distribution
    """
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def load_split(
    array: np.ndarray, len_a: int, len_b: int, len_c: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Splits array of normal distribution load percentages into
    three new arrays, one for each phase.

    Parameters
    ----------
    array : np.ndarray
        Array of percentages
    len_a : int
        Amount of loads on phase A
    len_b : int
        Amount of loads on phase B
    len_c : int
        Amount of loads on phase C

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        load percentages split for phase A, B and C, respectively
    """
    a = array[:len_a]
    b = array[len_a : len_a + len_b]
    c = array[len_a + len_b :]
    return a, b, c


def update_loads(Z_array: np.ndarray, lines_copy: list) -> list:
    """Returns list of lines with updated impedances

    Parameters
    ----------
    Z_array : np.ndarray
        Array of indices and impedances (complex number).
        Dimension (m, 2), where
            m = number of impedances
            (,0) = indices column
            (,1) = impedances column
    lines_copy : list
        List with .atp file content

    Returns
    -------
    list
        List of .atp file content with updated impedances
    """
    for Z in Z_array:
        idx = Z[0]
        z = Z[1]

        idx = int(idx)
        R = f"{z.real:.6f}".center(12)
        X = f"{z.imag:.6f}".center(12)
        line = lines_copy[idx]
        new_line = f"{line[:30]}{R}{line[42:46]}{X}{line[58:]}"

        lines_copy[idx] = new_line
    return lines_copy


def initial_load_state(YA, YB, YC, lines_copy, atp_file_name):
    pattern_load = "L(\d{3}\.\d{2})"
    pattern_load_change = "LC(\d{3}\.\d{2})_(\d{3}\.\d{2})"
    cargabilidad_inicial = float(re.search(pattern_load, atp_file_name).group(1))

    Ya = np.copy(YA[:, 1])
    Yb = np.copy(YB[:, 1])
    Yc = np.copy(YC[:, 1])
    idx_a = np.copy(YA[:, 0])
    idx_b = np.copy(YB[:, 0])
    idx_c = np.copy(YC[:, 0])

    len_a = Ya.shape[0]
    len_b = Yb.shape[0]
    len_c = Yc.shape[0]
    load_amount = len_a + len_b + len_c

    initial_load = (
        get_truncated_normal(mean=cargabilidad_inicial, sd=1, low=0, upp=200).rvs(
            load_amount
        )
        / 100
    )

    # Variación de Carga por Fase
    initial_a, initial_b, initial_c = load_split(initial_load, len_a, len_b, len_c)

    # Admitancias por fase iniciales y finales
    Ya_initial, Yb_initial, Yc_initial = (
        Ya * initial_a,
        Yb * initial_b,
        Yc * initial_c,
    )

    # Admitancia total luego de la variación de carga
    Y_initial_total = Ya_initial.sum() + Yb_initial.sum() + Yc_initial.sum()

    # Hallar impedancias a partir de las admitancias
    Za_initial = 1 / Ya_initial
    Zb_initial = 1 / Yb_initial
    Zc_initial = 1 / Yc_initial

    # Crear nuevo vector de impedancias con índices (concatenar Z_initial/target con idx)
    Za_ini = np.append([idx_a], [Za_initial], axis=0).T
    Zb_ini = np.append([idx_b], [Zb_initial], axis=0).T
    Zc_ini = np.append([idx_c], [Zc_initial], axis=0).T

    lines_copy = update_loads(Za_ini, lines_copy)
    lines_copy = update_loads(Zb_ini, lines_copy)
    lines_copy = update_loads(Zc_ini, lines_copy)

    return lines_copy


def load_change_list_creator(load_percentages: list):
    """Writes load variation list in EVENT_FILES_LIST

    Parameters
    ----------
    load_percentages : list
        List of all load percentage values
    """

    with open(f"{EVENTS_DIR}\{EVENT_FILES_LIST}", mode="w+") as f:
        for low, high in load_percentages:
            # f.write(f"Load_{percentage:06.2f}.atp\n")
            f.write(f"L{low:06.2f}_{high:06.2f}.atp\n")


# Name Loads
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
