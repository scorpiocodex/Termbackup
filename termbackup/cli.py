"""
Command Line Interface entry point using Typer.
"""
import asyncio
import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from .config import get_config_dir, load_profile, list_profiles, save_profile, get_profile_token
from .crypto import (
    derive_key,
    derive_recovery_key,
    encrypt,
    generate_recovery_phrase,
    generate_salt,
    generate_signing_keypair,
)
from .models import Profile
from .ui import (
    confirm,
    console,
    render_banner,
    render_error,
    render_progress,
    render_status,
    render_table,
    render_tree,
    render_warning,
)

app = typer.Typer(
    help=(
        "[bold cyan]TERMBACKUP[/] [dim]v2.0[/]\n\n"
        "⚡ [bold magenta]The Nexus Zero-Trust Matrix Engine[/]\n"
        "A next-generation, professionally hardened, cryptographic vault for your terminal.\n\n"
        "> [italic]Encrypt Reality. Trust Nothing.[/]\n"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich"
)

def run_async(coro):
    """Helper to run async code inside Typer sync commands."""
    return asyncio.run(coro)

@app.command(name="init")
def init(
    name: str = typer.Option(..., "--name", "-n", prompt="Profile Name"),
    repo: str = typer.Option(..., "--repo", "-r", prompt="GitHub Repo (user/repo)"),
    source: str = typer.Option(..., "--source", "-s", prompt="Directory to backup"),
    token: str = typer.Option(..., "--token", "-t", prompt=True, hide_input=True),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, confirmation_prompt=True)
):
    """
    Initialize a new backup profile.
    Generates Master DEK, Recovery Phrase, and Ed25519 signing keys.
    """
    render_banner()
    render_status("info", "Initialize new TermBackup zero-trust profile...")
    
    # 1. Validate Token First
    from .github import GitHubClient
    client = GitHubClient(token)
    
    with console.status("[cyan]Validating GitHub token scopes..."):
        validation = client.validate_token()
        
    if not validation.is_valid:
        render_error(validation.message)
        raise typer.Exit(1)
        
    render_status("success", f"Token validated (Type: {validation.token_type})")
    if validation.needs_warning:
        render_warning(validation.message)
        if not confirm("Proceed despite token warnings?"):
            raise typer.Exit(0)
            
    # 2. Master Key Architecture
    # Master Data Encryption Key (DEK) encrypts everything else.
    master_dek = os.urandom(32)
    
    # Encrypt DEK with user password
    pwd_salt = generate_salt()
    pwd_kek = derive_key(password, pwd_salt)
    master_key_enc = encrypt(master_dek, pwd_kek)
    
    # Encrypt DEK with Recovery Phrase
    phrase = generate_recovery_phrase()
    rec_salt = generate_salt()
    rec_kek = derive_recovery_key(phrase, rec_salt)
    recovery_key_enc = encrypt(master_dek, rec_kek)
    
    # Generate Ed25519 signing keypair
    priv, pub = generate_signing_keypair()
    pub_b64 = base64.b64encode(pub).decode("ascii")
    # Store private key encrypted by DEK
    priv_enc = encrypt(priv, master_dek)
    priv_enc_b64 = base64.b64encode(priv_enc).decode("ascii")
    
    profile = Profile(
        name=name,
        source_dir=str(Path(source).resolve()),
        repo=repo,
        token_ref=f"termbackup_{name}_token",
        created_at=datetime.now(timezone.utc),
        master_key_enc=base64.b64encode(master_key_enc).decode("ascii"),
        master_key_salt=base64.b64encode(pwd_salt).decode("ascii"),
        recovery_key_enc=base64.b64encode(recovery_key_enc).decode("ascii"),
        recovery_key_salt=base64.b64encode(rec_salt).decode("ascii"),
        signing_public_key=pub_b64,
        signing_private_key_enc=priv_enc_b64
    )
    
    save_profile(profile, token)
    
    render_status("success", f"Profile '{name}' saved successfully.")
    
    # Display Recovery Phrase safely
    render_warning("CRITICAL: SAVE YOUR RECOVERY PHRASE. If you lose your password AND this phrase, YOUR DATA IS GONE.")
    console.print(Panel(f"[bold red]{phrase}[/]", title="Recovery Phrase", border_style="red"))
    
    confirm("I have written down the 24-word recovery phrase securely. Continue?")

from .github import GitHubClient
from .manifest import create_initial_manifest
from .snapshot import create_snapshot
from .restore import preview_tree, restore_snapshot, diff_snapshot

