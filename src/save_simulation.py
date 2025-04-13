import json

from typing import List

from load_zac_code import JobData, Instruction
from generate_mpeg import generate_mpeg

import numpy as np
import pandas as pd
from bloqade.qbraid.simulation_result import QuEraSimulationResult
from bloqade.visual.animation.gate_event import GateEvent
from bloqade.visual.animation.runtime.aod import AODMoveEvent
from bloqade.visual.animation.runtime.atoms import AtomTrajectory
from bloqade.visual.animation.runtime.ppoly import PPoly
from bloqade.visual.animation.runtime.qpustate import AnimateQPUState

from bloqade.qbraid import schema

def run_simulation(json_filename: str, output_json_filename: str):
    # First, load the job data JSON (using our JobData and Instruction classes defined earlier)
    with open(json_filename, "r") as f:
        json_str = f.read()
    # Assume JobData.from_json is defined as in the previous example.
    job_data = JobData.from_json(json_str)

    # Prepare containers for simulation events
    block_durations = []
    gate_events = []
    atoms = []
    aod_moves = []

    # For demonstration, we create a common PPoly for trajectories
    # In practice these should be created from actual simulation data.
    x_poly = PPoly(np.random.rand(4, 4), np.array([0, 1, 2, 3, 4]))
    y_poly = PPoly(np.random.rand(4, 4), np.array([0, 1, 2, 3, 4]))

    # Iterate through the instructions in the job data and create events accordingly.
    for inst in job_data.instructions:
        if inst.type == "init":
            # For an "init" instruction, assume each initial location gives rise to an atom trajectory.
            init_locs = inst.details.get("init_locs", [])
            for loc in init_locs:
                # Using the first element of loc as a dummy atom ID.
                atom_id = loc[0]
                # Create an AtomTrajectory with an event at the begin_time of the init instruction.
                atoms.append(AtomTrajectory(atom_id, x_poly, y_poly, [(inst.begin_time, "Init")]))
        elif inst.type == "1qGate":
            # For a one-qubit gate, create a gate event.
            # Here we assume the unitary type is stored in details under "unitary".
            gate_type = inst.details.get("unitary", "UnknownGate")
            # Use the dependency info to get a qubit identifier if available.
            dependency = inst.details.get("dependency", {})
            qubit = dependency.get("qubit", [None])[0]
            duration = inst.end_time - inst.begin_time
            gate_events.append((inst.begin_time, GateEvent(gate_type, {"qubit": qubit}, duration)))
        elif inst.type == "rearrangeJob":
            # For a "rearrangeJob", treat it as an AOD move event.
            duration = inst.end_time - inst.begin_time
            # Create an AODMoveEvent; in a real scenario, you might derive the polynomials from loc data.
            aod_moves.append(AODMoveEvent(inst.begin_time, duration, x_poly, y_poly))
            # Also, we record this rearrange as a block duration.
            block_durations.append(duration)
        # You can add additional conversions for other instruction types (e.g., "rydberg") as needed.

    # Define a default slm_zone; in practice this may be derived from the instructions.
    slm_zone = [(0.0, 0.0)]

    # Create the AnimateQPUState object
    animate_qpu_state = AnimateQPUState(
        block_durations=block_durations,
        gate_events=gate_events,
        atoms=atoms,
        slm_zone=slm_zone,
        aod_moves=aod_moves,
    )

    # Create dummy counts and logs for demonstration purposes
    counts = {}
    logs = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    # Get a noise model (your implementation might differ)
    noise_model = get_noise_model()

    # Instantiate the QuEraSimulationResult
    quera_simulation_result = QuEraSimulationResult(
        flair_visual_version="0.0.1",
        counts=counts,
        logs=logs,
        atom_animation_state=animate_qpu_state,
        noise_model=noise_model,
    )

    # Write the simulation result to a JSON file
    with open(output_json_filename, "w") as f:
        f.write(json.dumps(quera_simulation_result.to_json(), indent=2))

# Example usage (when running as a script)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run QuEra simulation from job JSON data.")
    parser.add_argument("json_file", type=str, nargs="?", default="./data/zac_code.json",
                        help="Path to the JSON file containing job data.")
    parser.add_argument("output_json_file", type=str, nargs="?", default="./data/zac_code_out.json",
                        help="Path to the JSON file containing job data.")
    args = parser.parse_args()

    run_simulation(args.json_file, args.output_json_file)
    generate_mpeg(args.output_json_file)