from bloqade import qasm2
from bloqade.qasm2.parse import ast
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold

@qasm2.extended
def main():
    q1 = qasm2.qreg(1)
    q2 = qasm2.qreg(2)

    theta = 1.3
    phi = 1.1
    lam = 1.2

    qasm2.glob.u(theta=theta, phi=phi, lam=lam, registers=[q1, q2])

UOpToParallel(dialects=main.dialects)(main)

# emit
target = qasm2.emit.QASM2(
    allow_parallel=True,
    allow_global=False,
)
ast = target.emit(main)
qasm2.parse.pprint(ast)

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