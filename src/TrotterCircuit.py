#!/usr/bin/env python3
"""
Bloqade Circuit Generation

This module converts Trotterized Hamiltonians to optimized QASM2 circuits
compatible with Bloqade.
"""

import math
import sys
from typing import List, Dict, Tuple, Union, Optional, Set, Callable

# Import Bloqade if available
from bloqade import qasm2
    
# # Mock implementation for testing without Bloqade
# class MockQASM2:
#     class Qubit:
#         def __init__(self, index):
#             self.index = index
            
#     @staticmethod
#     def qreg(n):
#         return [MockQASM2.Qubit(i) for i in range(n)]
        
#     @staticmethod
#     def cx(control, target):
#         print(f"CX: {control.index} -> {target.index}")
        
#     @staticmethod
#     def rx(target, angle):
#         print(f"RX({angle}): {target.index}")
        
#     @staticmethod
#     def ry(target, angle):
#         print(f"RY({angle}): {target.index}")
        
#     @staticmethod
#     def rz(target, angle):
#         print(f"RZ({angle}): {target.index}")
        
#     @staticmethod
#     def extended(func):
#         return func
        
# qasm2 = MockQASM2()

# Import PauliHamiltonian and Trotterization

# Adjust import paths as needed
sys.path.append('/Users/harrywanghc/Developer/2025/2025YaleQHack/src/')
from PauliHamiltonian import PauliOp, PauliTerm, PauliHamiltonian
from SuzukiTrotter import Trotterization

# ===== Circuit Building Functions =====

@qasm2.extended
def single_qubit_pauli_rotation(qubit: qasm2.Qubit, pauli_type: PauliOp, angle: float):
    """
    Apply a rotation around a Pauli axis.
    
    Args:
        qubit: The qubit to apply the rotation to
        pauli_type: The Pauli operator to rotate around (X, Y, or Z)
        angle: The rotation angle
    """
    if pauli_type == PauliOp.X:
        qasm2.rx(qubit, angle)
    elif pauli_type == PauliOp.Y:
        qasm2.ry(qubit, angle)
    elif pauli_type == PauliOp.Z:
        qasm2.rz(qubit, angle)
    # No operation needed for Identity (I)


@qasm2.extended
def pauli_basis_change(qubit: qasm2.Qubit, from_basis: PauliOp, to_basis: PauliOp):
    """
    Change the basis of a qubit from one Pauli basis to another.
    
    Args:
        qubit: The qubit to apply the basis change to
        from_basis: The starting Pauli basis
        to_basis: The target Pauli basis
    """
    # No change needed if bases are the same
    if from_basis == to_basis:
        return
        
    # No change needed for Identity
    if from_basis == PauliOp.I or to_basis == PauliOp.I:
        return
        
    # Z ↔ X
    if (from_basis == PauliOp.Z and to_basis == PauliOp.X) or \
        (from_basis == PauliOp.X and to_basis == PauliOp.Z):
        qasm2.ry(qubit, math.pi / 2)
        
    # Z ↔ Y
    elif (from_basis == PauliOp.Z and to_basis == PauliOp.Y) or \
        (from_basis == PauliOp.Y and to_basis == PauliOp.Z):
        qasm2.rx(qubit, -math.pi / 2)
        
    # X ↔ Y
    elif (from_basis == PauliOp.X and to_basis == PauliOp.Y) or \
        (from_basis == PauliOp.Y and to_basis == PauliOp.X):
        qasm2.rz(qubit, math.pi / 2)


@qasm2.extended
def pauli_string_exponentiation(
    qubits: List[qasm2.Qubit],
    pauli_string: Dict[int, PauliOp],
    angle: float,
):
    """
    Implement e^(-i * angle * P), where P is a tensor product of Pauli operators.
    
    Args:
        qubits: List of qubits
        pauli_string: Dictionary mapping qubit indices to Pauli operators
        angle: Rotation angle
    """
    used_qubits = []
    used_paulis = []
    
    # Extract the qubits and operators involved
    for idx, op in pauli_string.items():
        if op != PauliOp.I:  # Skip Identity operators
            used_qubits.append(qubits[idx])
            used_paulis.append(op)
    
    # Handle special cases
    if len(used_qubits) == 0:
        # Global phase (all identities) - no operation needed
        return
    elif len(used_qubits) == 1:
        # Single qubit rotation
        single_qubit_pauli_rotation(used_qubits[0], used_paulis[0], angle)
        return
    
    # For multi-qubit Pauli strings:
    
    # 1. Change basis to Z for all qubits
    for i, qubit in enumerate(used_qubits):
        pauli_basis_change(qubit, used_paulis[i], PauliOp.Z)
    
    # 2. Apply ZZ...Z rotation using CNOT ladder
    for i in range(len(used_qubits) - 1):
        qasm2.cx(used_qubits[i], used_qubits[i + 1])
    
    # Apply Z rotation on the last qubit
    qasm2.rz(used_qubits[-1], angle)
    
    # Undo the CNOT ladder
    for i in range(len(used_qubits) - 1, 0, -1):
        qasm2.cx(used_qubits[i - 1], used_qubits[i])
    
    # 3. Change basis back
    for i, qubit in enumerate(used_qubits):
        pauli_basis_change(qubit, PauliOp.Z, used_paulis[i])


