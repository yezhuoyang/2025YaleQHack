import re

def convert_qasm_to_python(qasm_code: str, output_qasm_file: str) -> str:
    """
    Converts a subset of OpenQASM 2.0 code to a Python dialect.
    
    Supported instructions:
      - qreg declarations, e.g.: "qreg q[4];"
      - CX gates, e.g.: "cx q[0],q[1];"
      - U3 gates, e.g.: "u3(pi/2,0,pi) q[0];"
    """
    # Start with the header for the Python dialect code.
    output_lines = [
        "from bloqade import qasm2", 
        "from bloqade.qasm2.parse import ast", 
        "from bloqade.qasm2.passes import UOpToParallel, QASM2Fold", 
        "", 
        "from numpy import pi", 
        "@qasm2.extended",
        "def main():"
    ]
    
    # Process each line in the QASM code.
    for line in qasm_code.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip header lines.
        if line.startswith("OPENQASM") or line.startswith("include"):
            continue
        
        # Convert register declaration: "qreg q[4];" -> "q = qasm2.qreg(4)"
        m = re.match(r'qreg\s+(\w+)\[(\d+)\];', line)
        if m:
            var = m.group(1)
            num = m.group(2)
            output_lines.append(f"    {var} = qasm2.qreg({num})")
            continue
        
        # Convert CX gate: "cx q[0],q[1];" -> "qasm2.cx(q[0], q[1])"
        m = re.match(r'cx\s+q\[(\d+)\],\s*q\[(\d+)\];', line)
        if m:
            control = m.group(1)
            target = m.group(2)
            output_lines.append(f"    qasm2.cx(q[{control}], q[{target}])")
            continue
        
        # Convert U3 gate: "u3(theta,phi,lambda) q[0];" ->
        # "qasm2.u(q[0], theta, phi, lambda)"
        m = re.match(r'u3\(([^)]+)\)\s+q\[(\d+)\];', line)
        if m:
            args = m.group(1)
            index = m.group(2)
            # Split the arguments and remove extra spaces.
            arg_list = [arg.strip() for arg in args.split(',')]
            if len(arg_list) == 3:
                output_lines.append(
                    f"    qasm2.u(q[{index}], {arg_list[0]}, {arg_list[1]}, {arg_list[2]})"
                )
            continue

        # If the line does not match any of the above patterns, skip it.
    
    output_lines.extend([
        "UOpToParallel(dialects=main.dialects)(main)",
        "",
        "# emit",
        "from rich.console import Console",
        "target = qasm2.emit.QASM2(",
        "    allow_parallel=True,",
        "    allow_global=True,",
        ")",
        "ast = target.emit(main)",
        "qasm_str: str = qasm2.parse.spprint(ast, console=Console(no_color=True))",
        f"open('{output_qasm_file}', 'w').write(qasm_str)"
    ])
    return "\n".join(output_lines)

import os
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

def run_bloqade_parallelize(qasm_str: str):
    tmp_python_file = f"{CURR_DIR}/tmp_convert_qasm.py"
    tmp_qasm_file = f"{CURR_DIR}/tmp_convert_qasm.qasm"
    
    python_code = convert_qasm_to_python(qasm_str, tmp_qasm_file)
    open(tmp_python_file, "w").write(python_code)

    os.system(f"python {tmp_python_file}")
    output_qasm_str = open(tmp_qasm_file).read()
    
    os.remove(tmp_python_file)
    os.remove(tmp_qasm_file)
    return output_qasm_str