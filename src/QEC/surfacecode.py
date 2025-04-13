from qiskit import QuantumCircuit
from typing import List
import numpy as np
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

class stabalizer:
    
    '''
    The stabilzier is a list of typle.
    For example:
          stab=[('X',1),('X',2),('Z',5),('Z',6)] 
          means the stabilizer is X1-X2-Z5-Z6
    '''
    def __init__(self,stab:List[tuple])->None:
        self.__stab=stab


    def __str__(self) -> str:
        strresult=""
        index=0
        for (stype,qubit) in self.__stab:
            strresult=strresult+stype+str(qubit)
            if index<len(self.__stab)-1:
                strresult=strresult+"-"
            index=index+1
        return strresult
    
    
    def get_stab(self)->List[tuple]:
        return self.__stab




class surfaceCode:
    
    
    '''
    Initialize a d*d surface code
    '''
    def __init__(self,distance:int) -> None:
        self._distance=distance
        '''
        A standard surface code has 2*distance**2-1 qubits and distance**2-1 stabilizers
        Following is the dataqubit of a 4*4 surface code                                                                                    
                                    Q1----Q2----Q3----Q4
                                    |    |     |     |
                                    |    |     |     | 
                                    Q5----Q6----Q7----Q8
                                    |    |     |     |
                                    |    |     |     | 
                                    Q9---Q10---Q11---Q12
                                    |    |     |     | 
                                    |    |     |     |
                                    Q13--Q14---Q15---Q16   
        We use the standard coordinate system to represent the qubits.
        Q1: (0,0), Q2: (0,1), Q3: (0,2), Q4: (0,3)                      
        Q5: (1,0), Q6: (1,1), Q7: (1,2), Q8: (1,3)
        Q9: (2,0), Q10:(2,1), Q11:(2,2), Q12:(2,3)
        Q13:(3,0), Q14:(3,1), Q15:(3,2), Q16:(3,3)                                     
        '''
        self._circuit=QuantumCircuit(2*distance**2-1,distance**2-1)
        self._ndataqubits=distance**2
        self._nstab=distance**2-1
        self._nXstab=0
        self._nZstab=0
        self._stab=[]
        self._error={}
        self.calc_stab()
        self._Hmatrix=np.zeros((self._nstab, 2*self._ndataqubits),dtype=int)
        self.calculate_H_matrix()
        
    def get_xy(self,qubit:int)->tuple:
        return qubit//self.__distance,qubit%self.__distance
        
        
    def draw_surface(self)->None:
        resultstr=""
        for line in range(self._distance):
            linestr=""
            for column in range(self._distance):
                index=line*self._distance+column+1
                if(column<self._distance-1):
                    if(len(str(index))==1):
                        linestr=linestr+"Q"+str(index)+"----"
                    if(len(str(index))==2):
                        linestr=linestr+"Q"+str(index)+"---"
                else:
                    linestr=linestr+"Q"+str(index)

            if line<self._distance-1:
                linestr=linestr+"\n"
                for column in range(self._distance-1):
                    linestr=linestr+"|     "
                linestr=linestr+"|\n"
                for column in range(self._distance-1):
                    linestr=linestr+"|     "
                linestr=linestr+"|\n"       
            resultstr=resultstr+linestr
        print(resultstr)     
        
    '''
    Calculate the satbilizer
    Each stabilizer is stored in a list.
    For example, S1=[1,2,5,6]
    '''    
    def calc_stab(self):
        '''
        Add X stabilizers in side the boundary
                        Qa------Qa+1
                        |       |
                        |       |
                        Qa+d----Qa+d+1
        line 0: Q1-Q2-Q3-...-Qd
        line 1: Qd+1-Q6-Q7-Q8-...-Q2d
        ...
        line k: Qkd+1-Qkd+2-...-Q(k+1)d
                        
        '''
        d=self._distance
        currentLine=0
        lefttopIndex=1
        while currentLine<d  and lefttopIndex+d+1<=d**2:
            self._stab.append(stabalizer([('X',lefttopIndex),('X',lefttopIndex+1),('X',lefttopIndex+d),('X',lefttopIndex+d+1)]))
            self._nXstab+=1
            if lefttopIndex+2 < (currentLine+1)*d:
                lefttopIndex=lefttopIndex+2
            else:
                currentLine=currentLine+1
                lefttopIndex=lefttopIndex+3
    
        '''
        Add X stabilizers that attached to the top and bottom boundary(Tough boundary)
        '''        
        leftindex=2
        while leftindex+1<=d:
            self._stab.append(stabalizer([('X',leftindex),('X',leftindex+1)]))
            self._nXstab+=1
            leftindex+=2
        leftindex=d*(d-1)+2
        while leftindex+1<=d**2:
            self._stab.append(stabalizer([('X',leftindex),('X',leftindex+1)]))
            self._nXstab+=1
            leftindex+=2
                            
        '''
        Add Z stabilizers inside the boundary
        '''
        currentLine=0
        lefttopIndex=2
        while currentLine<d  and lefttopIndex+d+1<=d**2:
            self._stab.append(stabalizer([('Z',lefttopIndex),('Z',lefttopIndex+1),('Z',lefttopIndex+d),('Z',lefttopIndex+d+1)]))
            self._nZstab+=1
            if lefttopIndex+2 < (currentLine+1)*d:
                lefttopIndex=lefttopIndex+2
            else:
                currentLine=currentLine+1
                lefttopIndex=lefttopIndex+3       

        '''
        Add Z stabilizers that attached to the left and right boundary(Soft boundary)
        '''          
        topindex=1     
        while topindex+d<=(d-1)*d+1:
            self._stab.append(stabalizer([('Z',topindex),('Z',topindex+d)]))
            self._nZstab+=1
            topindex=topindex+2*d
        topindex=d
        while topindex+d<=d**2:
            self._stab.append(stabalizer([('Z',topindex),('Z',topindex+d)]))
            self._nZstab+=1
            topindex=topindex+2*d


    def get_stab_by_index(self,index:int)->stabalizer:
        return self._stab[index]
    
    
    def print_stab(self):
        for s in self._stab:
            print(s)
    

    
    def compile_syndrome_circuit(self):
        synindex=0
        for stab in self._stab:
            tmpstab=stab.get_stab()
            if tmpstab[0][0]=='X':
                self._circuit.h(self._ndataqubits+synindex)
                for (typestr,qubit) in tmpstab:
                        self._circuit.cx(self._ndataqubits+synindex,qubit)
                
                self._circuit.h(self._ndataqubits+synindex)
            else:
                
                for (typestr,qubit) in tmpstab:
                        self._circuit.cx(qubit,self._ndataqubits+synindex)                     
            '''
            Measure the syndrome qubit
            ''' 
            self._circuit.measure(self._ndataqubits+synindex,synindex)
            synindex+=1 
        
        
    '''
    Inject error to the data qubit of the surface code
    Error is a dictionary, the key is the qubit index, the value is the error type
    For example, error={1:'X',2:'Z',3:'Y'} means qubit 1 has X error, qubit 2 has Z error, qubit 3 has Y error
    '''
    def inject_error(self,error:dict):
        self._error=error
        for qubit in error:
            if error[qubit]=='X':
                self._circuit.x(qubit)
            if error[qubit]=='Z':
                self._circuit.z(qubit)
            if error[qubit]=='Y':
                self._circuit.y(qubit)
    
             
        
        
    def get_circuit(self)->QuantumCircuit:
        return self._circuit
        
        
        
    '''
    Surface code is a CSS code, which means it has X and Z stabilizers.
    We can calculate the check matrix H
    For example, a code with stabilizers: S1=Z1Z2, S2=Z2Z3, S3=X1X2, S4=X2X3 has the following check matrix:
                                Z1  Z2  Z3  X1  X2  X3                                       
                            S1  1   1   0   0   0   0 
                        H=  S2  0   1   1   0   0   0   
                            S3  0   0   0   1   1   0 
                            S4  0   0   0   0   1   1 
                        
    '''                     
    
    def calculate_H_matrix(self):
        stabindex=0
        for stab in self._stab:
            tmpstab=stab.get_stab()
            for (typestr,qubit) in tmpstab:
                if typestr=='Z':
                    self._Hmatrix[stabindex][qubit-1]=1
                else:
                    self._Hmatrix[stabindex][self._ndataqubits+qubit-1]=1
            stabindex+=1
    
    
        
    def get_check_matrix(self)->np.array:
        return self._Hmatrix
    

    def run_simulation(self,shots:int)->dict:
        backend = AerSimulator()
        job = backend.run(self._circuit, shots=shots)
        output = job.result().get_counts() 
        return output
    
    

