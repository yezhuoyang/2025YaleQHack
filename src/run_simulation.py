
import json

import numpy as np
import pandas as pd
from bloqade.qbraid.simulation_result import QuEraSimulationResult
from bloqade.visual.animation.gate_event import GateEvent
from bloqade.visual.animation.runtime.aod import AODMoveEvent
from bloqade.visual.animation.runtime.atoms import AtomTrajectory
from bloqade.visual.animation.runtime.ppoly import PPoly
from bloqade.visual.animation.runtime.qpustate import AnimateQPUState

from bloqade.qbraid import schema


def get_noise_model():
    single_qubit_error = schema.SingleQubitError(
        survival_prob=(survival_prob := tuple(1 for _ in range(10))),
        operator_error=(pauli_error_model := schema.PauliErrorModel()),
    )
    cz_error = schema.CZError(
        survival_prob=survival_prob,
        entangled_error=pauli_error_model,
        single_error=pauli_error_model,
        storage_error=pauli_error_model,
    )
    return schema.NoiseModel(
        all_qubits=(all_qubits := tuple(range(10))),
        gate_events=[
            schema.GateEvent(
                operation=schema.LocalW(
                    participants=(0,),
                    theta=0.25,
                    phi=0,
                ),
                error=single_qubit_error,
            ),
            schema.GateEvent(
                operation=schema.CZ(participants=((0, 1),)),
                error=cz_error,
            ),
            schema.GateEvent(
                operation=schema.CZ(participants=((0, 2),)),
                error=cz_error,
            ),
            schema.GateEvent(
                operation=schema.Measurement(
                    participants=all_qubits,
                ),
                error=single_qubit_error,
            ),
        ],
    )

def run_simulation(json_filename: str):
    noise_model = get_noise_model()

    x_x = np.array([0, 1, 2, 3, 4])
    x_c = np.random.rand(4, 4)
    x = PPoly(x_c, x_x)

    y_x = np.array([0, 1, 2, 3, 4])
    y_c = np.random.rand(4, 4)
    y = PPoly(y_c, y_x)

    animate_qpu_state = AnimateQPUState(
        block_durations=[15.0],
        gate_events=[(3.0, GateEvent("GlobalCZGate", {"Test": 1}, 10.0))],
        atoms=[AtomTrajectory(1, x, y, [(0.0, "Test")])],
        slm_zone=[(0.0, 0.0)],
        aod_moves=[AODMoveEvent(1.0, 1.0, x, y)],
    )

    counts = {}

    logs = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    quera_simulation_result = QuEraSimulationResult(
        flair_visual_version="0.0.1",
        counts=counts,
        logs=logs,
        atom_animation_state=animate_qpu_state,
        noise_model=noise_model,
    )
    open(json_filename, "w").write(
        json.dumps(quera_simulation_result.to_json(), indent=4)
    )
    
if __name__ == "__main__":
    run_simulation("./data/simulation.json")