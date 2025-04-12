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


from bloqade.qasm2.emit import QASM2 # the QASM2 target
from bloqade.qasm2.parse import pprint # the QASM2 pretty printer


'''
target = QASM2()
ast = target.emit(ghz_linear(2))
pprint(ast)
'''



def ghz_log_depth(n: int):
    n_qubits = int(2**n)

    @qasm2.extended
    def layer_of_cx(i_layer: int, qreg: qasm2.QReg):
        # count layer and deploy CNOT gates accordingly
        step = n_qubits // (2**i_layer)
        for j in range(0, n_qubits, step):
            qasm2.cx(ctrl=qreg[j], qarg=qreg[j + step // 2])

    @qasm2.extended
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)
        # add starting Hadamard and build layers
        qasm2.h(qreg[0])
        for i in range(n):
            layer_of_cx(i_layer=i, qreg=qreg)

    return ghz_log_depth_program


'''
target = QASM2()
ast = target.emit(ghz_log_depth(2))
pprint(ast)
'''


def ghz_log_simd(n: int):
    n_qubits = int(2**n)

    @qasm2.extended
    def layer(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)

        def get_qubit(x: int):
            return qreg[x]

        ctrl_qubits = ilist.map(fn=get_qubit, collection=range(0, n_qubits, step))
        targ_qubits = ilist.map(
            fn=get_qubit, collection=ilist.range(step // 2, n_qubits, step)
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

        qasm2.u3(qarg=qreg[0], theta=math.pi / 2, phi=0.0, lam=math.pi)
        for i in range(n):
            layer(i_layer=i, qreg=qreg)

    return ghz_log_depth_program

'''
target = QASM2()
ast = target.emit(ghz_log_simd(2))
pprint(ast)
'''

'''
target = QASM2( allow_parallel=True)
ast = target.emit(ghz_log_simd(2))
pprint(ast)
'''


from bloqade.qasm2.rewrite.native_gates import RydbergGateSetRewriteRule
from kirin import ir
from kirin.rewrite import Walk
from bloqade.qasm2.passes import UOpToParallel, QASM2Fold


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


def ghz_log_depth_2(n: int, parallelize: bool = True):
    n_qubits = int(2**n)

    @extended_opt
    def layer_of_cx(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)
        for j in range(0, n_qubits, step):
            qasm2.cx(ctrl=qreg[j], qarg=qreg[j + step // 2])


    @extended_opt(parallelize=parallelize)
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)

        qasm2.h(qreg[0])
        for i in range(n):
            layer_of_cx(i_layer=i, qreg=qreg)

    return ghz_log_depth_program

'''
target = qasm2.emit.QASM2(
    allow_parallel=True,
)
ast = target.emit(ghz_log_depth_2(2, parallelize=True))
qasm2.parse.pprint(ast)
'''


def ghz_log_depth_3(n: int):
    n_qubits = int(2**n)

    @extended_opt
    def layer_of_cx(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)
        for j in range(0, n_qubits, step):
            qasm2.cx(ctrl=qreg[j], qarg=qreg[j + step // 2])
            qasm2.barrier((qreg[j], qreg[j + step // 2]))


    @extended_opt(parallelize=True)
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)

        qasm2.h(qreg[0])
        for i in range(n):
            layer_of_cx(i_layer=i, qreg=qreg)

    return ghz_log_depth_program


'''
target = qasm2.emit.QASM2(
    allow_parallel=True,
)
ast = target.emit(ghz_log_depth_3(2))
qasm2.parse.pprint(ast)
'''


def ghz_log_depth(n: int, parallelize: bool = True):
    n_qubits = int(2**n)

    @extended_opt
    def layer_of_cx(i_layer: int, qreg: qasm2.QReg):
        step = n_qubits // (2**i_layer)
        for j in range(0, n_qubits, step):
            qasm2.cx(ctrl=qreg[j], qarg=qreg[j + step // 2])
            qasm2.barrier((qreg[j], qreg[j + step // 2]))


    @extended_opt(parallelize=parallelize)
    def ghz_log_depth_program():

        qreg = qasm2.qreg(n_qubits)
        creg = qasm2.creg(n_qubits)

        qasm2.h(qreg[0])
        for i in range(n):
            layer_of_cx(i_layer=i, qreg=qreg)
            
        for i in range(n_qubits):
            qasm2.measure(qreg[i],creg[i])
            
        return creg # return register for simulation

    return ghz_log_depth_program


kernel = ghz_log_depth(2, parallelize=False)


from bloqade.pyqrack import PyQrack
from collections import Counter



def to_bitstrings(results):
    return Counter(map(lambda result:"".join(map(str, result)), results))


'''
device = PyQrack(dynamic_qubits=True, pyqrack_options={"isBinaryDecisionTree": False})
results = device.multi_run(kernel, _shots=100)

counts = to_bitstrings(results)

for key, value in counts.items():
    print(key, value)
'''
    
    
    
from bloqade.qasm2.passes import NoisePass
from bloqade.noise import native

# add noise
noise_kernel = kernel.similar()
extended_opt.run_pass(noise_kernel, parallelize=True)
NoisePass(extended_opt)(noise_kernel)

noise_kernel = noise_kernel.similar(extended_opt.add(native))

device = PyQrack(dynamic_qubits=True, pyqrack_options={"isBinaryDecisionTree": False})
results = device.multi_run(noise_kernel, _shots=100)


counts = to_bitstrings(results)

for key, value in counts.items():
    print(key, value)