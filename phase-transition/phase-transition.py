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

def phase_transition(n: int, time: int, steps: int, parallelize: bool = True):
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
    def phase_transition_program():
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

    return phase_transition_program

time_interval = 0.5
steps = 24
N = 2
mag_vals = [] 

for i in range(steps):
    kernel_PT = phase_transition(N, time_interval*i, i)
    
    device = PyQrack(dynamic_qubits=True, pyqrack_options={"isBinaryDecisionTree": False})
    results = device.multi_run(kernel_PT, _shots=100)
    
    def to_bitstrings(results):
        return Counter(map(lambda result:"".join(map(str, result)), results))
    
    counts = to_bitstrings(results)
    
    total_magnetization = 0
    
    for key, value in counts.items():
        spin_down = str(key).count('1')
        #print("Time " + str(time_interval*i) + ": " + str(key) + " " + str(value))
        total_magnetization += value*spin_down * (-1/2) + value*(2**N - spin_down) * (1/2)

    print("Time " + str(time_interval*i) + ": " + str(total_magnetization/100))
    mag_vals.append(total_magnetization/100) 

import matplotlib.pyplot as plt 
import numpy as np

t = np.linspace(0, 11.5, 24)
magnetization = np.array(mag_vals)
plt.plot(t, magnetization)