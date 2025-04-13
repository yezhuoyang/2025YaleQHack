def count_qasm_gates_simple(qasm_str):
    """
    Count local/global 1-qubit and 2-qubit gates by checking the
    first few characters of each line.  Skips lines that start with
    'OPENQASM', 'include', 'qreg', or are empty.

    Assumes:
      - Lines for local single-qubit gates start with "h ", "x ", "y ", "z ",
        or "U(" (etc.).
      - Lines for local two-qubit gates start with "cz ", "cx ", "swap ", etc.
      - Lines for parallel single-qubit gates start with "parallel.U(" ...
      - Lines for parallel two-qubit gates start with "parallel.CZ", "parallel.CX", etc.

    This is a simple prefix-based approach.  It does not parse further
    to count multiple qubits in a single line, etc.  It simply treats
    each line as exactly one gate statement.
    """

    lines = [line.strip() for line in qasm_str.splitlines()]
    
    # We will store the counts in a small dictionary
    gate_counts = {
        'local_1q': 0,
        'local_2q': 0,
        'global_1q': 0,
        'global_2q': 0
    }

    for line in lines:
        if not line:  
            continue    # skip empty lines
        # skip lines that are obviously not gate instructions
        if (line.startswith("OPENQASM") or
            line.startswith("include") or
            line.startswith("qreg") or
            line.startswith("creg") or
            line.startswith("measure") or
            line.startswith("barrier") or
            line.startswith("//")):
            continue

        # Trim trailing semicolons if present
        if line.endswith(';'):
            line = line[:-1].strip()

        # --- LOCAL 1-QUBIT gates (by prefix) ---
        if (line.startswith("h ") or
            line.startswith("x ") or
            line.startswith("y ") or
            line.startswith("z ") or
            line.startswith("s ") or
            line.startswith("sdg ") or
            line.startswith("t ") or
            line.startswith("tdg ") or
            # or a U(...) form
            line.startswith("U(") or
            line.startswith("u(") or
            line.startswith("rx(") or
            line.startswith("ry(") or
            line.startswith("rz(")):
            gate_counts['local_1q'] += 1

        # --- LOCAL 2-QUBIT gates (by prefix) ---
        elif (line.startswith("cz ") or
              line.startswith("cx ") or
              line.startswith("cy ") or
              line.startswith("swap ")):
            gate_counts['local_2q'] += 1

        # --- GLOBAL (PARALLEL) 1-QUBIT ---
        elif line.startswith("parallel.U(") or line.startswith("parallel.u("):
            # If you truly need to parse how many qubits are inside braces,
            # that requires more code.  But if each "parallel" line is guaranteed
            # to be exactly one gate statement, just do:
            gate_counts['global_1q'] += 1

        # --- GLOBAL (PARALLEL) 2-QUBIT ---
        elif (line.startswith("parallel.CZ") or
              line.startswith("parallel.CX") or
              line.startswith("parallel.CY") or
              line.startswith("parallel.swap")):
            gate_counts['global_2q'] += 1

        else:
            # Anything else is unknown or not a gate
            pass

    return gate_counts




def score(qasm_str):
    """
    Score a QASM string based on the number of local/global 1-qubit and 2-qubit gates.
    The score is calculated as follows:
      - local_1q: +1 point
      - local_2q: +2 points
      - global_1q: +3 points
      - global_2q: +4 points

    Args:
        qasm_str (str): The QASM string to be scored.

    Returns:
        int: The total score based on the gate counts.
    """
    gate_counts = count_qasm_gates_simple(qasm_str)
    score = (gate_counts['local_1q'] * 0.2 +
             gate_counts['local_2q'] * 0.4 +
             gate_counts['global_1q'] * 0.1 +
             gate_counts['global_2q'] * 0.4)
    return score

import argparse
parser = argparse.ArgumentParser(description='Score a QASM string.')
parser.add_argument('qasm_file', type=str, help='Path to the QASM file to be scored.')
args = parser.parse_args()

if __name__ == "__main__":
    qasm_str: str = open(args.qasm_file).read()
    score_value = score(qasm_str)
    print(f"Score: {score_value:.2f}")