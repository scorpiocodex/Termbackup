"""
Core utilities for TermBackup.
"""
import ctypes
import hashlib
import os
import shutil
import signal
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator


def is_windows() -> bool:
    """Return True if running on Windows."""
    return sys.platform == "win32"

def mask_token(token: str) -> str:
    """Mask a token, returning only the last 4 characters visible."""
    if not token or len(token) < 8:
        return "****"
    return "*" * (len(token) - 4) + token[-4:]

def secure_shred_file(path: Path) -> None:
    """Securely overwrite and remove a file."""
    if not path.is_file():
        return
    try:
        size = path.stat().st_size
        with path.open("wb") as f:
            # Overwrite with random bytes
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

@contextmanager
def secure_temp_dir() -> Generator[Path, None, None]:
    """Provide a secure temporary directory that is shredded on cleanup."""
    temp_dir = Path(tempfile.mkdtemp(prefix="termbackup_"))
    try:
        # Secure permissions 700
        if not is_windows():
            temp_dir.chmod(0o700)
        yield temp_dir
    finally:
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                secure_shred_file(Path(root) / name)
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

def validate_path(path: str | Path, base_dir: str | Path) -> Path:
    """
    Resolve a path and ensure it falls strictly under the base_dir to prevent directory traversal.
    """
    resolved_path = Path(path).resolve()
    resolved_base = Path(base_dir).resolve()
    
    if not str(resolved_path).startswith(str(resolved_base)):
        from .errors import PathTraversalError
        raise PathTraversalError(f"Path '{path}' escapes base directory '{base_dir}'.")
    return resolved_path

def sha256_file(path: Path) -> str:
    """Stream a file and return its SHA-256 hex digest."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def human_size(nbytes: int) -> str:
    """Convert bytes to a human-readable string (e.g. 1.2 MiB)."""
    if nbytes == 0:
        return "0 B"
    suffixes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0  # type: ignore
        i += 1
    if i == 0:
        return f"{int(nbytes)} {suffixes[i]}"
    return f"{nbytes:.1f} {suffixes[i]}"

def timestamp_id() -> str:
    """Return a YYYYMMDD_HHMMSS formatted string."""
    return time.strftime("%Y%m%d_%H%M%S")

def setup_signal_handlers(cleanup_fn: Callable[[], None]) -> None:
    """Install SIGINT/SIGTERM handlers that invoke the cleanup function and exit."""
    def handler(signum: Any, frame: Any) -> None:
        cleanup_fn()
        sys.exit(1)
        
    signal.signal(signal.SIGINT, handler)
    if not is_windows():
        signal.signal(signal.SIGTERM, handler)

def zero_memory(data: bytearray | memoryview) -> None:
    """Best-effort to zero-out sensitive memory buffers."""
    try:
        if isinstance(data, bytearray):
            ctypes.memset(id(data) + 16, 0, len(data))  # Rough CPython struct offset
        elif isinstance(data, memoryview):
            for i in range(len(data)):
                data[i] = 0
    except Exception:
        pass
