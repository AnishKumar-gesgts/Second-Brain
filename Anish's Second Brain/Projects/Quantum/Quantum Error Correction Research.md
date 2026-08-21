**Project: Quantum**

This project is tracked in the vault [[Anish's Second Brain/Setup/GOALS|goals]] and [[Anish's Second Brain/Documents/Things I've Done|work history]].

Overview

This project collects simulation code and experiments related to error-detection and loss-aware decoding for quantum error correction. The current contents include a Science Fair project (2025–2026) with simulation scripts and test programs. The project folder is intended to hold research code, small reproducible experiments, and notes required for outreach or reproducibility.

Contents summary

- [[Anish's Second Brain/Projects/Quantum/HybridMCMC-CRW/Hybrid MCMC Correlated Random-Walk Decoder|HybridMCMC-CRW]]: Holds the extracted proposal for Hybrid Monte Carlo / correlated random-walk style decoder work.

- `Science Fair 25_26/`: Contains the main simulation code and supporting tests used for the Science Fair project. Key files:
  - `Simulation Program.py`: Qiskit-based simulation that models amplitude-damping / loss and runs decoders.
  - `test/`: A collection of small test scripts used during development (Qiskit Aer smoke tests, decoder experiments, and ancilla post-processing).

Next actions

- Add a `requirements.txt` in the project root describing Python deps (e.g., `qiskit`, `qiskit-aer`, `numpy`).
- Optionally, move or remove the original `Quantum` directory after verifying copies.
