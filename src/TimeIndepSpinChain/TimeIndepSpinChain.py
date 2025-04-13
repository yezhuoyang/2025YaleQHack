from bloqade import qasm2
import numpy as np
from bloqade.pyqrack import PyQrack
from collections import Counter
from bloqade.qasm2.rewrite.native_gates import RydbergGateSetRewriteRule
from kirin import ir
from kirin.rewrite import Walk
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold

import warnings
warnings.filterwarnings("ignore")

@ir.dialect_group(qasm2.extended)
def extended_opt(self):
    native_rewrite = Walk(RydbergGateSetRewriteRule(self)) # use Kirin's functionality to walk code line by line while applying neutral-atom gate decomposition as defined in Bloqade
    parallelize_pass = UOpToParallel(self) # review the code and apply parallelization using a heuristic
    agg_fold = QASM2Fold(self) # supports parallelization by unfolding loops to search for parallelization opportunities

    # here we define our new compiler pass
    def run_pass(
        kernel: ir.Method,
        *,
        fold: bool = True,
        typeinfer: bool = True,
        parallelize: bool = False,
    ):
        assert qasm2.extended.run_pass is not None
        qasm2.extended.run_pass(kernel, fold=fold, typeinfer=typeinfer) # apply the original run_pass to the lowered kernel
        native_rewrite.rewrite(kernel.code) # decompose all gates in the circuit to neutral atom gate set

        # here goes our parallelization optimizer; the order of the commands here matters!
        if parallelize:
            agg_fold.fixpoint(kernel)
            parallelize_pass(kernel)

    return run_pass

def unopt(self):
    native_rewrite = Walk(RydbergGateSetRewriteRule(self)) # use Kirin's functionality to walk code line by line while applying neutral-atom gate decomposition as defined in Bloqade
    parallelize_pass = UOpToParallel(self) # review the code and apply parallelization using a heuristic
    agg_fold = QASM2Fold(self) # supports parallelization by unfolding loops to search for parallelization opportunities

    # here we define our new compiler pass
    def run_pass(
        kernel: ir.Method,
        *,
        fold: bool = False,
        typeinfer: bool = False,
        parallelize: bool = False,
    ):
        assert qasm2.extended.run_pass is not None
        qasm2.extended.run_pass(kernel, fold=fold, typeinfer=typeinfer) # apply the original run_pass to the lowered kernel
        native_rewrite.rewrite(kernel.code) # decompose all gates in the circuit to neutral atom gate set

        # here goes our parallelization optimizer; the order of the commands here matters!
        if parallelize:
            agg_fold.fixpoint(kernel)
            parallelize_pass(kernel)

    return run_pass


def SpinChainLieTrotter(n: int, time: int, steps: int, parallelize: bool = True):
    n_qubits = int(2**n)
    
    @extended_opt
    def trotter_layer(qreg: qasm2.QReg, timestep: int, J: int, h: int):
        for i in range(n_qubits):
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
            qasm2.rz(qreg[(i+1)%n_qubits], 2*J*timestep)
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
        for i in range(n_qubits):
            qasm2.rx(qreg[i], 2*h*timestep)

    @extended_opt(parallelize=parallelize)
    def SpinChainLieTrotter_program():
        if time == 0: 
            creg = qasm2.creg(n_qubits) 
            return creg
        
        qreg = qasm2.qreg(n_qubits)
        creg = qasm2.creg(n_qubits)

        J = 0.2 
        h = 1.2 
        timestep = time/steps 
        for i in range(steps): 
            trotter_layer(qreg, timestep, J, h)
        
        for i in range(n_qubits):
            qasm2.measure(qreg[i],creg[i])

        return creg

    return SpinChainLieTrotter_program

def SpinChainLieTrotterUnopt(n: int, time: int, steps: int):
    n_qubits = int(2**n)
    
    def trotter_layer(qreg: qasm2.QReg, timestep: int, J: int, h: int):
        for i in range(n_qubits):
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
            qasm2.rz(qreg[(i+1)%n_qubits], 2*J*timestep)
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
        for i in range(n_qubits):
            qasm2.rx(qreg[i], 2*h*timestep)

    def SpinChainLieTrotterUnopt_program():
        if time == 0: 
            creg = qasm2.creg(n_qubits) 
            return creg
        
        qreg = qasm2.qreg(n_qubits)
        creg = qasm2.creg(n_qubits)

        J = 0.2 
        h = 1.2 
        timestep = time/steps 
        for i in range(steps): 
            trotter_layer(qreg, timestep, J, h)
        
        for i in range(n_qubits):
            qasm2.measure(qreg[i],creg[i])

        return creg

    return SpinChainLieTrotterUnopt_program

def SpinChainLieTrotterParallel(n: int, time: int, steps: int, parallelize: bool = True):
    n_qubits = int(2**n)
    
    @extended_opt
    def trotter_layer(qreg: qasm2.QReg, timestep: int, J: int, h: int): #puts commuting ZZ in parallel
        for i in range(0,n_qubits, 2):
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
            qasm2.rz(qreg[(i+1)%n_qubits], 2*J*timestep)
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
        for i in range(1,n_qubits, 2):
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
            qasm2.rz(qreg[(i+1)%n_qubits], 2*J*timestep)
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
        for i in range(n_qubits):
            qasm2.rx(qreg[i], 2*h*timestep)

    @extended_opt(parallelize=parallelize)
    def SpinChainLieTrotterParallel_program():
        if time == 0: 
            creg = qasm2.creg(n_qubits) 
            return creg
        
        qreg = qasm2.qreg(n_qubits)
        creg = qasm2.creg(n_qubits)

        J = 0.2 
        h = 1.2 
        timestep = time/steps 
        for i in range(steps): 
            trotter_layer(qreg, timestep, J, h)
        
        for i in range(n_qubits):
            qasm2.measure(qreg[i],creg[i])

        return creg

    return SpinChainLieTrotterParallel_program



def SpinChainSuzukiTrotter(n: int, time: int, steps: int, parallelize: bool = True):
    n_qubits = int(2**n)
    
    @extended_opt
    def trotter_layer(qreg: qasm2.QReg, timestep: int, J: int, h: int):
        for i in range(n_qubits):
            qasm2.rx(qreg[i], h*timestep)
            qasm2.rx(qreg[i], h*timestep) # global pulse!
        for i in range(n_qubits):
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
            qasm2.rz(qreg[(i+1)%n_qubits], 2*J*timestep)
            qasm2.cx(qreg[i], qreg[(i+1)%n_qubits])
        for i in range(n_qubits):
            qasm2.rx(qreg[i], h*timestep)


    @extended_opt(parallelize=parallelize)
    def SpinChainSuzukiTrotter_program():
        if time == 0: 
            creg = qasm2.creg(n_qubits) 
            return creg
        
        qreg = qasm2.qreg(n_qubits)
        creg = qasm2.creg(n_qubits)

        J = 0.2 
        h = 1.2 
        timestep = time/steps 
        for i in range(steps): 
            trotter_layer(qreg, timestep, J, h)
        
        for i in range(n_qubits):
            qasm2.measure(qreg[i],creg[i])

        return creg

    return SpinChainSuzukiTrotter_program

from rich.console import Console
target = qasm2.emit.QASM2(allow_parallel=False, allow_global=False) 
ast = target.emit(SpinChainLieTrotter(2,12,24, parallelize=False)) 
qasm_str: str = qasm2.parse.spprint(ast, console=Console(no_color=True))
open("output.txt","w").write(qasm_str) # not fully functional