@qasm2.extended
def apply_pauli_term(qubits: List[qasm2.Qubit], term: PauliTerm, time: float):
    """
    Apply the time evolution operator e^(-i * H * time) for a single Pauli term.
    
    Args:
        qubits: List of qubits
        term: PauliTerm to apply
        time: Evolution time
    """
    # Calculate the angle (coefficient * time)
    angle = term.coefficient.real * time
    
    # Apply the Pauli string exponentiation
    pauli_string_exponentiation(qubits, term.operators, angle)


# ===== Circuit Optimization Functions =====

def optimize_circuit_layout(terms: List[PauliTerm]) -> Dict[int, int]:
    """
    Optimize the circuit layout by reordering qubits to minimize CNOT gates.
    
    Args:
        terms: List of PauliTerm objects
        
    Returns:
        Dictionary mapping original qubit indices to new indices
    """
    # Identify all qubits used
    all_qubits = set()
    for term in terms:
        all_qubits.update(term.get_qubits())
    
    # For each pair of qubits, count how many terms they appear together in
    interaction_strength = {}
    for i in all_qubits:
        for j in all_qubits:
            if i < j:
                interaction_strength[(i, j)] = 0
                
    # Count interactions
    for term in terms:
        qubits = term.get_qubits()
        for i in qubits:
            for j in qubits:
                if i < j:
                    interaction_strength[(i, j)] += 1
                    
    # Sort pairs by interaction strength
    sorted_pairs = sorted(interaction_strength.items(), key=lambda x: x[1], reverse=True)
    
    # Create a greedy qubit layout
    layout = {}
    next_idx = 0
    
    # Process pairs in order of interaction strength
    for (i, j), _ in sorted_pairs:
        if i not in layout:
            layout[i] = next_idx
            next_idx += 1
        if j not in layout:
            layout[j] = next_idx
            next_idx += 1
            
    # Add any remaining qubits
    for q in all_qubits:
        if q not in layout:
            layout[q] = next_idx
            next_idx += 1
            
    return layout


# ===== Main Execution Functions =====

@qasm2.extended
def trotterize_hamiltonian(hamiltonian: PauliHamiltonian, time: float, steps: int, order: int = 1):
    """
    Create a QASM2 circuit implementing Trotterized time evolution.
    
    Args:
        hamiltonian: PauliHamiltonian to evolve
        time: Total evolution time
        steps: Number of Trotter steps
        order: Trotter order (1, 2, or 4)
        
    Returns:
        QASM2 circuit function
    """
    # Generate the Trotter sequence
    trotter_sequence = Trotterization.get_trotter_sequence(hamiltonian, time, steps, order)
    
    # Get number of qubits needed
    n_qubits = hamiltonian.get_n_qubits()
    
    # Optimize the qubit layout
    qubit_layout = optimize_circuit_layout(hamiltonian.terms)
    
    @qasm2.extended
    def circuit():
        """The Trotterized circuit function"""
        # Create quantum register
        qubits = qasm2.qreg(n_qubits)
        
        # Apply each term in the Trotter sequence
        for term, dt in trotter_sequence:
            apply_pauli_term(qubits, term, dt)
            
        return qubits
    
    return circuit


def create_qasm2_program(hamiltonian: PauliHamiltonian, time: float, steps: int, order: int = 1) -> str:
    """
    Create a QASM2 program string for the Trotterized evolution.
    
    Args:
        hamiltonian: PauliHamiltonian to evolve
        time: Total evolution time
        steps: Number of Trotter steps
        order: Trotter order (1, 2, or 4)
        
    Returns:
        QASM2 program as a string
    """
        
    # Create the circuit function
    circuit_func = trotterize_hamiltonian(hamiltonian, time, steps, order)
    
    # Emit QASM2 code
    target = qasm2.emit.QASM2()
    ast = target.emit(circuit_func)
    
    # Convert AST to string (if available)
    if hasattr(qasm2, 'parse') and hasattr(qasm2.parse, 'to_string'):
        return qasm2.parse.to_string(ast)
    else:
        return str(ast)  # Fallback


# ===== Example Usage =====

def create_example_hamiltonian() -> PauliHamiltonian:
    """Create an example Hamiltonian for testing"""
    h = PauliHamiltonian()
    
    # Add some X terms
    h.add_term(PauliTerm(0.5, {0: PauliOp.X}))
    h.add_term(PauliTerm(0.3, {1: PauliOp.X}))
    
    # Add some Z terms
    h.add_term(PauliTerm(0.7, {0: PauliOp.Z}))
    h.add_term(PauliTerm(0.2, {2: PauliOp.Z}))
    
    # Add some interaction terms
    h.add_term(PauliTerm(0.4, {0: PauliOp.Z, 1: PauliOp.Z}))
    h.add_term(PauliTerm(0.1, {1: PauliOp.Y, 2: PauliOp.Y}))
    h.add_term(PauliTerm(0.25, {0: PauliOp.X, 2: PauliOp.Z}))
    
    return h


@qasm2.extended
def main():
    """Example main function"""
    # Create an example Hamiltonian
    hamiltonian = create_example_hamiltonian()
    
    # Print Hamiltonian information
    print(f"Example Hamiltonian: {hamiltonian}")
    print(f"Number of terms: {len(hamiltonian.terms)}")
    
    # Create and return the trotterized circuit
    time = 1.0
    steps = 2
    order = 2
    
    circuit = trotterize_hamiltonian(hamiltonian, time, steps, order)
    return circuit()


if __name__ == "__main__":
    # Generate QASM2 program
    hamiltonian = create_example_hamiltonian()
    qasm_program = create_qasm2_program(hamiltonian, time=1.0, steps=2, order=2)
    
    print("QASM2 Program:")
    print(qasm_program)