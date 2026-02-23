"""
Pydantic v2 data models for TermBackup.
"""
import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)

class Profile(FrozenModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    source_dir: str
    repo: str  # Format: "user/repo"
    token_ref: str  # Reference name in keyring or config fallback
    exclude_patterns: List[str] = Field(default_factory=list)
    created_at: datetime
    master_key_enc: str      # Base64 encoded, encrypted Master DEK
    master_key_salt: str     # Base64 encoded Argon2 salt for the password
    recovery_key_enc: str    # Base64 encoded, DEK encrypted with Recovery Phrase
    recovery_key_salt: str   # Base64 encoded salt for the recovery phrase KDF

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", v):
            raise ValueError("Repo must be in 'owner/name' format")
        return v

class FileFingerprint(FrozenModel):
    relative_path: str
    sha256: str
    size: int
    mtime: float

class SnapshotMeta(FrozenModel):
    snapshot_id: str
    timestamp: datetime
    parent_id: Optional[str]
    file_count: int
    total_size: int
    salt_b64: str
    nonce_b64: str

class ManifestEntry(FrozenModel):
    snapshot_id: str
    filename: str
    sha256: str
    size: int
    uploaded_at: datetime

class Manifest(FrozenModel):
    version: str = "1.0"
    entries: List[ManifestEntry] = Field(default_factory=list)

class DeltaResult(FrozenModel):
    added: List[FileFingerprint] = Field(default_factory=list)
    modified: List[FileFingerprint] = Field(default_factory=list)
    deleted: List[FileFingerprint] = Field(default_factory=list)
    unchanged: List[FileFingerprint] = Field(default_factory=list)

class PluginMeta(FrozenModel):
    name: str
    version: str
    entry_point: str
    verified: bool

class DoctorCheck(FrozenModel):
    name: str
    status: Literal["pass", "warn", "fail"]
    detail: str
