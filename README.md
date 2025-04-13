# 2025YaleQHack

This is the soluation of QuBruin team for 2025 Yale Hackathon. We are students from UCLA.

<img src="Figures/Logo.png" alt="alt text" width="300"> 

Team member: 
John Ye, Hanyu Wang, Harry Wang, Luca Niu, Victor Yu

In this challenge, we explore two different area to demonstrate the power of new language feature, as well as software-hardware codesign. First, we implement error correction code such as repetition code and surface code. With the help of modularized design and function reusing, we show that we can also implement simple logical algorithm with surface code. We also use recursion to implement fault-tolerant syndrome measurement. Second, we implement a second-order Trotterized time evolution simulation of the transverse-field Ising model (TFIM)—a paradigmatic strongly correlated system exhibiting two distinct phases determined by the competition between spin-spin interactions and external transverse fields.By adiabatically tuning the Hamiltonian parameters, our simulations successfully detect the crossing of the critical point separating these phases. Furthermore, we optimize the quantum circuit to minimize the number of required pulses, demonstrating an efficient quantum simulation protocol for the TFIM. We have also put a lot of effort in figuring out the compilation automation pipeline, such that all of our algorithm can be compiled down to atom movements, we also use video to demonstrate our compilation. In the contest, we find some potential bugs in the provided packages. 



# Environment setup

To reproduce the result, we recommend you to use virtual environment. 

Windows

```bash
cd path\to\your\project
py -m venv yalehack
yalehack\Scripts\activate
pip install -r requirements.txt
pip install cirq
pip install ply
```

Mac

```bash
cd path/to/your/project
python3 -m venv yalehack
source yalehack/bin/activate
pip install -r requirements.txt
```









