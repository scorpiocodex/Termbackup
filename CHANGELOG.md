# CHANGELOG

All notable changes to **Termbackup** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

## [2.0.0] - 2024-05-24
### Added
- **Profiles Command**: New `profiles` command to list all configured TermBackup profiles globally.
- **Diff Command**: New `diff` command providing cryptographic delta computation between remote backup and local target.
- **Delete Commands**: Introduced native mechanisms to delete profiles locally and purge snapshots dynamically from remote via `delete` and `delete-snapshot`.
- **SHA-256 Manifest Integrity**: Replaced stub hashing with cryptographically secure continuous SHA-256 integrity verifications.

### Changed
- Implemented persistent DEK-encrypted `Ed25519` signing keys during profile init.
- Overhauled TermBackup CLI UI with Next-Gen Nexus Zero-Trust Matrix formatting.
- Designed resilient fallback storage to JSON configs dynamically when OS `keyring` fails.
- Re-architected `github.py` with strict context manager support.

### Fixed
- Fixed `doctor.py` attempting to execute synchronous code via `await` and `asyncio.run`.
- Fixed silent `pass` failure mechanisms inside `audit.py`, enabling reliable fallback auditing.

## [1.0.0] - 2026-02-23
### Added
- **Nexus Matrix Engine**: Initial release of the termbackup architecture.
- **Zero-Trust Encryption**: Complete client-side `AES-256-GCM` symmetric encryption pipeline.
- **Argon2 KDF Validation**: Master key protection via memory-hard Argon2id.
- **24-word Recovery Phrases**: Cryptographically secure system for emergency decryption bypassing.
- **Ghost Protocol Daemon**: Fully functional background `systemd` / `Task Scheduler` profile runner.
- **Terminal UI (TUI)**: Beautiful, exact "Termbackup" ASCII banners, neon-styled tables, and dynamic progress bars via `Rich`.
- **Plugin Registry**: Sandboxed extension loading via Python `entry_points` (`termbackup.plugins`).
- **Doctor Diagnostic Suite**: A 12-point network, permission, and cryptography test module.
- **Native GitHub API**: Direct `httpx` integration bypassing standard `git`, pushing raw encrypted objects seamlessly without `.git` folders.
- **Comprehensive Documentation**: Included sci-fi themed `README.md`, `LICENSE`, and `CHANGELOG.md`.

### Changed
- Re-architected previous concepts into a stable, highly-performant synchronized python application.
- Redesigned the Typer CLI `help` string rendering for a pristine, ultra-modern developer experience.
- Hand-tuned Unicode/ASCII rendering alignments across platforms.

### Fixed
- Fixed Python `asyncio.run` thread leaking when Typer invokes nested coroutines.
- Fixed layout wrapping logic on Windows MS Terminal (`rich.Table` column alignment handling).
- Fixed collision bugs inside the extension API.
