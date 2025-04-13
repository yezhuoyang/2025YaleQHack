from bloqade import qasm2
from bloqade.qasm2.parse import ast
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold

from numpy import pi

@qasm2.extended
def main():
    q = qasm2.qreg(3)
    qasm2.rz(q[0], pi/3)
    qasm2.rz(q[2], pi/3)
    qasm2.cx(q[0], q[1])
    qasm2.rz(q[1], pi/3)
    
    # qasm2.u(q[0], pi/2, 0, pi)
    # qasm2.u(q[1], pi/2, 0, -pi)
    # qasm2.u(q[2], pi/2, 0, pi)
    # qasm2.cx(q[0], q[1])




UOpToParallel(dialects=main.dialects)(main)

# emit
from rich.console import Console
target = qasm2.emit.QASM2(
    allow_parallel=True,
    allow_global=True,
)
ast = target.emit(main)
qasm_str: str = qasm2.parse.spprint(ast, console=Console(no_color=True))
open("test.qasm", "w").write(qasm_str)