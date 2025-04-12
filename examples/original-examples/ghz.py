import math

from bloqade import qasm2
from kirin.dialects import ilist

def ghz_linear(n: int):
    n_qubits = int(2**n)

    @qasm2.extended
    def ghz_linear_program():

        qreg = qasm2.qreg(n_qubits)
        # Apply a Hadamard on the first qubit
        qasm2.h(qreg[0])
        # Create a cascading sequence of CX gates
        # necessary for quantum computers that
        # only have nearest-neighbor connectivity between qubits
        for i in range(1, n_qubits):
            qasm2.cx(qreg[i - 1], qreg[i])

    return ghz_linear_program

def ghz_log_depth(n: int):
    n_qubits = int(2**n)

    @qasm2.extended
    def layer_of_cx(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)
        for j in range(0, n_qubits, step):
            qasm2.cx(ctrl=qreg[j], qarg=qreg[j + step // 2])

    @qasm2.extended
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)

        qasm2.h(qreg[0])
        for i in range(n):
            layer_of_cx(i_layer=i, qreg=qreg)

    return ghz_log_depth_program

def ghz_log_simd(n: int):
    n_qubits = int(2**n)

    @qasm2.extended
    def layer(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)

        def get_qubit(x: int):
            return qreg[x]

        ctrl_qubits = ilist.Map(fn=get_qubit, collection=range(0, n_qubits, step))
        targ_qubits = ilist.Map(
            fn=get_qubit, collection=range(step // 2, n_qubits, step)
        )

        # Ry(-pi/2)
        qasm2.parallel.u(qargs=targ_qubits, theta=-math.pi / 2, phi=0.0, lam=0.0)

        # CZ gates
        qasm2.parallel.cz(ctrls=ctrl_qubits, qargs=targ_qubits)

        # Ry(pi/2)
        qasm2.parallel.u(qargs=targ_qubits, theta=math.pi / 2, phi=0.0, lam=0.0)

    @qasm2.extended
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)

        qasm2.h(qreg[0])
        for i in range(n):
            layer(i_layer=i, qreg=qreg)

    return ghz_log_depth_program

target = qasm2.emit.QASM2(
    allow_parallel=True,
)
ast = target.emit(ghz_log_simd(4))
qasm2.parse.pprint(ast)