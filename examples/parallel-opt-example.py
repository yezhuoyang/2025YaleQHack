from bloqade import qasm2
from bloqade.qasm2.parse import ast
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold

@qasm2.extended
def main():
    # q1 = qasm2.qreg(1)
    # q2 = qasm2.qreg(2)

    # theta = 1.3
    # phi = 1.1
    # lam = 1.2

    # qasm2.glob.u(theta=theta, phi=phi, lam=lam, registers=[q1, q2])

    q = qasm2.qreg(4)

    # theta = 0.1
    # phi = 0.2
    # lam = 0.3

    # qasm2.u(q[1], theta, phi, lam)
    # qasm2.u(q[3], theta, phi, lam)
    # qasm2.cx(q[1], q[3])
    # qasm2.u(q[2], theta, phi, lam)
    # qasm2.u(q[0], theta, phi, lam)
    # qasm2.cx(q[0], q[2])
    qasm2.cx(q[0], q[1])
    qasm2.cx(q[0], q[1])


UOpToParallel(dialects=main.dialects)(main)

# emit
from rich.console import Console
target = qasm2.emit.QASM2(
    allow_parallel=False,
    allow_global=False,
)
ast = target.emit(main)
qasm2.parse.pprint(ast, console=Console(no_color=True))

"""
include "qelib1.inc";
qreg q2[2];
qreg q1[1];
parallel.U(1.3, 1.1, 1.2) {
    q1[0];
    q2[0]; // parallel
    q2[1]; // parallel
}
"""