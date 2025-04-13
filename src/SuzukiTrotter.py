#!/usr/bin/env python3
"""
Trotterization Implementation

This module provides functions for Suzuki-Trotterization of quantum Hamiltonians
represented using the Pauli Hamiltonian System.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Union, Optional, Set, Callable

# Import necessary classes from PauliHamiltonian
import sys
sys.path.append('/Users/harrywanghc/Developer/2025/2025YaleQHack/src/')
from PauliHamiltonian import PauliOp, PauliTerm, PauliHamiltonian

class Trotterization:
    """Class for Suzuki-Trotterization of quantum Hamiltonians"""
    
    @staticmethod
    def collect_commuting_terms(terms: List[PauliTerm]) -> List[List[PauliTerm]]:
        """
        Group Pauli terms into sets of mutually commuting terms.
        This is an important optimization for Trotterization.
        
        Args:
            terms: List of PauliTerm objects
            
        Returns:
            List of lists, where each inner list contains commuting terms
        """
        if not terms:
            return []
            
        # Start with each term in its own group
        groups = [[term] for term in terms]
        
        # Try to merge groups
        i = 0
        while i < len(groups):
            j = i + 1
            while j < len(groups):
                # Check if all terms in group i commute with all terms in group j
                all_commute = True
                
                for term_i in groups[i]:
                    for term_j in groups[j]:
                        if not term_i.commutes_with(term_j):
                            all_commute = False
                            break
                    if not all_commute:
                        break
                        
                if all_commute:
                    # Merge group j into group i
                    groups[i].extend(groups[j])
                    groups.pop(j)
                else:
                    j += 1
                    
            i += 1
            
        return groups
    
    @staticmethod
    def first_order_trotter(hamiltonian: PauliHamiltonian, time: float, steps: int) -> List[Tuple[PauliTerm, float]]:
        """
        Generate a first-order Trotter sequence.
        
        Args:
            hamiltonian: The Hamiltonian to evolve
            time: Total evolution time
            steps: Number of Trotter steps
            
        Returns:
            List of (term, time) tuples to apply sequentially
        """
        dt = time / steps
        trotter_sequence = []
        
        # Group terms that commute
        commuting_groups = Trotterization.collect_commuting_terms(hamiltonian.terms)
        
        # For each Trotter step, apply all terms
        for _ in range(steps):
            for group in commuting_groups:
                # Terms in the same group can be applied in any order or simultaneously
                for term in group:
                    trotter_sequence.append((term, dt))
                    
        return trotter_sequence
    
    @staticmethod
    def second_order_trotter(hamiltonian: PauliHamiltonian, time: float, steps: int) -> List[Tuple[PauliTerm, float]]:
        """
        Generate a second-order (symmetric) Trotter sequence.
        
        Args:
            hamiltonian: The Hamiltonian to evolve
            time: Total evolution time
            steps: Number of Trotter steps
            
        Returns:
            List of (term, time) tuples to apply sequentially
        """
        dt = time / steps
        trotter_sequence = []
        
        # Group terms that commute
        commuting_groups = Trotterization.collect_commuting_terms(hamiltonian.terms)
        
        # For each Trotter step, apply the symmetric formula
        for _ in range(steps):
            # First half: Apply all terms with dt/2
            for group in commuting_groups:
                for term in group:
                    trotter_sequence.append((term, dt/2))
                    
            # Second half: Apply all terms with dt/2 in reverse order
            for group in reversed(commuting_groups):
                for term in group:
                    trotter_sequence.append((term, dt/2))
                    
        return trotter_sequence
    
    @staticmethod
    def fourth_order_trotter(hamiltonian: PauliHamiltonian, time: float, steps: int) -> List[Tuple[PauliTerm, float]]:
        """
        Generate a fourth-order Suzuki-Trotter sequence.
        
        Args:
            hamiltonian: The Hamiltonian to evolve
            time: Total evolution time
            steps: Number of Trotter steps
            
        Returns:
            List of (term, time) tuples to apply sequentially
        """
        dt = time / steps
        trotter_sequence = []
        
        # Constants for fourth-order decomposition
        p = 4 - 4**(1/3)
        
        # Helper function for second-order step
        def second_order_step(step_time):
            step_sequence = []
            commuting_groups = Trotterization.collect_commuting_terms(hamiltonian.terms)
            
            # First half
            for group in commuting_groups:
                for term in group:
                    step_sequence.append((term, step_time/2))
            
            # Second half (reverse order)
            for group in reversed(commuting_groups):
                for term in group:
                    step_sequence.append((term, step_time/2))
                    
            return step_sequence
        
        # For each Trotter step, apply the fourth-order formula
        for _ in range(steps):
            # Recursive construction using three second-order steps
            trotter_sequence.extend(second_order_step(p * dt / 4))
            trotter_sequence.extend(second_order_step((1 - p/2) * dt))
            trotter_sequence.extend(second_order_step(p * dt / 4))
                
        return trotter_sequence
    
    @staticmethod
    def get_trotter_sequence(hamiltonian: PauliHamiltonian, time: float, steps: int, order: int = 1) -> List[Tuple[PauliTerm, float]]:
        """
        Get a Trotter sequence for the given Hamiltonian.
        
        Args:
            hamiltonian: The Hamiltonian to evolve
            time: Total evolution time
            steps: Number of Trotter steps
            order: Trotter order (1, 2, or 4)
            
        Returns:
            List of (term, time) tuples to apply sequentially
        """
        if order == 1:
            return Trotterization.first_order_trotter(hamiltonian, time, steps)
        elif order == 2:
            return Trotterization.second_order_trotter(hamiltonian, time, steps)
        elif order == 4:
            return Trotterization.fourth_order_trotter(hamiltonian, time, steps)
        else:
            raise ValueError(f"Unsupported Trotter order: {order}. Supported orders are 1, 2, and 4.")
    
    @staticmethod
    def simulate_trotter_evolution(hamiltonian: PauliHamiltonian, initial_state: np.ndarray, 
                                time: float, steps: int, order: int = 1) -> np.ndarray:
        """
        Directly simulate Trotterized time evolution using matrix exponentiation.
        
        Args:
            hamiltonian: The Hamiltonian to evolve under
            initial_state: Initial state vector
            time: Total evolution time
            steps: Number of Trotter steps
            order: Trotter order (1, 2, or 4)
            
        Returns:
            Final state vector after evolution
        """
        n_qubits = hamiltonian.get_n_qubits()
        dim = 2**n_qubits
        
        if initial_state.shape[0] != dim:
            raise ValueError(f"Initial state dimension ({initial_state.shape[0]}) does not match Hamiltonian size (2^{n_qubits} = {dim}).")
        
        # Get the Trotter sequence
        trotter_sequence = Trotterization.get_trotter_sequence(hamiltonian, time, steps, order)
        
        # Initialize state
        state = initial_state.copy()
        
        # Apply each evolution step
        for term, dt in trotter_sequence:
            # Create evolution operator: U = exp(-i*H*dt)
            term_matrix = term.to_sparse_matrix(n_qubits)
            evolution_op = np.exp(-1j * term_matrix.toarray() * dt)
            
            # Apply evolution operator
            state = evolution_op @ state
            
        return state


# Helper functions for creating common Hamiltonians

def create_ising_hamiltonian(n_qubits: int, j: float = 1.0, h: float = 1.0) -> PauliHamiltonian:
    """
    Create a transverse field Ising model Hamiltonian:
    H = -J ∑ Z_i Z_{i+1} - h ∑ X_i
    
    Args:
        n_qubits: Number of qubits
        j: Coupling strength (J)
        h: Transverse field strength (h)
        
    Returns:
        PauliHamiltonian representing the TFIM
    """
    ham = PauliHamiltonian()
    
    # Add ZZ interaction terms
    for i in range(n_qubits - 1):
        term = PauliTerm(-j, {i: PauliOp.Z, i+1: PauliOp.Z})
        ham.add_term(term)
    
    # Add transverse field (X) terms
    for i in range(n_qubits):
        term = PauliTerm(-h, {i: PauliOp.X})
        ham.add_term(term)
        
    return ham


def create_heisenberg_xyz_hamiltonian(n_qubits: int, jx: float = 1.0, jy: float = 1.0, jz: float = 1.0) -> PauliHamiltonian:
    """
    Create a Heisenberg XYZ model Hamiltonian:
    H = ∑ [Jx X_i X_{i+1} + Jy Y_i Y_{i+1} + Jz Z_i Z_{i+1}]
    
    Args:
        n_qubits: Number of qubits
        jx: X-coupling strength
        jy: Y-coupling strength
        jz: Z-coupling strength
        
    Returns:
        PauliHamiltonian representing the Heisenberg XYZ model
    """
    ham = PauliHamiltonian()
    
    for i in range(n_qubits - 1):
        # Add XX interaction
        ham.add_term(PauliTerm(jx, {i: PauliOp.X, i+1: PauliOp.X}))
        
        # Add YY interaction
        ham.add_term(PauliTerm(jy, {i: PauliOp.Y, i+1: PauliOp.Y}))
        
        # Add ZZ interaction
        ham.add_term(PauliTerm(jz, {i: PauliOp.Z, i+1: PauliOp.Z}))
        
    return ham


# Example usage
if __name__ == "__main__":
    # Create a simple Hamiltonian
    h = create_ising_hamiltonian(n_qubits=3, j=1.0, h=0.5)
    
    print("Hamiltonian:", h)
    
    # Generate a Trotter sequence
    time = 1.0
    steps = 4
    order = 2
    
    trotter_sequence = Trotterization.get_trotter_sequence(h, time, steps, order)
    
    print(f"\nTrotter decomposition (order {order}, {steps} steps):")
    for i, (term, dt) in enumerate(trotter_sequence[:10]):
        print(f"  Step {i+1}: Evolve under {term} for time {dt}")
        
    if len(trotter_sequence) > 10:
        print(f"  ... and {len(trotter_sequence) - 10} more steps")
        
    # Find commuting groups
    commuting_groups = Trotterization.collect_commuting_terms(h.terms)
    
    print(f"\nCommuting groups ({len(commuting_groups)}):")
    for i, group in enumerate(commuting_groups):
        print(f"  Group {i+1}: {' + '.join(str(term) for term in group)}")