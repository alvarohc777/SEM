# lines = update_simulation_time(lines, element_idx["simulation_time"])
def update_simulation_time(lines, simulation_time, simulation_time_idx):
    simulation_time = str(simulation_time).rjust(8)
    simulation_time_line = lines[simulation_time_idx]
    lines[simulation_time_idx] = (
        simulation_time_line[:8] + simulation_time + simulation_time[16:]
    )
    return lines
