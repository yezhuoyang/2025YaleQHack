import numpy as np
import math
from typing import List, Tuple, Dict, Union, Optional, Callable
from enum import Enum

from bloqade import qasm2
from kirin.dialects import ilist
from bloqade.qasm2.rewrite.native_gates import RydbergGateSetRewriteRule
from kirin import ir
from kirin.rewrite import Walk
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold

from PauliHamiltonian import PauliOp, PauliTerm, PauliHamiltonian


class SuzukiTrotter:
    """
    Class to perform Suzuki-Trotter evolution for a Pauli Hamiltonian.
    
    Implements various orders of the Suzuki-Trotter product formula to simulate
    the time evolution operator e^(-iHt) for a Hamiltonian H.
    """
    
    def __init__(self, hamiltonian: PauliHamiltonian):
        """
        Initialize a SuzukiTrotter simulator with a Pauli Hamiltonian.
        
        Args:
            hamiltonian: The Hamiltonian to simulate.
        """
        self.hamiltonian = hamiltonian
        self.terms = hamiltonian.terms
        self.n_qubits = hamiltonian.get_n_qubits()
        
        # We'll group terms by commutation relationships for more efficient trotterization
        self.grouped_terms = hamiltonian.group_terms_by_type()
        
        # Create commuting groups for more efficient evolution
        self.commuting_groups = hamiltonian.commuting_groups()
        
    @staticmethod
    def _compile_trotter_circuit(circuit_kernel, parallelize: bool = True):
        """
        Compile a Trotter circuit using Bloqade's custom compiler pipeline.
        
        Args:
            circuit_kernel: The circuit kernel function decorated with @qasm2.extended
            parallelize: Whether to apply parallelization optimizations
            
        Returns:
            Compiled circuit kernel
        """
        # Create extended dialect for compiler optimization
        @ir.dialect_group(qasm2.extended)
        def extended_opt(self):
            native_rewrite = Walk(RydbergGateSetRewriteRule(self))
            parallelize_pass = UOpToParallel(self)
            agg_fold = QASM2Fold(self)

            def run_pass(
                kernel: ir.Method,
                *,
                fold: bool = True,
                typeinfer: bool = True,
                parallelize: bool = False,
            ):
                assert qasm2.extended.run_pass is not None
                qasm2.extended.run_pass(kernel, fold=fold, typeinfer=typeinfer)
                native_rewrite.rewrite(kernel.code)

                # Apply parallelization if requested
                if parallelize:
                    agg_fold.fixpoint(kernel)
                    parallelize_pass(kernel)

            return run_pass
            
        # Create a new version of the circuit with our optimization passes
        compiled_kernel = circuit_kernel.similar()
        extended_opt.run_pass(compiled_kernel, parallelize=parallelize)
        
        return compiled_kernel
    
    def _get_pauli_evolution_circuit(self, term: PauliTerm, time: float) -> Callable:
        """
        Generate a quantum circuit to implement e^(-i * term * time).
        
        Args:
            term: PauliTerm to evolve
            time: Evolution time
            
        Returns:
            Circuit generator function
        """
        coefficient = term.coefficient
        operators = term.operators
        
        @qasm2.extended
        def circuit_gen(qreg: qasm2.QReg):
            # Handle different types of Pauli terms
            
            # Case 1: Identity term - global phase, no circuit needed
            if not operators:
                # Just a global phase, no operation needed
                pass
                
            # Case 2: Single Pauli operator
            elif len(operators) == 1:
                qubit_idx, op = list(operators.items())[0]
                angle = -coefficient * time
                
                if op == PauliOp.X:
                    # Implement e^(-i * X * angle)
                    qasm2.h(qreg[qubit_idx])
                    qasm2.rz(qreg[qubit_idx], 2 * angle)
                    qasm2.h(qreg[qubit_idx])
                    
                elif op == PauliOp.Y:
                    # Implement e^(-i * Y * angle)
                    qasm2.rx(qreg[qubit_idx], np.pi/2)
                    qasm2.rz(qreg[qubit_idx], 2 * angle)
                    qasm2.rx(qreg[qubit_idx], -np.pi/2)
                    
                elif op == PauliOp.Z:
                    # Implement e^(-i * Z * angle)
                    qasm2.rz(qreg[qubit_idx], 2 * angle)
                    
                # Identity operator requires no gates
            
            # Case 3: Two-qubit Pauli operator
            elif len(operators) == 2:
                qubits = sorted(operators.keys())
                angle = -coefficient * time
                
                # Get the two Pauli operators
                op1 = operators[qubits[0]]
                op2 = operators[qubits[1]]
                
                # Implementation strategy depends on the Pauli types
                
                # ZZ two-qubit interaction
                if op1 == PauliOp.Z and op2 == PauliOp.Z:
                    # Implement e^(-i * Z⊗Z * angle)
                    # Using CNOT-RZ-CNOT decomposition
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    qasm2.rz(qreg[qubits[1]], 2 * angle)
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                
                # XX two-qubit interaction
                elif op1 == PauliOp.X and op2 == PauliOp.X:
                    # Implement e^(-i * X⊗X * angle)
                    # Transform to ZZ using Hadamards
                    qasm2.h(qreg[qubits[0]])
                    qasm2.h(qreg[qubits[1]])
                    
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    qasm2.rz(qreg[qubits[1]], 2 * angle)
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    
                    qasm2.h(qreg[qubits[0]])
                    qasm2.h(qreg[qubits[1]])
                
                # YY two-qubit interaction
                elif op1 == PauliOp.Y and op2 == PauliOp.Y:
                    # Implement e^(-i * Y⊗Y * angle)
                    # Transform to ZZ using rotations
                    qasm2.rx(qreg[qubits[0]], np.pi/2)
                    qasm2.rx(qreg[qubits[1]], np.pi/2)
                    
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    qasm2.rz(qreg[qubits[1]], 2 * angle)
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    
                    qasm2.rx(qreg[qubits[0]], -np.pi/2)
                    qasm2.rx(qreg[qubits[1]], -np.pi/2)
                
                # XY interaction
                elif op1 == PauliOp.X and op2 == PauliOp.Y:
                    # Implement e^(-i * X⊗Y * angle)
                    qasm2.h(qreg[qubits[0]])
                    qasm2.rx(qreg[qubits[1]], np.pi/2)
                    
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    qasm2.rz(qreg[qubits[1]], 2 * angle)
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    
                    qasm2.h(qreg[qubits[0]])
                    qasm2.rx(qreg[qubits[1]], -np.pi/2)
                
                # Other combinations - use a similar approach with appropriate basis transformations
                # XZ, YX, YZ, ZX, ZY interactions would be handled here in a complete implementation
                # For brevity, not all combinations are shown
                else:
                    # General approach for any two-qubit Pauli term
                    # First, transform to computational basis
                    for i, q in enumerate(qubits):
                        if operators[q] == PauliOp.X:
                            qasm2.h(qreg[q])
                        elif operators[q] == PauliOp.Y:
                            qasm2.rx(qreg[q], np.pi/2)
                    
                    # Apply controlled-Z rotation
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    qasm2.rz(qreg[qubits[1]], 2 * angle)
                    qasm2.cx(qreg[qubits[0]], qreg[qubits[1]])
                    
                    # Transform back from computational basis
                    for i, q in enumerate(qubits):
                        if operators[q] == PauliOp.X:
                            qasm2.h(qreg[q])
                        elif operators[q] == PauliOp.Y:
                            qasm2.rx(qreg[q], -np.pi/2)
            
            # Case 4: Multi-qubit Pauli operator (3+ qubits)
            else:
                qubits = sorted(operators.keys())
                angle = -coefficient * time
                
                # For multi-qubit Pauli strings, we first transform each qubit
                # to the appropriate basis (X, Y, or Z)
                for q in qubits:
                    if operators[q] == PauliOp.X:
                        qasm2.h(qreg[q])
                    elif operators[q] == PauliOp.Y:
                        qasm2.rx(qreg[q], np.pi/2)
                
                # Then implement a multi-controlled Z rotation
                # We use a ladder of CNOT gates
                for i in range(len(qubits) - 1):
                    qasm2.cx(qreg[qubits[i]], qreg[qubits[i+1]])
                
                # Apply the rotation on the last qubit
                qasm2.rz(qreg[qubits[-1]], 2 * angle)
                
                # Undo the CNOT ladder
                for i in range(len(qubits) - 1, 0, -1):
                    qasm2.cx(qreg[qubits[i-1]], qreg[qubits[i]])
                
                # Transform back from computational basis
                for q in qubits:
                    if operators[q] == PauliOp.X:
                        qasm2.h(qreg[q])
                    elif operators[q] == PauliOp.Y:
                        qasm2.rx(qreg[q], -np.pi/2)
                        
        return circuit_gen
    
    def first_order_trotter(self, time: float, n_steps: int = 1) -> Callable:
        """
        Implement first-order Suzuki-Trotter formula: e^(A+B)t ≈ [e^(At/n) e^(Bt/n)]^n
        
        Args:
            time: Total evolution time
            n_steps: Number of Trotter steps
            
        Returns:
            Circuit generator function
        """
        dt = time / n_steps
        
        @qasm2.extended
        def circuit_gen(qreg: qasm2.QReg = None):
            if qreg is None:
                qreg = qasm2.qreg(self.n_qubits)
                
            # For each Trotter step
            for _ in range(n_steps):
                # Apply each term in sequence
                for term in self.terms:
                    # Get circuit for this term and apply it
                    term_circuit = self._get_pauli_evolution_circuit(term, dt)
                    term_circuit(qreg)
                    
                    # Add a barrier to maintain correct ordering
                    if len(term.operators) > 0:
                        qubits_used = [qreg[i] for i in term.get_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
            
            return qreg
            
        return circuit_gen
    
    def second_order_trotter(self, time: float, n_steps: int = 1) -> Callable:
        """
        Implement second-order (symmetric) Suzuki-Trotter formula:
        e^(A+B)t ≈ [e^(At/2n) e^(Bt/n) e^(At/2n)]^n
        
        Args:
            time: Total evolution time
            n_steps: Number of Trotter steps
            
        Returns:
            Circuit generator function
        """
        dt = time / n_steps
        
        @qasm2.extended
        def circuit_gen(qreg: qasm2.QReg = None):
            if qreg is None:
                qreg = qasm2.qreg(self.n_qubits)
                
            # For each Trotter step
            for _ in range(n_steps):
                # First half of terms in forward order
                for i, term in enumerate(self.terms):
                    # Apply half-step for first part
                    term_circuit = self._get_pauli_evolution_circuit(term, dt/2)
                    term_circuit(qreg)
                    
                    # Add barrier
                    if len(term.operators) > 0:
                        qubits_used = [qreg[i] for i in term.get_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
                
                # Second half of terms in reverse order
                for i in range(len(self.terms)-1, -1, -1):
                    term = self.terms[i]
                    # Apply half-step for second part
                    term_circuit = self._get_pauli_evolution_circuit(term, dt/2)
                    term_circuit(qreg)
                    
                    # Add barrier
                    if len(term.operators) > 0:
                        qubits_used = [qreg[i] for i in term.get_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
            
            return qreg
            
        return circuit_gen
    
    def trotter_suzuki_recursive(self, time: float, n_steps: int = 1, order: int = 2) -> Callable:
        """
        Implement the recursive Suzuki-Trotter formula of arbitrary even order.
        
        For k > 1, the formula is defined recursively:
        S_2k(λ) = [S_2k-2(p_k λ)]^2 [S_2k-2((1-4p_k)λ)] [S_2k-2(p_k λ)]^2
        where p_k = 1/(4-4^(1/(2k-1)))
        
        Args:
            time: Total evolution time
            n_steps: Number of Trotter steps
            order: The order of the formula (must be even)
            
        Returns:
            Circuit generator function
        """
        if order % 2 != 0 or order < 2:
            raise ValueError("Order must be a positive even integer")
            
        dt = time / n_steps
        
        # Base case: second-order formula
        if order == 2:
            return self.second_order_trotter(time, n_steps)
        
        # Recursive case
        # Calculate the p_k coefficient for the recursive formula
        k = order // 2
        p_k = 1.0 / (4.0 - 4.0**(1.0/(2.0*k-1.0)))
        
        # Get the circuit for the lower order
        lower_order_circuit = self.trotter_suzuki_recursive(time, n_steps, order-2)
        
        @qasm2.extended
        def circuit_gen(qreg: qasm2.QReg = None):
            if qreg is None:
                qreg = qasm2.qreg(self.n_qubits)
                
            # For each Trotter step
            for _ in range(n_steps):
                # Implement the recursive formula:
                # S_2k(λ) = [S_2k-2(p_k λ)]^2 [S_2k-2((1-4p_k)λ)] [S_2k-2(p_k λ)]^2
                
                # First [S_2k-2(p_k λ)]^2 term
                for _ in range(2):
                    lower_order_circuit(qreg, time=p_k*dt, n_steps=1)
                
                # Middle [S_2k-2((1-4p_k)λ)] term
                lower_order_circuit(qreg, time=(1-4*p_k)*dt, n_steps=1)
                
                # Last [S_2k-2(p_k λ)]^2 term
                for _ in range(2):
                    lower_order_circuit(qreg, time=p_k*dt, n_steps=1)
            
            return qreg
            
        return circuit_gen
    
    def optimized_trotter(self, time: float, n_steps: int = 1, order: int = 1, 
                        parallelize: bool = True) -> Callable:
        """
        Generate an optimized Trotter circuit that uses commutation relationships
        to reduce the circuit depth and improve accuracy.
        
        Args:
            time: Total evolution time
            n_steps: Number of Trotter steps
            order: Trotter order (1, 2, or higher even number)
            parallelize: Whether to apply parallelization optimizations
            
        Returns:
            An optimized circuit generator function
        """
        dt = time / n_steps
        
        @qasm2.extended
        def circuit_gen(qreg: qasm2.QReg = None):
            if qreg is None:
                qreg = qasm2.qreg(self.n_qubits)
                
            # For each Trotter step
            for _ in range(n_steps):
                if order == 1:
                    # First-order Trotter formula
                    # Apply each commuting group as a block
                    for group in self.commuting_groups:
                        # Process all terms in this commuting group
                        for term in group.terms:
                            term_circuit = self._get_pauli_evolution_circuit(term, dt)
                            term_circuit(qreg)
                        
                        # Add barrier between commuting groups
                        qubits_used = [qreg[i] for i in group.get_all_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
                
                elif order == 2:
                    # Second-order Trotter formula
                    # First half of commuting groups in forward order
                    for group in self.commuting_groups:
                        # Process all terms in this commuting group
                        for term in group.terms:
                            term_circuit = self._get_pauli_evolution_circuit(term, dt/2)
                            term_circuit(qreg)
                        
                        # Add barrier between commuting groups
                        qubits_used = [qreg[i] for i in group.get_all_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
                    
                    # Second half of commuting groups in reverse order
                    for group in reversed(self.commuting_groups):
                        # Process all terms in this commuting group
                        for term in group.terms:
                            term_circuit = self._get_pauli_evolution_circuit(term, dt/2)
                            term_circuit(qreg)
                        
                        # Add barrier between commuting groups
                        qubits_used = [qreg[i] for i in group.get_all_qubits()]
                        if qubits_used:
                            qasm2.barrier(qubits_used)
                
                else:
                    # Higher-order Trotter using recursive formula
                    # This is a simplified implementation that doesn't fully leverage
                    # the commutation relationships for higher orders
                    high_order_circuit = self.trotter_suzuki_recursive(dt, 1, order)
                    high_order_circuit(qreg)
            
            return qreg
            
        # Compile the circuit with optimizations if requested
        if parallelize:
            return self._compile_trotter_circuit(circuit_gen, parallelize=True)
        
        return circuit_gen
    
    def trotterize(self, time: float, n_steps: int = 1, order: int = 1, 
                    optimize: bool = True, parallelize: bool = True) -> Callable:
        """
        Main method to generate a trotterized circuit for the given Hamiltonian.
        
        Args:
            time: Total evolution time
            n_steps: Number of Trotter steps
            order: Trotter order (1, 2, or higher even number)
            optimize: Whether to use commutation relationships for optimization
            parallelize: Whether to apply circuit parallelization
            
        Returns:
            A circuit generator function that can be used with Bloqade
        """
        if optimize:
            return self.optimized_trotter(time, n_steps, order, parallelize)
        
        if order == 1:
            return self.first_order_trotter(time, n_steps)
        elif order == 2:
            return self.second_order_trotter(time, n_steps)
        else:
            return self.trotter_suzuki_recursive(time, n_steps, order)


# Example usage
if __name__ == "__main__":
    from PauliHamiltonian import create_transverse_field_ising_model
    from bloqade.qasm2.emit import QASM2
    from bloqade.qasm2.parse import pprint
    
    # Create an example Hamiltonian - Transverse field Ising model
    n_qubits = 4
    j_coupling = 1.0  # ZZ interaction strength
    h_field = 0.5     # X field strength
    
    tfim = create_transverse_field_ising_model(n_qubits, j_coupling, h_field)
    print(f"TFIM Hamiltonian: {tfim}")
    
    # Create a SuzukiTrotter instance
    trotter = SuzukiTrotter(tfim)
    
    # Generate a trotterized circuit
    evolution_time = 1.0
    trotter_steps = 2
    trotter_order = 2
    
    circuit = trotter.trotterize(
        time=evolution_time,
        n_steps=trotter_steps,
        order=trotter_order,
        optimize=True,
        parallelize=True
    )
    
    # Print the QASM2 representation of the circuit
    target = QASM2(allow_parallel=True)
    ast = target.emit(circuit)
    pprint(ast)