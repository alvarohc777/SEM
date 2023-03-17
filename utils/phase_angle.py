from utils.CONFIG import EVENTS_DIR, EVENT_FILES_LIST
import random


def source_phase_change(lines_copy: list, element_idx) -> list:
    main_source_idx = element_idx["mainSource"]
    MG_source_idx = element_idx["microGridSource"]
    phase_int = random.randint(0, 180)
    phase_dec = round(random.random(), 5)
    source_phase = phase_int + phase_dec
    phi_a = str(round(source_phase, 5))
    phi_b = str(round(source_phase - 120, 5))
    phi_c = str(round(source_phase - 240, 5))
    try:
        phase_line_a = lines_copy[main_source_idx]
        phase_line_b = lines_copy[main_source_idx + 1]
        phase_line_c = lines_copy[main_source_idx + 2]
        lines_copy[
            main_source_idx
        ] = f"{phase_line_a[:30]}{phi_a:>10}{phase_line_a[40:]}"
        lines_copy[
            main_source_idx + 1
        ] = f"{phase_line_b[:30]}{phi_b:>10}{phase_line_b[40:]}"
        lines_copy[
            main_source_idx + 2
        ] = f"{phase_line_c[:30]}{phi_c:>10}{phase_line_c[40:]}"
    except NameError:
        print("There is no source with mainSource in comment")
    try:
        phase_line = lines_copy[MG_source_idx]
        lines_copy[
            MG_source_idx
        ] = f"{phase_line[:30]}{str(round(source_phase+0.17, 5)):>10}{phase_line[40:]}"
    except NameError:
        print("There is no microgrid source with microGridSource in comment")
    return lines_copy
