## Circuit Optimization

To run the circuit optimization, you need to specify the qasm file and the optimization method. The qasm file should be in the `./examples/circuit-optimization/qasm/` directory. The optimization method can be one of the following:
- `zx-qiskit`: This method uses ZX calculus to optimize the circuit.
- `qiskit-bloqade-parallel`: This method uses ZX calculus to optimize the circuit and then uses UOpToParallel to optimize the circuit.
- `zx-qiskit-bloqade-parallel`: This method uses UOpToParallel to optimize the circuit.

An example of running the optimization is as follows:
```
python ./examples/circuit-optimization/run_optimization.py --qasm_file ./examples/circuit-optimization/qasm/opt-qiskit.qasm --method zx-bloqade-parallel
```


### Results: Ising Model Simulation Circuit Rewriting Experiment

The cost metric:

| Gate Type       | Cost Weight |
| --------------- | ----------- |
| Local 1-qubit   | 0.2         |
| Local 2-qubit   | 0.4         |
| Global 1-qubit  | 0.1         |
| Global 2-qubit  | 0.4         |


To demonstrate the effectiveness of our flow, we conducted prototyping and experimentation on the algorithm. The cost is defined based on the number of local single-qubit gates, local two-qubit gates, parallel single-qubit gates, and parallel two-qubit gates. We assign a lower cost to the parallel single-qubit gate than to the local ones to encourage the tools to parallelize them. Results show that our flow utilizes more parallelism than directly parsing it through UOpToParallel. 


| Circuit                         | Score  |
| ------------------------------- | ------ |
| Init                            | 268.80 |
| Init + Qiskit                   | 76.80  |
| Init + Qiskit + UOpParallel     | 72.10  |
| Init + Qiskit + ZX              | 120.00 |
| Init + Qiskit + ZX + UOpParallel| 65.40  |

