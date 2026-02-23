"""
Chronos Multi-Epoch Restore engine.
Safely extracts validated paths, diffs against filesystem, previews trees.
"""
import tarfile
import gzip
import io
import os
from pathlib import Path
from typing import List, Optional

from rich.tree import Tree

from .models import Profile, SnapshotMeta, DeltaResult
from .errors import RestoreExtractionError, DecryptionError
from .crypto import derive_key, decrypt, verify
from .utils import validate_path
from .snapshot import MAGIC_BYTES, get_master_dek

def list_snapshots(profile: Profile, password: str) -> List[SnapshotMeta]:
    """Stub to list snapshots for the profile."""
    return []

def _read_snapshot_payload(tbk_path: Path, dek: bytes, public_key_raw: Optional[bytes] = None) -> bytes:
    """Reads the .tbk file, verifies signature, and decrypts it with the DEK."""
    with tbk_path.open("rb") as f:
        magic = f.read(len(MAGIC_BYTES))
        if magic != MAGIC_BYTES:
            raise RestoreExtractionError(f"Invalid magic bytes in {tbk_path}. Not a valid tbk file.")
            
        nonce = f.read(12)
        sig_len_bytes = f.read(2)
        if len(sig_len_bytes) < 2:
            raise RestoreExtractionError("File too short.")
        sig_len = int.from_bytes(sig_len_bytes, "big")
        
        signature = f.read(sig_len)
        encrypted_payload = f.read()
        
    if public_key_raw:
        if not verify(encrypted_payload, signature, public_key_raw):
            raise RestoreExtractionError("Signature verification failed. The snapshot may have been tampered with.")
            
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(dek)
        plaintext = aesgcm.decrypt(nonce, encrypted_payload, None)
        return plaintext
    except Exception as e:
        raise DecryptionError(f"Failed to decrypt snapshot: {e}") from e

def preview_tree(tbk_path: Path, profile: Profile, password: str, public_key_raw: Optional[bytes] = None) -> Tree:
    """Decrypt the snapshot in memory and generate a Rich Tree preview of its contents."""
    dek = get_master_dek(profile, password)
    plaintext = _read_snapshot_payload(tbk_path, dek, public_key_raw)
    
    buffer = io.BytesIO(plaintext)
    tree = Tree(f"📦 [bold cyan]{tbk_path.name}[/]")
    
    try:
        with gzip.GzipFile(fileobj=buffer, mode="rb") as gz:
            with tarfile.open(fileobj=gz, mode="r") as tar:
                for member in tar.getmembers():
                    if member.name == ".tbk_meta.json":
                        continue
                    # A naive flat tree for now, in a real TUI we'd nest the folders
                    tree.add(f"[green]{member.name}[/] ({member.size} B)")
    except Exception as e:
        raise RestoreExtractionError(f"Failed to read tar archive: {e}") from e
        
    return tree

def diff_snapshot(tbk_path: Path, profile: Profile, password: str, target_dir: Path) -> DeltaResult:
    """Compare what is in the snapshot vs what's currently in target_dir."""
    # Simplified mock for the diff feature. In a full implementation,
    # we'd hash the files in target_dir and compare them against tar.getmembers()
    return DeltaResult()

def restore_snapshot(
    tbk_path: Path, 
    profile: Profile, 
    password: str, 
    target_dir: Path, 
    public_key_raw: Optional[bytes] = None,
    overwrite: bool = False
) -> None:
    """
    Safely extract the snapshot to target_dir. 
    Strict path traversal prevention applied.
    """
    dek = get_master_dek(profile, password)
    plaintext = _read_snapshot_payload(tbk_path, dek, public_key_raw)
    
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    buffer = io.BytesIO(plaintext)
    try:
        with gzip.GzipFile(fileobj=buffer, mode="rb") as gz:
            with tarfile.open(fileobj=gz, mode="r") as tar:
                for member in tar.getmembers():
                    if member.name == ".tbk_meta.json":
                        continue
                        
                    # 1. Path traversal defense
                    try:
                        extracted_path = validate_path(target_dir / member.name, target_dir)
                    except Exception as e:
                        # Log/skip dangerous paths
                        continue
                        
                    # 2. Overwrite protection
                    if extracted_path.exists() and not overwrite:
                        raise RestoreExtractionError(f"File {extracted_path} already exists. Use overwrite=True.")
                        
                    # Ensure parent dir exists
                    extracted_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if member.isdir():
                        extracted_path.mkdir(exist_ok=True)
                    elif member.isfile():
                        f_in = tar.extractfile(member)
                        if f_in:
                            with extracted_path.open("wb") as f_out:
                                f_out.write(f_in.read())
                            
                            # Restore mtime
                            os.utime(extracted_path, (member.mtime, member.mtime))
                            
    except RestoreExtractionError:
        raise
    except Exception as e:
        raise RestoreExtractionError(f"Extraction failed: {e}") from e
