"""
Delta Engine: parallel hashing and sector-level delta detection.
"""
import concurrent.futures
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import DeltaResult, FileFingerprint
from .utils import sha256_file

# Extensions that are already compressed, we skip compression for these.
COMPRESSED_EXTS: Set[str] = {
    ".zip", ".gz", ".xz", ".bz2", ".7z", ".rar", 
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mkv", ".mp3"
}

def scan_file(path: Path, base_dir: Path) -> FileFingerprint:
    """Hash and stat a single file."""
    stat = path.stat()
    rel_path = path.relative_to(base_dir).as_posix()
    return FileFingerprint(
        relative_path=rel_path,
        sha256=sha256_file(path),
        size=stat.st_size,
        mtime=stat.st_mtime
    )

def scan_directory(source_dir: str | Path, exclude_patterns: List[str]) -> List[FileFingerprint]:
    """
    Scan a directory, parallel hashing all files.
    """
    base_dir = Path(source_dir).resolve()
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    files_to_scan: List[Path] = []
    
    # We use a simple exclusion logic based on substring matches for now
    for root, _, files in os.walk(base_dir):
        root_path = Path(root)
        # Check exclusion on the relative root path
        rel_root = root_path.relative_to(base_dir).as_posix()
        
        skip_dir = False
        for pattern in exclude_patterns:
            if pattern in rel_root or f"/{pattern}/" in f"/{rel_root}/":
                skip_dir = True
                break
        if skip_dir:
            continue
            
        for f in files:
            file_path = root_path / f
            rel_file = file_path.relative_to(base_dir).as_posix()
            
            skip_file = False
            for pattern in exclude_patterns:
                if pattern in rel_file:
                    skip_file = True
                    break
            
            if not skip_file and file_path.is_file():
                files_to_scan.append(file_path)

    fingerprints: List[FileFingerprint] = []
    
    # Use ThreadPoolExecutor for parallel IO-bound hashing
    max_workers = min(32, (os.cpu_count() or 1) * 4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(scan_file, p, base_dir): p for p in files_to_scan}
        for future in concurrent.futures.as_completed(future_to_path):
            try:
                fp = future.result()
                fingerprints.append(fp)
            except Exception:
                # Log or ignore files we can't read
                pass

    # Sort for deterministic output
    fingerprints.sort(key=lambda x: x.relative_path)
    return fingerprints

def compute_delta(current: List[FileFingerprint], parent: Optional[List[FileFingerprint]]) -> DeltaResult:
    """
    Compare current fingerprints against parent to find added/modified/deleted/unchanged.
    """
    if not parent:
        return DeltaResult(added=current, modified=[], deleted=[], unchanged=[])

    parent_map: Dict[str, FileFingerprint] = {fp.relative_path: fp for fp in parent}
    
    added: List[FileFingerprint] = []
    modified: List[FileFingerprint] = []
    unchanged: List[FileFingerprint] = []
    
    current_paths: Set[str] = set()

    for fp in current:
        current_paths.add(fp.relative_path)
        if fp.relative_path not in parent_map:
            added.append(fp)
        else:
            p_fp = parent_map[fp.relative_path]
            if p_fp.sha256 != fp.sha256:
                modified.append(fp)
            else:
                unchanged.append(fp)

    deleted: List[FileFingerprint] = [
        p_fp for p_path, p_fp in parent_map.items() if p_path not in current_paths
    ]

    return DeltaResult(
        added=added,
        modified=modified,
        deleted=deleted,
        unchanged=unchanged
    )
    
def should_compress(filename: str) -> bool:
    """Smart threshold: skip double-compression for media/archives."""
    ext = Path(filename).suffix.lower()
    return ext not in COMPRESSED_EXTS
