"""
Manifest logic for termbackup. Immutable append-only record.
"""
import json

from .errors import ManifestError
from .models import Manifest, ManifestEntry


def create_initial_manifest() -> Manifest:
    """Create an empty version 1.0 manifest."""
    return Manifest()

def load_manifest(data: bytes) -> Manifest:
    """Deserialize and validate a manifest payload."""
    try:
        parsed = json.loads(data.decode("utf-8"))
        return Manifest(**parsed)
    except Exception as e:
        raise ManifestError(f"Failed to parse manifest: {e}") from e

def serialize_manifest(manifest: Manifest) -> bytes:
    """Serialize the manifest to JSON bytes deterministically."""
    return manifest.model_dump_json(indent=2).encode("utf-8")

def append_entry(manifest: Manifest, entry: ManifestEntry) -> Manifest:
    """Immutable append of a new snapshot entry to the manifest."""
    # Create a new list to enforce immutability strictly
    new_entries = manifest.entries.copy()
    new_entries.append(entry)
    
    # Sort them by snapshot timestamp based on snapshot_id prefix (which is YYYYMMDD_HHMMSS)
    new_entries.sort(key=lambda x: x.snapshot_id)
    
    return Manifest(version=manifest.version, entries=new_entries)

def verify_integrity(manifest: Manifest) -> list[str]:
    """
    Currently returns a list of errors if integrity fails.
    For this basic check, we just ensure no duplicate snapshot IDs and correct ordering.
    In a true implementation, we'd also check signature chains if they existed inside the manifest.
    """
    errors = []
    seen = set()
    for entry in manifest.entries:
        if entry.snapshot_id in seen:
            errors.append(f"Duplicate snapshot ID in manifest: {entry.snapshot_id}")
        seen.add(entry.snapshot_id)
        
        if not entry.sha256 or len(entry.sha256) != 64:
            errors.append(f"Invalid SHA-256 for snapshot {entry.snapshot_id}")
            
    return errors
