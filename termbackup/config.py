"""
Configuration, profile management, and token storage for TermBackup.
"""
import json
import os
import stat
import sys
from pathlib import Path
from typing import List, Optional

import keyring

from .errors import ProfileNotFoundError, ProfileValidationError
from .models import Profile

APP_NAME = "termbackup"

def get_config_dir() -> Path:
    """Returns the platform-specific configuration directory."""
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            base_dir = Path(appdata)
        else:
            base_dir = Path.home() / "AppData" / "Roaming"
    else:
        # XDG Base Directory specification
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            base_dir = Path(xdg_config)
        else:
            base_dir = Path.home() / ".config"
    
    config_dir = base_dir / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def list_profiles() -> List[str]:
    """List all available profile names."""
    config_dir = get_config_dir()
    profiles = []
    for fp in config_dir.glob("*.json"):
        if fp.is_file() and not fp.name.startswith("."):
            profiles.append(fp.stem)
    return sorted(profiles)

def get_profile_path(name: str) -> Path:
    """Return the filesystem path for a specific profile name."""
    return get_config_dir() / f"{name}.json"

def apply_secure_permissions(path: Path) -> None:
    """Apply chmod 600 equivalent permissions to a file."""
    if sys.platform != "win32":
        # Owner read/write only
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

def save_profile(profile: Profile, token: str) -> None:
    """Save a profile to disk and its token securely."""
    # Attempt to store token in the keyring. Do not store in config to avoid plaintext tokens.
    try:
        keyring.set_password(APP_NAME, profile.token_ref, token)
    except Exception:
        # If keyring fails (e.g. headless linux), fallback to storing it encrypted would be ideal, 
        # but per spec, we only keep it out of the JSON. If keyring fails, the user must provide it or configure a working keyring.
        pass

    path = get_profile_path(profile.name)
    with path.open("w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))
    
    apply_secure_permissions(path)

def load_profile(name: str) -> Profile:
    """Load a profile by name from disk."""
    path = get_profile_path(name)
    if not path.exists():
        raise ProfileNotFoundError(f"Profile '{name}' does not exist.")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return Profile(**data)
    except Exception as e:
        raise ProfileValidationError(f"Failed to load profile '{name}': {e}") from e

def get_profile_token(profile: Profile) -> Optional[str]:
    """Retrieve the token for a given profile."""
    try:
        return keyring.get_password(APP_NAME, profile.token_ref)
    except Exception:
        return None

def delete_profile(name: str) -> None:
    """Delete a profile and its associated token."""
    try:
        profile = load_profile(name)
        try:
            keyring.delete_password(APP_NAME, profile.token_ref)
        except Exception:
            pass  # Maybe it wasn't there
    except ProfileNotFoundError:
        pass
    
    path = get_profile_path(name)
    if path.exists():
        path.unlink()
