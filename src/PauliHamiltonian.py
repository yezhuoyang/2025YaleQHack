import numpy as np
import scipy.sparse as sparse
from typing import List, Dict, Tuple, Union, Optional
from enum import Enum


class PauliOp(Enum):
    """Enum representation of Pauli operators"""
    I = 0  # Identity
    X = 1  # Pauli X
    Y = 2  # Pauli Y
    Z = 3  # Pauli Z
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    @property
    def matrix(self):
        """Return the matrix representation of the Pauli operator"""
        if self == PauliOp.I:
            return np.array([[1, 0], [0, 1]], dtype=complex)
        elif self == PauliOp.X:
            return np.array([[0, 1], [1, 0]], dtype=complex)
        elif self == PauliOp.Y:
            return np.array([[0, -1j], [1j, 0]], dtype=complex)
        else:  # PauliOp.Z
            return np.array([[1, 0], [0, -1]], dtype=complex)
    
    @property
    def sparse_matrix(self):
        """Return the sparse matrix representation of the Pauli operator"""
        return sparse.csr_matrix(self.matrix)


class PauliTerm:
    """
    Class representing a term in a Pauli Hamiltonian: coefficient * P_1 ⊗ P_2 ⊗ ... ⊗ P_n
    where P_i are Pauli operators (I, X, Y, Z)
    """
    
    def __init__(self, coefficient: complex, operators: Dict[int, PauliOp]):
        """
        Initialize a Pauli term.
        
        Args:
            coefficient: Complex coefficient for the term
            operators: Dictionary mapping qubit indices to Pauli operators
        """
        self.coefficient = coefficient
        self.operators = operators
        
    def __str__(self):
        if not self.operators:
            return f"{self.coefficient}*I"
        
        term_str = f"{self.coefficient}*"
        sorted_qubits = sorted(self.operators.keys())
        
        ops = []
        for q in sorted_qubits:
            ops.append(f"{self.operators[q].name}_{q}")
            
        term_str += " ".join(ops)
        return term_str
    
    def __repr__(self):
        return self.__str__()
    
    def to_matrix(self, n_qubits: int) -> np.ndarray:
        """Convert the Pauli term to a matrix representation."""
        # Start with identity
        result = np.array([[1]], dtype=complex)
        
        for i in range(n_qubits):
            if i in self.operators:
                pauli = self.operators[i].matrix
            else:
                pauli = PauliOp.I.matrix
                
            result = np.kron(result, pauli)
                
        return self.coefficient * result
    
    def to_sparse_matrix(self, n_qubits: int) -> sparse.csr_matrix:
        """Convert the Pauli term to a sparse matrix representation."""
        # Define the basic Pauli matrices
        I = PauliOp.I.sparse_matrix
        X = PauliOp.X.sparse_matrix
        Y = PauliOp.Y.sparse_matrix
        Z = PauliOp.Z.sparse_matrix
        
        pauli_matrices = {
            PauliOp.I: I,
            PauliOp.X: X,
            PauliOp.Y: Y,
            PauliOp.Z: Z
        }
        
        # Start with identity for all qubits
        result = 1
        
        # Build the tensor product
        for i in range(n_qubits):
            if i in self.operators:
                pauli = pauli_matrices[self.operators[i]]
            else:
                pauli = I
                
            if i == 0:
                result = pauli
            else:
                result = sparse.kron(result, pauli, format='csr')
                
        return self.coefficient * result
    
    def get_qubits(self) -> List[int]:
        """Get the list of qubits this term operates on."""
        return list(self.operators.keys())
    
    def commutes_with(self, other: 'PauliTerm') -> bool:
        """Check if this Pauli term commutes with another term."""
        # Two Pauli terms commute if they have an even number of positions
        # where they differ and neither is the identity
        count_anticommuting_positions = 0
        
        # Check all positions where both terms have operators
        common_qubits = set(self.operators.keys()) & set(other.operators.keys())
        
        for qubit in common_qubits:
            op1 = self.operators[qubit]
            op2 = other.operators[qubit]
            
            # Identity commutes with everything
            if op1 == PauliOp.I or op2 == PauliOp.I:
                continue
                
            # Check if these operators anticommute
            # X, Y, Z all anticommute with each other
            if op1 != op2:
                count_anticommuting_positions += 1
                
        # If the number of anticommuting positions is even, the terms commute
        return count_anticommuting_positions % 2 == 0