from bloqade import qasm2
from kirin.dialects import ilist
from pyqrack import QrackSimulator
from bloqade.pyqrack import PyQrack, reg
from bloqade.noise import native



from bloqade.qasm2.emit import QASM2 # the QASM2 target
from bloqade.qasm2.parse import pprint # the QASM2 pretty printer



@qasm2.extended
def add_X_syndrome_circuit(qreg: qasm2.QReg,creg:qasm2.CReg,ndataqubits:int,stabindex:int,index_tuple:tuple[int, ...]):
    qasm2.h(qreg[ndataqubits+stabindex])
    for i in range(len(index_tuple)):
        qasm2.cx(qreg[ndataqubits+stabindex],qreg[index_tuple[i]])
    qasm2.h(qreg[ndataqubits+stabindex])
    qasm2.measure(qreg[ndataqubits+stabindex],creg[stabindex])



@qasm2.extended
def add_Z_syndrome_circuit(qreg: qasm2.QReg,creg:qasm2.CReg,ndataqubits:int,stabindex:int,index_tuple:tuple[int, ...]):
    for i in range(len(index_tuple)):
        qasm2.cx(qreg[index_tuple[i]],qreg[ndataqubits+stabindex])
    qasm2.measure(qreg[ndataqubits+stabindex],creg[stabindex])



@qasm2.extended
def surface_code_d2_circuit():
    qreg = qasm2.qreg(2*3**2-1)
    creg = qasm2.creg(3**2-1)
    add_X_syndrome_circuit(qreg,creg,9,0,(1,2,4,5))
    add_X_syndrome_circuit(qreg,creg,9,1,(4,5,7,8))
    
    add_X_syndrome_circuit(qreg,creg,9,2,(2,3))    
    add_X_syndrome_circuit(qreg,creg,9,3,(8,9))    
    
    add_Z_syndrome_circuit(qreg,creg,9,4,(2,3,5,6))
    add_Z_syndrome_circuit(qreg,creg,9,5,(5,6,8,9))
    
    
    add_Z_syndrome_circuit(qreg,creg,9,6,(1,4))    
    add_Z_syndrome_circuit(qreg,creg,9,7,(3,6))          


    
    
if __name__ == '__main__':
    '''
    suf=surfaceCode(3)
    suf.inject_error({1:'X'})
    suf.draw_surface()
    suf.print_stab()
    '''
    
    
    #print(suf._Hmatrix)
    #suf.compile_syndrome_circuit()
    #result=suf.run_simulation(1)
    #print(result)
    
    
    target = QASM2()
    ast = target.emit(surface_code_d2_circuit)
    pprint(ast)