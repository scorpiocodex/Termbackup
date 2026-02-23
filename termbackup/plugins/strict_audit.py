"""
Enhanced Audit Logging Plugin.
"""
from typing import Any

from ..audit import AuditLogger
from ..plugins import PluginAPI


class StrictAuditPlugin:
    name = "strict_audit"
    version = "1.0.0"
    
    def __init__(self):
        self.logger = AuditLogger()
    
    def on_snapshot_pre(self, api: PluginAPI) -> None:
        self.logger.log("plugin_strict_audit", action="snapshot_pre", profile=api.profile_name)
        
    def on_snapshot_post(self, api: PluginAPI, meta: Any) -> None:
        self.logger.log("plugin_strict_audit", action="snapshot_post", profile=api.profile_name, snapshot=meta.snapshot_id)
        
    def on_restore_pre(self, api: PluginAPI, snapshot_id: str) -> None:
        self.logger.log("plugin_strict_audit", action="restore_pre", profile=api.profile_name, snapshot=snapshot_id)
        
    def on_restore_post(self, api: PluginAPI, snapshot_id: str) -> None:
        self.logger.log("plugin_strict_audit", action="restore_post", profile=api.profile_name, snapshot=snapshot_id)
