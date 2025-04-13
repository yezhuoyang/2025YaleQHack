
from bloqade import qasm2
from kirin.dialects import ilist
from pyqrack import QrackSimulator
from bloqade.pyqrack import PyQrack, reg
from bloqade.noise import native



from bloqade.qasm2.emit import QASM2 # the QASM2 target
from bloqade.qasm2.parse import pprint # the QASM2 pretty printer


from collections import Counter


def to_bitstrings(results):
    return Counter(map(lambda result:"".join(map(str, result)), results))


@qasm2.extended
def repetition_code():
    
    qreg = qasm2.qreg(5)
    creg = qasm2.creg(5)

    qasm2.cx(qreg[0], qreg[3])
    qasm2.cx(qreg[1], qreg[3])
    qasm2.cx(qreg[1], qreg[4])
    qasm2.cx(qreg[2], qreg[4])
    
    qasm2.measure(qreg[0], creg[0])
    qasm2.measure(qreg[1], creg[1])
    qasm2.measure(qreg[2], creg[2])
    qasm2.measure(qreg[3], creg[3])
    qasm2.measure(qreg[4], creg[4])
    
    if creg[3] == 0 and creg[4] == 1:
        qasm2.x(qreg[2])    
    
    if creg[3] == 1 and creg[4] == 1:
        qasm2.x(qreg[1])
        
    if creg[3] == 1 and creg[4] == 0:
        qasm2.x(qreg[0])    
        
    return creg





device = PyQrack(dynamic_qubits=True, pyqrack_options={"isBinaryDecisionTree": False})
results = device.multi_run(repetition_code, _shots=100)

counts = to_bitstrings(results)

for key, value in counts.items():
    print(key, value)



