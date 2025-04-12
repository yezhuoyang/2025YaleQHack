import math

from bloqade import qasm2
from kirin.dialects import ilist
from pyqrack import QrackSimulator
from bloqade.pyqrack import PyQrack, reg
from bloqade.noise import native



from bloqade.qasm2.emit import QASM2 # the QASM2 target
from bloqade.qasm2.parse import pprint # the QASM2 pretty printer


@qasm2.extended
def xgate_program(qreg: qasm2.QReg, target: int):
    qasm2.x(qreg[target])
    return qreg


@qasm2.extended
def ygate_program(qreg: qasm2.QReg, target: int):
    qasm2.y(qreg[target])
    return qreg





@qasm2.extended
def compose_x_program(qreg: qasm2.QReg,typestr: str,targets: tuple[int, ...]):
    for i in range(len(targets)):
        if typestr[i] == "x":
            xgate_program(qreg,targets[i])
        elif typestr[i] == "y":
            ygate_program(qreg,targets[i])
    return qreg



@qasm2.extended
def add_cnot_qasm2(qindex1: int,qindex2: int,qreg: qasm2.QReg):
    qasm2.cx(qreg[qindex1], qreg[qindex2])        
    return qreg


@qasm2.extended
def add_hadamard_qasm2(qindex: int,qreg: qasm2.QReg):
    qasm2.h(qreg[qindex])
    return qreg    
      
      
@qasm2.extended
def add_measure_qasm2(qindex: int,mindex: int,creg:qasm2.CReg,qreg:qasm2.QReg):
    qasm2.measure(qreg[qindex],creg[mindex])
    return qreg
    


@qasm2.extended
def final_program():
    qreg = qasm2.qreg(10)
    compose_x_program(qreg=qreg, typestr="xxyy",targets=(0, 1, 2, 3))  
    



target = QASM2()
ast = target.emit(final_program)
pprint(ast)