@app.command(name="snapshot")
def create_snapshot_cmd(
    name: str = typer.Argument(..., help="Profile to snapshot"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
):
    """
    Create a new zero-trust snapshot and upload it.
    """
    render_banner()
    try:
        profile = load_profile(name)
        render_status("snapshot", f"Starting snapshot for {name} on {profile.source_dir}")
        
        token = get_profile_token(profile)
        if not token:
            raise typer.Exit("Token not found in keyring/config. Please run init again.")
            
        client = GitHubClient(token)
        
        with render_progress("Creating zero-trust snapshot...") as progress:
            tbk_path, meta = create_snapshot(profile, password)
            
        render_status("encrypt", f"Snapshot {meta.snapshot_id} created and encrypted locally.")
        
        with render_progress("Uploading to GitHub..."):
            # Update manifest
            manifest = client.download_manifest(profile.repo)
            if not manifest:
                manifest = create_initial_manifest()
            
            # Read tbk
            content = tbk_path.read_bytes()
            
            # Upload snapshot
            client.upload_file(profile.repo, f"snapshots/{tbk_path.name}", content, f"Add snapshot {meta.snapshot_id}")
            
            # Update manifest
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
            
        tbk_path.unlink()  # Cleanup local
        render_status("success", f"Snapshot {meta.snapshot_id} securely uploaded to {profile.repo}.")
        
    except Exception as e:
        render_error(str(e))
        raise typer.Exit(1)
        
@app.command(name="restore")
def run_restore(
    name: str = typer.Argument(..., help="Profile to restore"),
    snapshot_id: str = typer.Argument(..., help="Snapshot ID to restore"),
    target: str = typer.Option(..., "--target", "-t", help="Directory to extract to"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files")
):
    """Restore a snapshot to a target directory."""
    render_banner()
    from pathlib import Path
    try:
        profile = load_profile(name)
        token = get_profile_token(profile)
        client = GitHubClient(token)
        
        target_dir = Path(target).resolve()
        
        with render_progress(f"Downloading snapshot {snapshot_id}..."):
            manifest = client.download_manifest(profile.repo)
            if not manifest:
                raise Exception("Manifest not found on GitHub. Cannot find snapshot.")
            
            # Find entry
            entry = next((e for e in manifest.entries if e.snapshot_id == snapshot_id), None)
            if not entry:
                raise Exception(f"Snapshot {snapshot_id} not found in manifest.")
                
            content = client.download_file(profile.repo, f"snapshots/{entry.filename}")
            
            import tempfile
            temp_tbk = Path(tempfile.gettempdir()) / entry.filename
            temp_tbk.write_bytes(content)
            
        with render_progress("Decrypting and extracting..."):
            restore_snapshot(temp_tbk, profile, password, target_dir, overwrite=overwrite)
            
        temp_tbk.unlink()
        render_status("success", f"Successfully restored to {target_dir}")
        
    except Exception as e:
        render_error(str(e))
        raise typer.Exit(1)

@app.command(name="doctor")
def run_doctor():
    """Run the 12-point diagnostic suite."""
    render_banner()
    from .doctor import run_diagnostics
    with render_progress("Running diagnostic checks..."):
        results = run_diagnostics()
        
    rows = []
    for r in results:
        status_text = "[bold green]PASS[/]" if r.status == "pass" else "[bold yellow]WARN[/]" if r.status == "warn" else "[bold red]FAIL[/]"
        rows.append([status_text, r.name, r.detail])
        
    render_table("Nexus Doctor Diagnostics", ["Status", "Check", "Details"], rows)

@app.command(name="daemon")
def run_daemon(
    name: str = typer.Argument(..., help="Profile name"),
    interval: int = typer.Option(60, "--interval", "-i", help="Interval in minutes"),
    generate: bool = typer.Option(False, "--generate", help="Just generate service file instead of running")
):
    """Ghost Protocol: Run background backups."""
    from .daemon import DaemonProcess, generate_systemd_unit, generate_windows_task_xml
    import sys
    
    if generate:
        if sys.platform == "win32":
            xml = generate_windows_task_xml(name, interval)
            console.print(Panel(xml, title="Windows Task Scheduler XML", border_style="cyan"))
        else:
            unit = generate_systemd_unit(name, interval)
            console.print(Panel(unit, title="Systemd Unit File", border_style="cyan"))
        return
        
    render_banner()
    render_status("daemon", f"Starting Ghost Protocol for {name} every {interval}m...")
    try:
        daemon = DaemonProcess(name, interval)
        daemon.start()
    except Exception as e:
        render_error(str(e))
        raise typer.Exit(1)

@app.command(name="list")
def list_snapshots_cmd(name: str = typer.Argument(..., help="Profile to list snapshots for")):
    """List snapshots available on GitHub."""
    render_banner()
    try:
        profile = load_profile(name)
        token = get_profile_token(profile)
        client = GitHubClient(token)
        
        with render_progress("Fetching manifest..."):
            manifest = client.download_manifest(profile.repo)
            
        if not manifest or not manifest.entries:
            render_status("info", "No snapshots found.")
            return
            
        rows = []
        for e in manifest.entries:
            rows.append([e.snapshot_id, e.filename, f"{e.size} B", e.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")])
            
        render_table(f"Snapshots for {name}", ["ID", "Filename", "Size", "Uploaded At"], rows)
        
    except Exception as e:
        render_error(str(e))
        raise typer.Exit(1)

@app.command(name="audit")
def show_audit(last_n: int = typer.Option(50, "--last", "-n", help="Number of recent events to show")):
    """Show recent audit logs."""
    render_banner()
    from .audit import get_audit_log
    events = get_audit_log(last_n)
    if not events:
        render_status("info", "No audit events found.")
        return
        
    rows = []
    for e in events:
        rows.append([e["timestamp"], e["event"], str(e["details"])])
        
    render_table("Audit Log", ["Timestamp", "Event", "Details"], rows)

@app.command(name="plugin")
def plugin_list():
    """List loaded plugins."""
    render_banner()
    from .plugins import load_plugins
    plugins = load_plugins()
    if not plugins:
        render_status("plugin", "No active plugins found.")
    else:
        for p in plugins:
            typer.echo(f"- {p.name} (v{p.version}): {p.description}")

@app.command(name="profiles")
def list_profiles_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format.")
):
    """List all configured Termbackup profiles."""
    from .config import list_profiles, load_profile
    from .ui import console
    import json
    
    profiles = list_profiles()
    if json_output:
        profiles_data = []
        for p in profiles:
            try:
                prof = load_profile(p)
                profiles_data.append({"name": prof.name, "repo": prof.repo, "source_dir": prof.source_dir})
            except Exception:
                pass
        print(json.dumps(profiles_data, indent=2))
        return

    if not profiles:
        typer.echo("No profiles found.")
        return
        
    from .ui import render_table
    
    rows = []
    for p in profiles:
        try:
            prof = load_profile(p)
            rows.append([prof.name, prof.repo, prof.source_dir])
        except Exception as e:
            err_msg = str(e).split('\n')[0]
            if len(err_msg) > 60: err_msg = err_msg[:57] + "..."
            rows.append([p, "[red]ERROR[/]", err_msg])
            
    render_table("Configured Profiles", ["Name", "Repository", "Source Directory"], rows)


@app.command(name="delete")
def delete_profile_cmd(
    name: str = typer.Argument(..., help="Profile to delete")
):
    """Delete a profile and its securely stored token."""
    from .config import delete_profile
    from .ui import render_status
    delete_profile(name)
    render_status("delete", f"Profile '{name}' deleted.")


@app.command(name="version")
def version_cmd():
    """Display Termbackup version information."""
    from .ui import console
    from rich.panel import Panel
    v = "2.0.0"
    console.print(Panel(f"[bold cyan]TERMBACKUP[/] v{v}\n[dim]The Nexus Zero-Trust Matrix Engine[/]", border_style="cyan", expand=False))


@app.command(name="diff")
def diff_cmd(
    profile_name: str = typer.Argument(..., help="Profile name"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Master password"),
    snapshot_id: str = typer.Option(..., "--snapshot", "-s", help="Snapshot ID to compare against")
):
    """Compare a snapshot with the current filesystem."""
    from .config import load_profile, get_profile_token
    from .github import GitHubClient
    from .restore import diff_snapshot
    from .ui import render_progress, render_error, render_diff
    import tempfile
    from pathlib import Path
    
    profile = load_profile(profile_name)
    token = get_profile_token(profile)
    if not token:
        render_error("Token not found. Please provide it via TERMBACKUP_TOKEN or re-init.")
        raise typer.Exit(1)
        
    with GitHubClient(token) as client:
        try:
            with render_progress(f"Downloading snapshot {snapshot_id}...") as prog:
                tbk_data = client.download_file(profile.repo, f"snapshots/{snapshot_id}.tbk")
        except Exception as e:
            render_error(f"Failed to download snapshot: {e}")
            raise typer.Exit(1)
            
    with tempfile.TemporaryDirectory() as td:
        tbk_path = Path(td) / f"{snapshot_id}.tbk"
        tbk_path.write_bytes(tbk_data)
        
        with render_progress("Computing cryptographic delta...") as prog:
            delta = diff_snapshot(tbk_path, profile, password, Path(profile.source_dir))
            
    render_diff(delta)


@app.command(name="delete-snapshot")
def delete_snapshot_cmd(
    profile_name: str = typer.Argument(..., help="Profile name"),
    snapshot_id: str = typer.Argument(..., help="Snapshot ID to delete")
):
    """Delete a specific snapshot from the remote vault."""
    from .config import load_profile, get_profile_token
    from .github import GitHubClient
    from .ui import render_status, render_error, render_progress
    
    profile = load_profile(profile_name)
    token = get_profile_token(profile)
    if not token:
        render_error("Token not found.")
        raise typer.Exit(1)
        
    with GitHubClient(token) as client:
        with render_progress(f"Annihilating snapshot {snapshot_id}...") as prog:
            try:
                client.delete_file(profile.repo, f"snapshots/{snapshot_id}.tbk", f"Delete snapshot {snapshot_id}")
            except Exception as e:
                render_error(f"Deletion failed: {e}")
                raise typer.Exit(1)
    render_status("delete", f"Snapshot {snapshot_id} successfully purged from vault.")

if __name__ == "__main__":
    app()
