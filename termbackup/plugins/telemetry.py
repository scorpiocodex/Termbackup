"""
Telemetry Plugin (Stub)
"""
from typing import Any

from ..plugins import PluginAPI


class TelemetryPlugin:
    name = "telemetry"
    version = "1.0.0"
    
    def on_snapshot_pre(self, api: PluginAPI) -> None: pass
    def on_snapshot_post(self, api: PluginAPI, meta: Any) -> None: pass
    def on_restore_pre(self, api: PluginAPI, snapshot_id: str) -> None: pass
    def on_restore_post(self, api: PluginAPI, snapshot_id: str) -> None: pass
