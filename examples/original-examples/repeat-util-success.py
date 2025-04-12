from bloqade import qasm2
from bloqade.pyqrack import PyQrack  # noqa: E402

@qasm2.extended
def prep_resource_state(theta: float):
    qreg = qasm2.qreg(1)
    qubit = qreg[0]
    qasm2.h(qubit)
    qasm2.rz(qubit, theta)
    return qubit

@qasm2.extended
def z_phase_gate_postselect(target: qasm2.Qubit, theta: float) -> qasm2.Qubit:
    ancilla = prep_resource_state(theta)
    qasm2.cx(ancilla, target)
    creg = qasm2.creg(1)
    qasm2.measure(target, creg[0])
    if creg[0] == 1:
        qasm2.x(ancilla)
    return ancilla

@qasm2.extended
def z_phase_gate_recursive(target: qasm2.Qubit, theta: float) -> qasm2.Qubit:
    """
    https://journals.aps.org/prxquantum/pdf/10.1103/PRXQuantum.5.010337 Fig. 7
    """
    ancilla = prep_resource_state(theta)
    qasm2.cx(ancilla, target)
    creg = qasm2.creg(1)
    qasm2.measure(target, creg[0])
    if creg[0] == 0:
        return z_phase_gate_recursive(ancilla, 2 * theta)
    if creg[0] == 1:
        qasm2.x(ancilla)
    return ancilla

@qasm2.extended
def z_phase_gate_loop(target: qasm2.Qubit, theta: float, attempts: int):
    """
    https://journals.aps.org/prxquantum/pdf/10.1103/PRXQuantum.5.010337 Fig. 7
    """
    creg = qasm2.creg(1)  # Implicitly initialized to 0, thanks qasm...
    for ctr in range(attempts):
        ancilla = prep_resource_state(theta * (2**ctr))
        if creg[0] == 0:
            qasm2.cx(ancilla, target)
            qasm2.measure(target, creg[0])
            target = ancilla
    qasm2.x(target)
    
    
theta = 0.1  # Specify some Z rotation angle. Note that this is being defined

@qasm2.extended
def postselect_main():
    target = qasm2.qreg(1)
    z_phase_gate_postselect(target[0], theta)


@qasm2.extended
def recursion_main():
    target = qasm2.qreg(1)
    z_phase_gate_recursive(target[0], theta)


@qasm2.extended
def loop_main():
    target = qasm2.qreg(1)
    z_phase_gate_loop(target[0], theta, 5)
    
device = PyQrack()
qreg = device.run(postselect_main)
print(qreg)

from bloqade.qasm2.emit import QASM2  # noqa: E402
from bloqade.qasm2.parse import pprint  # noqa: E402

target = QASM2()
qasm_postselect = target.emit(postselect_main)
qasm_loop = target.emit(loop_main)

try:  # The recursion version has no qasm representation.
    qasm_recursive = target.emit(recursion_main)
except Exception:
    print("Whoops! We cannot emit calls with return value. This is expected.")

print("\n\n--- Postselect ---")
pprint(qasm_postselect)
print("\n\n--- Loop ---")
pprint(qasm_loop)

payload = target.emit_str(postselect_main)