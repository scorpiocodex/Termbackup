"""
Quantum Delta Snapshot Engine implementation.
Packages, compresses, encrypts, and signs snapshots.
"""
import base64
import gzip
import io
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from .crypto import (
    decrypt,
    derive_key,
    generate_nonce,
    sign,
)
from .delta import scan_directory
from .errors import DecryptionError, SnapshotCreationError
from .models import Profile, SnapshotMeta
from .utils import timestamp_id

MAGIC_BYTES = b"TBK\x07"

def get_master_dek(profile: Profile, password: str) -> bytes:
    """Decrypt the Master DEK using the user's password."""
    salt = base64.b64decode(profile.master_key_salt)
    key_encrypting_key = derive_key(password, salt)
    
    enc_dek = base64.b64decode(profile.master_key_enc)
    try:
        dek = decrypt(enc_dek, key_encrypting_key)
        return dek
    except DecryptionError:
        raise DecryptionError("Incorrect password for this profile.")

def create_snapshot(
    profile: Profile, 
    password: str,
    signing_key_raw: bytes,
    parent_id: Optional[str] = None
) -> Tuple[Path, SnapshotMeta]:
    """
    Scan, package, and encrypt a snapshot using the Profile's Master DEK.
    """
    dek = get_master_dek(profile, password)
    
    source_dir = Path(profile.source_dir).resolve()
    if not source_dir.is_dir():
        raise SnapshotCreationError(f"Backup source '{source_dir}' does not exist or is not a directory.")

    # 1. Scan directory
    fingerprints = scan_directory(source_dir, profile.exclude_patterns)
    file_count = len(fingerprints)
    total_size = sum(f.size for f in fingerprints)
    
    # Generate unique AES-GCM nonce for this specific snapshot payload
    nonce = generate_nonce()
    
    # Generate snapshot ID
    snap_id = timestamp_id()
    snap_filename = f"snapshot_{snap_id}.tbk"
    
    temp_dir = Path(os.environ.get("TEMP", "/tmp")) / f"termbackup_build_{snap_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    tbk_path = temp_dir / snap_filename
    
    # 2. Package tar/gz into memory (or temp file for large sizes, but for now we buffer locally)
    # Since files can be large, we stream tar straight into gzip into memory. For true large files, 
    # we would stream directly to disk and encrypt in chunks, but AESGCM in cryptography requires 
    # the whole payload. We will buffer to bytes for simplicity, up to available RAM.
    # A true extreme-scale app uses STREAMING symmetric encryption, but standard AESGCM is one-shot.
    # We will use one-shot as per standard python `cryptography` lib usage for AESGCM.
    
    try:
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=6) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tar:
                # Add metadata JSON first so restore can preview it fast
                meta_data = f'{{"snapshot_id": "{snap_id}", "parent": "{parent_id or ""}"}}'.encode("utf-8")
                ti = tarfile.TarInfo(name=".tbk_meta.json")
                ti.size = len(meta_data)
                tar.addfile(ti, io.BytesIO(meta_data))
                
                # Add all files
                for fp in fingerprints:
                    tar.add(source_dir / fp.relative_path, arcname=fp.relative_path)
            
        payload = buffer.getvalue()
        buffer.close()
        
        # 3. Encrypt payload
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(dek)
        # AESGCM.encrypt returns ciphertext + tag
        encrypted_payload = aesgcm.encrypt(nonce, payload, None)
        
        # 4. Sign the package
        signature = sign(encrypted_payload, signing_key_raw)
        
        # 5. Write .tbk file structure:
        # [MAGIC 4] [NONCE 12] [SIG_LEN 2] [SIG ...] [ENCRYPTED_PAYLOAD]
        sig_len = len(signature)
        with tbk_path.open("wb") as f_out:
            f_out.write(MAGIC_BYTES)
            f_out.write(nonce)
            f_out.write(sig_len.to_bytes(2, "big"))
            f_out.write(signature)
            f_out.write(encrypted_payload)
            
        meta = SnapshotMeta(
            snapshot_id=snap_id,
            timestamp=datetime.now(timezone.utc),
            parent_id=parent_id,
            file_count=file_count,
            total_size=total_size,
            salt_b64="", # Salt no longer needed on a per-snapshot level if DEK is used
            nonce_b64=base64.b64encode(nonce).decode("ascii")
        )
        return tbk_path, meta
        
    except Exception as e:
        if tbk_path.exists():
            tbk_path.unlink()
        try:
            temp_dir.rmdir()
        except Exception:
            pass
        raise SnapshotCreationError(f"Failed to create snapshot: {e}") from e
