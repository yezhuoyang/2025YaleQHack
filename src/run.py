from run_simulation import run_simulation
from generate_mpeg import generate_mpeg
from fix_simulation import fix_simulation

if __name__ == "__main__":
    simulation_file: str = "./data/simulation.json"
    run_simulation(simulation_file)
    fix_simulation(simulation_file)
    generate_mpeg(simulation_file)