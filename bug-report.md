
In `schema.py`:
```python
    # Add this function to dump the noise model (so that we can load it later)
    # will be called in QuEraSimulationResult to_json
    # will be loaded in `noise_model = NoiseModel(**json["noise_model"])`
    def model_dump(self, mode: str = "json"):
        """Dump the noise model for later reloading.

        Args:
            mode (str): The output format. "json" returns a JSON string,
                        "dict" returns a dictionary. Default is "json".

        Returns:
            Union[str, dict]: The dumped noise model data.
        """
        data = self.dict()
        if mode == "json":
            return data
        else:
            raise ValueError("Unsupported mode. Please choose 'json' or 'dict'.")
```





The following program will force the compiler into an infinite loop:



'''python
@qasm2.extended
def add_X_syndrome_circuit_recursive(result:int,round:int,qreg: qasm2.QReg,creg:qasm2.CReg,ndataqubits:int,stabindex:int,index_tuple:tuple[int, ...]):
    if round==3:
        return
    
    qasm2.h(qreg[ndataqubits+stabindex])
    for i in range(len(index_tuple)):
        qasm2.cx(qreg[ndataqubits+stabindex],qreg[index_tuple[i]])
    qasm2.h(qreg[ndataqubits+stabindex])
    qasm2.measure(qreg[ndataqubits+stabindex],creg[stabindex])


    if creg[stabindex]==result:
        return add_X_syndrome_circuit_recursive(result,round+1,qreg,creg,ndataqubits,stabindex,index_tuple)
       
    qasm2.reset(qreg[ndataqubits+stabindex]) 
    return add_X_syndrome_circuit_recursive(1-result,1,qreg,creg,ndataqubits,stabindex,index_tuple)


@qasm2.extended
def add_Z_syndrome_circuit_recursive(result:int,round:int,qreg: qasm2.QReg,creg:qasm2.CReg,ndataqubits:int,stabindex:int,index_tuple:tuple[int, ...]):
    if round==3:
        return
    
    for i in range(len(index_tuple)):
        qasm2.cx(qreg[index_tuple[i]],qreg[ndataqubits+stabindex])
    qasm2.measure(qreg[ndataqubits+stabindex],creg[stabindex])
    
    if creg[stabindex]==result:
        return add_Z_syndrome_circuit_recursive(result,round+1,qreg,creg,ndataqubits,stabindex,index_tuple)
   
    qasm2.reset(qreg[ndataqubits+stabindex]) 
    return add_Z_syndrome_circuit_recursive(1-result,1,qreg,creg,ndataqubits,stabindex,index_tuple)

@qasm2.extended
def surface_code_d2_circuit_recursive():
    qreg = qasm2.qreg(2*3**2-1)
    creg = qasm2.creg(3**2-1)
    add_X_syndrome_circuit_recursive(0,0,qreg,creg,9,0,(1,2,4,5))
    add_X_syndrome_circuit_recursive(0,0,qreg,creg,9,1,(4,5,7,8))
    
    add_X_syndrome_circuit_recursive(0,0,qreg,creg,9,2,(2,3))    
    add_X_syndrome_circuit_recursive(qreg,creg,9,3,(8,9))    
    
    add_Z_syndrome_circuit_recursive(0,0,qreg,creg,9,4,(2,3,5,6))
    add_Z_syndrome_circuit_recursive(0,0,qreg,creg,9,5,(5,6,8,9))
    
    
    add_Z_syndrome_circuit_recursive(0,0,qreg,creg,9,6,(1,4))    
    add_Z_syndrome_circuit_recursive(0,0,qreg,creg,9,7,(3,6))       
```

