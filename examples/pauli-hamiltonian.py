import numpy as np
import sys
sys.path.append('/Users/harrywanghc/Developer/2025/2025YaleQHack/src/')
from PauliHamiltonian import (
    PauliOp, PauliTerm, PauliHamiltonian, 
    create_transverse_field_ising_model
)

def main():
    print("== Basic Pauli Hamiltonian Example ==")
    
    # Create a simple 2-qubit Hamiltonian
    h = PauliHamiltonian()
    
    # Add X term on qubit 0
    h.add_term(PauliTerm(1.0, {0: PauliOp.X}))
    
    # Add Z term on qubit 1
    h.add_term(PauliTerm(0.5, {1: PauliOp.Z}))
    
    # Add ZZ interaction between qubits 0 and 1
    h.add_term(PauliTerm(0.25, {0: PauliOp.Z, 1: PauliOp.Z}))
    
    print(f"Hamiltonian: {h}")
    
    # Get matrix representation
    n_qubits = 2
    matrix = h.to_sparse_matrix(n_qubits)
    
    # Convert to dense for display
    dense_matrix = matrix.toarray()
    print(f"\nMatrix representation (shape {dense_matrix.shape}):")
    print(np.round(dense_matrix, 3))
    
    # Group terms by type
    grouped = h.group_terms_by_type()
    print("\nTerms grouped by type:")
    for term_type, group in grouped.items():
        if group.terms:
            print(f"  {term_type}: {group}")
    
    # Group terms into commuting sets
    commuting_groups = h.commuting_groups()
    print(f"\nNumber of commuting groups: {len(commuting_groups)}")
    for i, group in enumerate(commuting_groups):
        print(f"  Group {i+1}: {group}")
    
    # Create a more complex Hamiltonian - TFIM
    print("\n== Transverse Field Ising Model ==")
    n_qubits = 4
    j_coupling = 1.0  # ZZ interaction strength
    h_field = 0.5     # X field strength
    
    tfim = create_transverse_field_ising_model(n_qubits, j_coupling, h_field)
    print(f"TFIM Hamiltonian: {tfim}")
    
    # Group TFIM terms into commuting sets (important for Trotterization)
    tfim_commuting = tfim.commuting_groups()
    print(f"\nCommuting groups for TFIM: {len(tfim_commuting)}")
    for i, group in enumerate(tfim_commuting):
        print(f"  Group {i+1}: {group}")
    
    # This grouping reveals the natural decomposition for Trotterization:
    # - All ZZ terms commute with each other
    # - All X terms commute with each other
    # - ZZ terms don't commute with X terms
    
    # Prepare for Trotterization
    print("\n== Preparation for Trotterization ==")
    print("The Hamiltonian can be split into commuting groups:")
    
    # Calculate eigenvalues to validate implementation
    if n_qubits <= 4:  # Only for small systems
        print("\nEigenvalues of the Hamiltonian:")
        eigenvalues = np.linalg.eigvalsh(tfim.to_sparse_matrix(n_qubits).toarray())
        print(np.sort(eigenvalues)[:5], "...")  # Show first few eigenvalues
    
if __name__ == "__main__":
    main()