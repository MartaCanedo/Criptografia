# 🔐 CryptoLab — Cryptography & Performance Analysis

A Python-based cryptography project for file encryption, decryption, and performance analysis of cryptographic algorithms.

CryptoLab combines a graphical user interface (GUI), a command-line interface (CLI), and benchmarking tools to explore cryptographic operations and compare execution performance across different encryption modes.

## ✨ Features

- **File Encryption & Decryption** — Encrypt and decrypt files using configurable cryptographic modes.
- **AES Encryption** — Implementations of AES-CBC, AES-CTR, and AES-GCM.
- **Additional Algorithms** — Includes ChaCha20-Poly1305 and Triple DES (3DES) implementations.
- **Graphical User Interface** — Desktop application built with Python and Tkinter.
- **Command-Line Interface** — CLI for file encryption and decryption workflows.
- **Performance Benchmarking** — Tools for measuring and comparing cryptographic execution times.
- **Data Visualization** — Benchmark results can be exported to CSV and explored through graphical visualizations.
- **Key Management** — Utilities for generating and loading cryptographic keys.

## 🛠️ Technologies

- Python
- PyCryptodome
- Tkinter
- Matplotlib
- CSV data processing

## 📁 Project Structure

```text
Criptografia/
├── app_gui.py
├── benchmark.py
├── benchmark_results.csv
├── cli.py
├── create_2gb_file.py
├── crypto_utils.py
├── file_ops.py
├── requirements.txt
└── output/
```

## 🚀 Getting Started

### Prerequisites

- Python 3
- pip

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Theproxycos/Criptografia.git
   cd Criptografia
   ```

2. Install the project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

### Launching the GUI

```bash
python app_gui.py
```

### Command-Line Interface

The CLI provides commands for file encryption and decryption. Its current implementation supports the following interface:

```bash
python cli.py encfile input.txt encrypted.bin --mode GCM --keyfile key.bin
```

```bash
python cli.py decfile encrypted.bin decrypted.txt --keyfile key.bin
```

**Note:** Verify the CLI module imports and the file format expected by the decryption function before running these examples. The current source references `aes_utils`, which should be reconciled with the modules present in the repository.

## 📊 Performance Analysis

CryptoLab includes benchmarking utilities and CSV-based results for exploring the performance of cryptographic operations.

Potential comparison dimensions include:

- Encryption and decryption execution time
- Cryptographic mode
- Input file size
- Key size

Actual results depend on the benchmark configuration and the execution environment.

## 🔒 Security Considerations

This project is intended for learning, experimentation, and cryptographic performance analysis.

- Keep cryptographic keys private and store them securely.
- Do not use custom cryptographic implementations to protect sensitive production data without an independent security review.
- Prefer established authenticated encryption schemes, such as AES-GCM, with correctly managed keys and nonces.
- Treat legacy algorithms such as 3DES as educational or compatibility examples rather than preferred choices for new systems.

## 🎯 Project Goals

- Explore practical cryptographic implementations in Python.
- Understand the differences between encryption modes.
- Experiment with file encryption and decryption workflows.
- Measure and visualize cryptographic performance.
- Develop practical skills in software development and applied cryptography.

## 👨‍💻 Author

**Theproxycos**

GitHub: [@Theproxycos](https://github.com/Theproxycos)

---

*Built with Python to explore cryptography, file security, and performance analysis.*
