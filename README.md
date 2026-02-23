<div align="center">

# ◢ 𝙏𝙀𝙍𝙈𝘽𝘼𝘾𝙆𝙐𝙋 ◣
## ❖ NEXUS ZERO-TRUST MATRIX ENGINE ❖

A next-generation zero-trust encrypted backup engine forged for terminal supremacy. Encrypt reality. Trust nothing.

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg?style=for-the-badge)](https://github.com/scorpiocodex/Termbackup)
[![Code Quality](https://img.shields.io/badge/Code_Quality-Pristine-purple.svg?style=for-the-badge)](https://github.com/scorpiocodex/Termbackup)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg?style=for-the-badge)](https://github.com/scorpiocodex/Termbackup)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

*Author:* **ScorpioCodeX**  
*Contact:* **scorpiocodex0@gmail.com**

</div>

---

## ⚡ WHAT IS TERMBACKUP?

**Termbackup v1.0** is an extremely powerful, fully-client-side-encrypted repository synchronizer. If you work with sensitive data, configuration files, or local secrets, you need absolute cryptographic certainty that your remote backups are private.

Termbackup is a professionally hardened, cryptographic vault designed to live inside your terminal. It compresses, encrypts, and uploads backups of your critical directories natively over the GitHub API, silently bypassing the need for Git histories. No plaintext files are ever written to remote storage. **Absolute zero-trust.**

---

## 🌌 NEXT-GENERATION FEATURES

- 🔒 **AES-256-GCM Encryption**: Your payloads are encrypted and authenticated simultaneously, guaranteeing absolute zero-trust privacy before the data ever leaves your machine.
- 🧠 **Argon2id Key Derivation**: High-grade, memory-hard hashing preventing brute forces on your Master Data Encryption Key (DEK).
- 🛡️ **24-word Recovery Phrases**: For catastrophic password loss, your Master Key can be recovered via an isolated BIP39-esque phrase. 
- ✍️ **Ed25519 Manifest Signing**: Identifies exactly which client pushed a payload to prevent tampering dynamically.
- 🛸 **Live Holographic Terminal UI**: Breathtaking terminal arrays powered by `Rich`—featuring cyberpunk gradients, dynamic progress bars, and pristine data tables.
- 👻 **Ghost Protocol (Daemon)**: Run Termbackup completely silently in the background via `systemd` or Windows Task Scheduler, ensuring backups happen without active input.
- 🩺 **The Doctor Diagnostics**: Run a 12-point automated scan directly in your terminal to instantly analyze cryptography bindings, network health, and filesystem integrations.

---

## 🧑‍🚀 INSTALLATION PROTOCOL

Termbackup is maintained securely and natively on GitHub. To use it, simply install it directly from this repository using `pipx` or `pip`. It requires **Python 3.10+**.

### The Best Way (`pipx`)
If you want Termbackup to be available globally anywhere on your system, use `pipx` (highly recommended):
```bash
pipx install git+https://github.com/scorpiocodex/Termbackup.git
```

### The Standard Way (`pip`)
If you're using a specific virtual environment:
```bash
pip install git+https://github.com/scorpiocodex/Termbackup.git
```

---

## 🚀 QUICK START GUIDE

Ready to secure your reality? Archiving data takes less than a minute.

**1. Initialize your vault**
Tell Termbackup your profile name, the folder to safeguard, and your empty target GitHub repository.
```bash
python -m termbackup.cli init --name secret_vault --repo scorpiocodex/my-vault-repo --source ./my_conf_files
```
*It will ask for your GitHub Personal Access Token and a password. It will give you a 24-word recovery phrase. Write it down!*

**2. Run a Snapshot**
Instantly compress, encrypt, and push your zero-trust backup to GitHub.
```bash
python -m termbackup.cli snapshot secret_vault
```

**3. List Backups**
Fetch the remote manifest from GitHub to review your timeline.
```bash
python -m termbackup.cli list secret_vault
```

**4. Restore Data**
Extract your files securely down to a specified directory anywhere.
```bash
python -m termbackup.cli restore secret_vault <SNAPSHOT_ID> --target ./recovered_files
```

---

### 🛠️ Useful Commands

| Command | What it does |
| --- | --- |
| `init` | Initializes a brand new encrypted vault profile and generates Master Keys. |
| `snapshot` | Creates a zero-trust backup archive, encrypts it, and pushes it remotely. |
| `restore` | Pulls an encrypted archive, decrypts it, and safely restores files. |
| `list` | Lists all remote records and snapshot manifest footprints. |
| `doctor` | Runs the advanced 12-point environment diagnostic suite. |
| `daemon` | Generates system services or executes background backup routines (`Ghost Protocol`). |
| `audit` | Displays security and application logs securely recorded by Termbackup. |
| `plugin` | Shows loaded and securely verified third-party extensions. |

---

## 🧩 PLUGINS AND EXTENSIONS

Termbackup supports a heavily isolated **Plugin Architecture** that can extend its lifecycle natively (such as securely shredding terminal logs post-snapshot).

Plugins are standard Python packages that register into the `termbackup.plugins` entry point. 

**To install a third-party plugin:**
```bash
pip install termbackup-plugin-aws-bridge
```
Then verify the runtime has successfully loaded and validated it:
```bash
python -m termbackup.cli plugin
```

---

<div align="center">

```text
                                                                               
  _|_|_|_|_|                                  _|                            _|                          
      _|      _|_|    _|  _|_|  _|_|_|  _|_|  _|_|_|      _|_|_|    _|_|_|  _|  _|    _|    _|  _|_|_|  
      _|    _|_|_|_|  _|_|      _|    _|    _|  _|    _|  _|    _|  _|        _|_|      _|    _|  _|    _|
      _|    _|        _|        _|    _|    _|  _|    _|  _|    _|  _|        _|  _|    _|    _|  _|    _|
      _|      _|_|_|  _|        _|    _|    _|  _|_|_|      _|_|_|    _|_|_|  _|    _|    _|_|_|  _|_|_|  
                                                                                                    _|      
                                                                                                    _|      
```

  <p><b>Created with passion by ScorpioCodeX.</b></p>
  <p><i>The future of reactive cryptography has arrived.</i></p>
</div>
