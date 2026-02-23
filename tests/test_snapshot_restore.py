import pytest
import os
import shutil
import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone

from termbackup.models import Profile
from termbackup.snapshot import create_snapshot
from termbackup.restore import restore_snapshot
from termbackup.crypto import generate_signing_keypair, generate_salt, derive_key, encrypt

@pytest.fixture
def mock_profile(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    (source_dir / "file1.txt").write_text("Hello World")
    
    pwd = "testpassword123"
    salt = generate_salt()
    master_dek = os.urandom(32)
    kek = derive_key(pwd, salt)
    enc_dek = encrypt(master_dek, kek)
    
    prof = Profile(
        name="test_profile",
        source_dir=str(source_dir),
        repo="user/repo",
        token_ref="mock_token",
        created_at=datetime.now(timezone.utc),
        master_key_enc=base64.b64encode(enc_dek).decode("ascii"),
        master_key_salt=base64.b64encode(salt).decode("ascii"),
        recovery_key_enc="",
        recovery_key_salt=""
    )
    return prof, pwd, source_dir

def test_snapshot_restore_cycle(mock_profile, tmp_path: Path):
    prof, pwd, source = mock_profile
    priv, pub = generate_signing_keypair()
    
    # Create Snapshot
    tbk_path, meta = create_snapshot(prof, pwd, priv)
    
    assert tbk_path.exists()
    assert meta.file_count == 1
    
    # Restore Snapshot
    target_dir = tmp_path / "restore"
    target_dir.mkdir()
    
    restore_snapshot(tbk_path, prof, pwd, target_dir, pub)
    
    assert (target_dir / "file1.txt").exists()
    assert (target_dir / "file1.txt").read_text() == "Hello World"