class PauliHamiltonian:
    """Class representing a Hamiltonian as a sum of Pauli terms."""
    
    def __init__(self, terms: Optional[List[PauliTerm]] = None):
        """
        Initialize a Pauli Hamiltonian.
        
        Args:
            terms: List of PauliTerm objects
        """
        self.terms = terms or []
        
    def add_term(self, term: PauliTerm):
        """Add a term to the Hamiltonian."""
        self.terms.append(term)
        return self
    
    def __str__(self):
        if not self.terms:
            return "0"
        
        return " + ".join(str(term) for term in self.terms)
    
    def __repr__(self):
        return self.__str__()
    
    def to_sparse_matrix(self, n_qubits: int = None) -> sparse.csr_matrix:
        """Convert the Hamiltonian to a sparse matrix representation."""
        if n_qubits is None:
            n_qubits = self.get_n_qubits()

        if not self.terms:
            dim = 2**n_qubits
            return sparse.csr_matrix((dim, dim), dtype=complex)
        
        result = self.terms[0].to_sparse_matrix(n_qubits)
        
        for term in self.terms[1:]:
            result += term.to_sparse_matrix(n_qubits)
            
        return result
    
    def to_matrix(self, n_qubits: int = None) -> sparse.csr_matrix:
        """Convert the Hamiltonian to a sparse matrix representation."""
        if n_qubits is None:
            n_qubits = self.get_n_qubits()
            
        # Convert the Hamiltonian to a sparse matrix first
        sparse_matrix = self.to_sparse_matrix(n_qubits)
    
        # Convert to dense matrix
        return sparse_matrix.toarray()
    
    def get_all_qubits(self) -> List[int]:
        """Get a sorted list of all qubits this Hamiltonian operates on."""
        qubits = set()
        for term in self.terms:
            qubits.update(term.get_qubits())
        return sorted(list(qubits))
    
    def get_n_qubits(self) -> int:
        """Get the number of qubits in the system based on highest qubit index."""
        if not self.terms:
            return 0
        
        all_qubits = self.get_all_qubits()
        if not all_qubits:
            return 0
        
        return max(all_qubits) + 1
    
    def group_terms_by_type(self) -> Dict[str, 'PauliHamiltonian']:
        """
        Group Hamiltonian terms by their Pauli type.
        
        Returns:
            Dictionary mapping term types ('X', 'Y', 'Z', 'mixed') to sub-Hamiltonians
        """
        grouped = {
            'X': PauliHamiltonian(),
            'Y': PauliHamiltonian(),
            'Z': PauliHamiltonian(),
            'mixed': PauliHamiltonian()
        }
        
        for term in self.terms:
            # Skip terms with coefficient 0
            if abs(term.coefficient) < 1e-10:
                continue
                
            # Check if this term has operators of only one type
            op_types = set(op for op in term.operators.values())
            
            if len(op_types) == 1:
                op_type = next(iter(op_types))
                if op_type == PauliOp.X:
                    grouped['X'].add_term(term)
                elif op_type == PauliOp.Y:
                    grouped['Y'].add_term(term)
                elif op_type == PauliOp.Z:
                    grouped['Z'].add_term(term)
                else:  # Identity terms
                    # Add identity terms to all groups since they commute with everything
                    for group in grouped.values():
                        group.add_term(term)
            else:
                # Mixed term
                grouped['mixed'].add_term(term)
                
        return grouped
    
    # Add this method to the PauliHamiltonian class in PauliHamiltonian.py

    def simplify(self):
        """
        Simplify the Hamiltonian by combining like terms and removing negligible terms.
        
        Returns:
            A new simplified PauliHamiltonian object
        """
        # Create a dictionary to group terms by their operators
        grouped_terms = {}
        
        for term in self.terms:
            # Create a unique key for each term based on its operators
            key_parts = []
            
            # Sort by qubit index for consistent ordering
            for qubit in sorted(term.operators.keys()):
                op = term.operators[qubit]
                key_parts.append(f"{op.name}_{qubit}")
            
            # Create the key - empty string means identity operator
            key = " ".join(key_parts) if key_parts else "I"
            
            # Add coefficient to the appropriate group
            if key in grouped_terms:
                grouped_terms[key] += term.coefficient
            else:
                grouped_terms[key] = term.coefficient
        
        # Create new PauliHamiltonian with simplified terms
        simplified = PauliHamiltonian()
        
        for key, coefficient in grouped_terms.items():
            # Skip terms with near-zero coefficients
            if abs(coefficient) < 1e-10:
                continue
            
            # Parse the key to reconstruct operators dictionary
            operators = {}
            
            # Handle the identity case
            if key == "I":
                term = PauliTerm(coefficient, {})
            else:
                # Split the key into operator_qubit pairs
                parts = key.split()
                for part in parts:
                    op_name, qubit_str = part.split('_')
                    qubit = int(qubit_str)
                    
                    # Map the name back to a PauliOp
                    if op_name == "X":
                        op = PauliOp.X
                    elif op_name == "Y":
                        op = PauliOp.Y
                    elif op_name == "Z":
                        op = PauliOp.Z
                    else:  # Identity
                        op = PauliOp.I
                    
                    operators[qubit] = op
                
                term = PauliTerm(coefficient, operators)
            
            # Add the simplified term to the new Hamiltonian
            simplified.add_term(term)
        
        return simplified
    
    def commuting_groups(self) -> List['PauliHamiltonian']:
        """
        Group the Hamiltonian terms into sets of mutually commuting terms.
        
        Returns:
            List of PauliHamiltonian objects, each containing mutually commuting terms
        """
        if not self.terms:
            return []
            
        # Start with each term in its own group
        groups = []
        for term in self.terms:
            groups.append(PauliHamiltonian([term]))
            
        # Try to merge groups
        i = 0
        while i < len(groups):
            j = i + 1
            while j < len(groups):
                # Check if all terms in group i commute with all terms in group j
                all_commute = True
                
                for term_i in groups[i].terms:
                    for term_j in groups[j].terms:
                        if not term_i.commutes_with(term_j):
                            all_commute = False
                            break
                    if not all_commute:
                        break
                        
                if all_commute:
                    # Merge group j into group i
                    groups[i].terms.extend(groups[j].terms)
                    groups.pop(j)
                else:
                    j += 1
                    
            i += 1
            
        return groups

