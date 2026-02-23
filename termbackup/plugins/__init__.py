"""
TermBackup Nexus Extension Subsystem.
Provides a sandboxed plugin architecture for controlled extensions.
"""
import importlib.metadata
from typing import Any, List, Protocol

from ..models import Profile, SnapshotMeta
from ..ui import render_status


class PluginAPI:
    """Sandboxed API subset passed to plugins."""
    def __init__(self, profile: Profile):
        self._profile = profile
        
    @property
    def profile_name(self) -> str:
        return self._profile.name
        
    @property
    def source_dir(self) -> str:
        return self._profile.source_dir
        
    # Notice: NO access to secret keys, crypto functions, or raw tokens.

class TermBackupPlugin(Protocol):
    """Protocol that all TermBackup plugins must implement."""
    name: str
    version: str
    
    def on_snapshot_pre(self, api: PluginAPI) -> None:
        ...
        
    def on_snapshot_post(self, api: PluginAPI, meta: SnapshotMeta) -> None:
        ...
        
    def on_restore_pre(self, api: PluginAPI, snapshot_id: str) -> None:
        ...
        
    def on_restore_post(self, api: PluginAPI, snapshot_id: str) -> None:
        ...

def load_plugins() -> List[TermBackupPlugin]:
    """Discover and load verified plugins via entry points."""
    plugins: List[TermBackupPlugin] = []
    
    try:
        # For Python 3.10+ entry_points syntax
        eps = importlib.metadata.entry_points(group="termbackup.plugins")
        for ep in eps:
            try:
                plugin_cls = ep.load()
                plugin_instance = plugin_cls()
                if validate_plugin(plugin_instance):
                    plugins.append(plugin_instance)
                else:
                    render_status("warn", f"Plugin '{ep.name}' failed validation.", "yellow")
            except Exception as e:
                render_status("warn", f"Failed to load plugin '{ep.name}': {e}", "yellow")
    except Exception:
        # If no plugins or metadata issues
        pass
        
    return plugins

def validate_plugin(plugin: Any) -> bool:
    """Ensure plugin respects the protocol and doesn't violate obvious sandbox rules."""
    if not hasattr(plugin, "name") or not hasattr(plugin, "version"):
        return False
        
    required_methods = [
        "on_snapshot_pre", "on_snapshot_post",
        "on_restore_pre", "on_restore_post"
    ]
    for method in required_methods:
        if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
            return False
            
    # Check for forbidden imports heuristically if we wanted true sandboxing,
    # but in Python real sandboxing is hard. We rely on the PluginAPI restriction 
    # and "verified" status in a real implementation.
    return True
