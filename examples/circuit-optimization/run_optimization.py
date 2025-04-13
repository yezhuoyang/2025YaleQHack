
import argparse
import json
import os

CURR_DIR = os.path.dirname(os.path.abspath(__file__))



def qiskit_optimization(qasm: str):
    from qiskit import qasm2
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    qc = qasm2.loads(qasm)
    n_qubits = qc.num_qubits
    backend = GenericBackendV2(num_qubits=n_qubits)
    pass_manager = generate_preset_pass_manager(
        optimization_level=3,
        backend=backend,
        basis_gates=["cx", "u3"],
        coupling_map=None,  # No coupling map for disabling qubit mapping
        initial_layout=None,  # No initial layout
        layout_method=None,  # No layout method
        routing_method=None,  # No routing method
        approximation_degree=1,
    )
    qc_opt = pass_manager.run(qc)
    return qasm2.dumps(qc_opt)


def pyzx_optimization(qasm: str, up_to_perm: bool = False):
    import pyzx as zx

    circuit = zx.Circuit.from_qasm(qasm)
    graph = circuit.to_graph()
    zx.simplify.full_reduce(graph, quiet=True)
    circuit = zx.extract_circuit(graph, up_to_perm=up_to_perm)
    circuit = circuit.to_basic_gates()
    circuit = circuit.split_phase_gates()
    return circuit.to_qasm()


def eval_qasm(qasm: str):
    try:
        import pyzx as zx
        circuit = zx.Circuit.from_qasm(qasm).to_basic_gates()
    except:
        print("Error in eval_qasm")
        print("-" * 80)
        raise ValueError
    return {
        "n": circuit.qubits,
        "2q": circuit.twoqubitcount(),
        "clifford": circuit.stats_dict()["clifford"],
        "t": circuit.tcount(),
        "g": circuit.stats_dict()["gates"],
    }

from score import get_cost
from bloqade_parallel import run_bloqade_parallelize


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run circuit optimization.')
    parser.add_argument(
        '--qasm_file', type=str, required=True,
        help='Path to the QASM file to be optimized.'
    )
    parser.add_argument(
        '--method', type=str, required=True,
        help='Optimization method to be used (e.g., "zx", "parallel").'
    )
    args = parser.parse_args()
    # Load QASM input
    print(f"[INFO] Loading QASM file: {args.qasm_file}")
    qasm_input: str = open(args.qasm_file).read()

    # Convert QASM to CX+U3
    qasm_str: str = qiskit_optimization(qasm_input)
    print(f"[INFO] Cost before optimization: {get_cost(qasm_str)}")
    
    if "zx" in args.method:
        print(f"[INFO] Running ZX optimization...")
        qasm_str = pyzx_optimization(qasm_str)    
        qasm_str = qiskit_optimization(qasm_str)
    
    if "parallel" in args.method:
        print(f"[INFO] Running Bloqade parallelization...")
        qasm_str = run_bloqade_parallelize(qasm_str)
        
    print(f"[INFO] Cost after optimization: {get_cost(qasm_str)}")
    
    final_qasm_str: str = qasm_str
    
    output_file = args.qasm_file.replace(".qasm", f"-{args.method}.qasm")
    print(f"[INFO] Saving optimized QASM file to: {output_file}")
    open(output_file, "w").write(final_qasm_str)