# Helper functions to create common Hamiltonians
def create_transverse_field_ising_model(n_qubits: int, 
                                       j_coupling: float = 1.0, 
                                       h_field: float = 1.0) -> PauliHamiltonian:
    """
    Create a transverse field Ising model Hamiltonian:
    H = -J ∑ Z_i Z_{i+1} - h ∑ X_i
    
    Args:
        n_qubits: Number of qubits
        j_coupling: Coupling strength (J)
        h_field: Transverse field strength (h)
        
    Returns:
        PauliHamiltonian representing the TFIM
    """
    ham = PauliHamiltonian()
    
    # Add ZZ interaction terms
    for i in range(n_qubits - 1):
        term = PauliTerm(-j_coupling, {i: PauliOp.Z, i+1: PauliOp.Z})
        ham.add_term(term)
    
    # Add transverse field (X) terms
    for i in range(n_qubits):
        term = PauliTerm(-h_field, {i: PauliOp.X})
        ham.add_term(term)
        
    return ham


def create_heisenberg_xyz_model(n_qubits: int, 
                              jx: float = 1.0, 
                              jy: float = 1.0, 
                              jz: float = 1.0) -> PauliHamiltonian:
    """
    Create a Heisenberg XYZ model Hamiltonian:
    H = ∑ (Jx X_i X_{i+1} + Jy Y_i Y_{i+1} + Jz Z_i Z_{i+1})
    
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


def create_xxx_model(n_qubits: int, j: float = 1.0) -> PauliHamiltonian:
    """
    Create an XXX model Hamiltonian (Heisenberg model with isotropic coupling):
    H = J ∑ (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1})
    
    Args:
        n_qubits: Number of qubits
        j: Coupling strength
        
    Returns:
        PauliHamiltonian representing the XXX model
    """
    return create_heisenberg_xyz_model(n_qubits, j, j, j)


# Example usage
if __name__ == "__main__":
    # Create a simple Hamiltonian
    h = PauliHamiltonian()
    
    # Add some terms
    h.add_term(PauliTerm(1.0, {0: PauliOp.X}))
    h.add_term(PauliTerm(0.5, {1: PauliOp.Z}))
    h.add_term(PauliTerm(0.25, {0: PauliOp.Z, 1: PauliOp.Z}))
    
    print("Simple Hamiltonian:")
    print(h)
    
    # Create a TFIM
    n_qubits = 4
    tfim = create_transverse_field_ising_model(n_qubits, 1.0, 0.5)
    
    print("\nTransverse Field Ising Model:")
    print(tfim)
    
    # Group terms
    grouped = tfim.group_terms_by_type()
    
    print("\nGrouped terms:")
    for term_type, subham in grouped.items():
        print(f"{term_type}: {subham}")
    
    # Find commuting groups
    commuting = tfim.commuting_groups()
    
    print("\nCommuting groups:")
    for i, group in enumerate(commuting):
        print(f"Group {i+1}: {group}")
