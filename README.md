```                                                                               
  _|_|_|_|_|                                  _|                            _|                          
      _|      _|_|    _|  _|_|  _|_|_|  _|_|  _|_|_|      _|_|_|    _|_|_|  _|  _|    _|    _|  _|_|_|  
      _|    _|_|_|_|  _|_|      _|    _|    _|  _|    _|  _|    _|  _|        _|_|      _|    _|  _|    _|
      _|    _|        _|        _|    _|    _|  _|    _|  _|    _|  _|        _|  _|    _|    _|  _|    _|
      _|      _|_|_|  _|        _|    _|    _|  _|_|_|      _|_|_|    _|_|_|  _|    _|    _|_|_|  _|_|_|  
                                                                                                    _|      
                                                                                                    _|      
```
> **A next-generation zero-trust encrypted backup engine forged for terminal supremacy. Encrypt reality. Trust nothing.**

---

## ⚡ The Nexus Matrix Engine
Welcome to **Termbackup v1.0**. 
Termbackup is an extremely powerful, fully-client-side-encrypted repository synchronizer. It is a professionally hardened, cryptographic vault designed to live inside your terminal. It compresses, encrypts, and uploads backups of your critical directories natively over the GitHub API, silently bypassing the need for Git histories. 

No plaintext files are ever written to remote storage. **Absolute zero-trust.**

---

## 🔒 Next-Gen Security Architecture
We don't play around with your data. The engine utilizes state-of-the-art systems:
- **AES-256-GCM Encryption**: Your payloads are encrypted and authenticated simultaneously.
- **Argon2id Key Derivation**: High-grade, memory-hard hashing preventing brute forces on your Master Data Encryption Key (DEK).
- **24-word Recovery Phrases**: For catastrophic password loss, your Master Key can be recovered via an isolated BIP39-esque phrase. 
- **Ed25519 Ephemeral Manifest Signing**: Identifies exactly which client pushed a payload to prevent tampering.

---

## 🚀 Installation & Setup

Termbackup is NOT available on PyPI—it must be pulled natively from GitHub. 
It requires **Python 3.10+**.

### Use pip or pipx natively from GitHub:
You can use `pipx` (recommended) to install the CLI seamlessly across your OS globally:
```bash
# Recommended standard install
pipx install git+https://github.com/scorpiocodex/Termbackup.git

# Alternatively via pip into your current environment
pip install git+https://github.com/scorpiocodex/Termbackup.git
```

This will automatically expose the `termbackup` command to your shell globally.

---

## 💻 Quick Start Guide

Termbackup's commands are elegant and easy to understand.

### 1. Initialize a Vault
You need a GitHub repository to push to. Tell Termbackup your profile name, the directory to safeguard, and your target repo:
```bash
python -m termbackup.cli init --name secret_vault --repo scorpiocodex/my-vault-repo --source ./my_conf_files
```
You will be prompted to provide your **GitHub Personal Access Token** and a secure vault password. 
> *IMPORTANT*: You will be handed a 24-word recovery phrase. Write it down immediately!

### 2. Run a Snapshot
Instantly compress, encrypt, and back up your files.
```bash
python -m termbackup.cli snapshot secret_vault
```

### 3. List Backups
Review reality. Request the remote manifest from GitHub.
```bash
python -m termbackup.cli list secret_vault
```

### 4. Restore Data
Extract your files securely down to a specified directory.
```bash
python -m termbackup.cli restore secret_vault <SNAPSHOT_ID> --target ./recovered_files
```

---

## 👻 Ghost Protocol (Daemon)
Never think about backups again. Generate and run background schedulers for **Linux** or **Windows**:
```bash
# Preview how termbackup creates a background job (e.g., XML for Windows, .service for Linux)
python -m termbackup.cli daemon secret_vault --interval 60 --generate

# Execute it in the background permanently
python -m termbackup.cli daemon secret_vault --interval 60
```

---

## 🩺 The Doctor
Having issues? Run the automated 12-point diagnostics module to test cryptography bindings, hardware networking, and filesystem scopes instantly in terminal:
```bash
python -m termbackup.cli doctor
```

---

## 🧩 Installing Termbackup Plugins
Termbackup supports a heavily isolated **Plugin Architecture** that can extend its lifecycle (like securely shredding terminal logs or advanced auditing).

Plugins are standard Python packages that register into the `termbackup.plugins` entry point. 
To install a third-party plugin:
```bash
# Example
pip install termbackup-plugin-aws-bridge

# Check it works
python -m termbackup.cli plugin
```

---

### Author & License
Engineered and maintained natively by **ScorpioCodeX**.
Licensed under the **MIT License**.

*End of Line.*
