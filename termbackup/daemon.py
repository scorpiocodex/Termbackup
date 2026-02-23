"""
Ghost Protocol: Background scheduler and systemd/schtasks integration for TermBackup.
"""
import os
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

from .config import get_config_dir
from .utils import setup_signal_handlers


class DaemonProcess:
    def __init__(self, profile_name: str, interval_minutes: int):
        self.profile = profile_name
        self.interval = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.pid_file = get_config_dir() / f"daemon_{profile_name}.pid"

    def is_running(self) -> bool:
        """Check if daemon is already running via PID file."""
        if not self.pid_file.exists():
            return False
        try:
            pid = int(self.pid_file.read_text())
            # Cross-platform basic check
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                process = kernel32.OpenProcess(0x1000, 0, pid)
                if process:
                    kernel32.CloseHandle(process)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            self.pid_file.unlink(missing_ok=True)
            return False

    def job(self) -> None:
        """The actual backup job."""
        from .audit import AuditLogger
        logger = AuditLogger()
        logger.log("daemon_job_start", profile=self.profile)
        try:
            password = os.environ.get("TERMBACKUP_PASSWORD")
            if not password:
                raise ValueError("TERMBACKUP_PASSWORD environment variable not set. Ghost Protocol cannot decrypt DEK.")
                
            from .config import load_profile, get_profile_token
            from .snapshot import create_snapshot
            from .github import GitHubClient
            from datetime import datetime, timezone
            
            profile = load_profile(self.profile)
            token = get_profile_token(profile)
            if not token:
                raise ValueError("Token not found in keyring.")
                
            with GitHubClient(token) as client:
                tbk_path, meta = create_snapshot(profile, password)
                content = tbk_path.read_bytes()
                
                manifest = client.download_manifest(profile.repo)
                if not manifest:
                    from .manifest import create_initial_manifest
                    manifest = create_initial_manifest()
                    
                client.upload_file(profile.repo, f"snapshots/{tbk_path.name}", content, f"Ghost Protocol Auto-backup {meta.snapshot_id}")
                
                from .manifest import append_entry
                from .models import ManifestEntry
                from .crypto import compute_sha256
                
                entry = ManifestEntry(
                    snapshot_id=meta.snapshot_id,
                    filename=tbk_path.name,
                    sha256=compute_sha256(content),
                    size=meta.total_size,
                    uploaded_at=datetime.now(timezone.utc)
                )
                manifest = append_entry(manifest, entry)
                client.upload_manifest(profile.repo, manifest)
                
            tbk_path.unlink(missing_ok=True)
            logger.log("daemon_job_end", profile=self.profile, status="success", snapshot_id=meta.snapshot_id)
        except Exception as e:
            logger.log("daemon_job_end", profile=self.profile, status="failed", error=str(e))

    def start(self) -> None:
        if self.is_running():
            raise RuntimeError(f"Daemon for profile '{self.profile}' is already running.")
            
        self.pid_file.write_text(str(os.getpid()))
        
        self.scheduler.add_job(self.job, 'interval', minutes=self.interval)
        self.scheduler.start()
        
        setup_signal_handlers(self.stop)
        
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            pass

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.pid_file.unlink(missing_ok=True)


def generate_systemd_unit(profile_name: str, interval: int) -> str:
    """Generate systemd .service content."""
    python_exec = sys.executable
    termbackup_cmd = f"{python_exec} -m termbackup.cli daemon {profile_name} --interval {interval}"
    
    return f"""[Unit]
Description=TermBackup Ghost Protocol ({profile_name})
After=network.target

[Service]
Type=simple
ExecStart={termbackup_cmd}
Restart=on-failure
RestartSec=30
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=termbackup-{profile_name}

[Install]
WantedBy=default.target
"""

def generate_windows_task_xml(profile_name: str, interval: int) -> str:
    """Generate an XML definition for Windows Task Scheduler (schtasks.exe)."""
    python_exec = sys.executable
    termbackup_cmd = f"-m termbackup.cli daemon {profile_name} --interval {interval}"
    
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>TermBackup Ghost Protocol for profile: {profile_name}</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT{interval}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2020-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exec}</Command>
      <Arguments>{termbackup_cmd}</Arguments>
    </Exec>
  </Actions>
</Task>"""
    return xml
