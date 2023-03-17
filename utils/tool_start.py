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
