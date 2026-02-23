"""
Rich Terminal UI components.
Provides cyberpunk aesthetics, neon gradients, unicode fallback.
"""
import sys
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from pathlib import Path
from typing import Generator

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich import box
from rich.text import Text
from rich.tree import Tree

# Detect ASCII fallback
try:
    "📦".encode(sys.stdout.encoding if sys.stdout else "utf-8")
    HAS_UNICODE = True
except Exception:
    HAS_UNICODE = False

ICONS: Dict[str, str] = {
    "snapshot": "📦",
    "encrypt": "🔐",
    "compress": "🗜️",
    "upload": "☁️",
    "download": "📥",
    "verify": "🧪",
    "success": "✅",
    "error": "❌",
    "warn": "⚠️",
    "info": "ℹ️",
    "daemon": "👻",
    "doctor": "🩺",
    "plugin": "🧩",
    "delta": "⚡",
    "manifest": "📜",
    "signature": "✍️"
}

ASCII_ICONS: Dict[str, str] = {
    "snapshot": "[PK]",
    "encrypt": "[SEC]",
    "compress": "[CMP]",
    "upload": "[UP]",
    "download": "[DWN]",
    "verify": "[CHK]",
    "success": "[OK]",
    "error": "[ERR]",
    "warn": "[WARN]",
    "info": "[INF]",
    "daemon": "[DMN]",
    "doctor": "[DOC]",
    "plugin": "[PLG]",
    "delta": "[DLT]",
    "manifest": "[MNF]",
    "signature": "[SIG]"
}

def icon(name: str) -> str:
    return ICONS.get(name, "") if HAS_UNICODE else ASCII_ICONS.get(name, "")

console = Console(width=120)
err_console = Console(stderr=True, width=120)

def render_banner() -> None:
    """Render the TermBackup exact ASCII art cyberpunk banner."""
    # Using an exact exact Termbackup ASCII Art
    termbackup_ascii = r"""                                                                               
  _|_|_|_|_|                                  _|                            _|                          
      _|      _|_|    _|  _|_|  _|_|_|  _|_|  _|_|_|      _|_|_|    _|_|_|  _|  _|    _|    _|  _|_|_|  
      _|    _|_|_|_|  _|_|      _|    _|    _|  _|    _|  _|    _|  _|        _|_|      _|    _|  _|    _|
      _|    _|        _|        _|    _|    _|  _|    _|  _|    _|  _|        _|  _|    _|    _|  _|    _|
      _|      _|_|_|  _|        _|    _|    _|  _|_|_|      _|_|_|    _|_|_|  _|    _|    _|_|_|  _|_|_|  
                                                                                                    _|      
                                                                                                    _|      
"""
    banner_text = Text(termbackup_ascii, style="bold color(39)")
    
    i_delta = icon("delta")
    banner_text.append(f"\n[  NEXUS MATRIX ENGINE v2.0 {i_delta} ZERO-TRUST CRYPTO VAULT  ]\n", style="bold cyan")
    banner_text.append("STATUS: ONLINE | ENCRYPTION: AES-256-GCM | SIGNATURE: Ed25519", style="dim magenta")
    
    console.print(Panel(
        banner_text, 
        border_style="cyan", 
        expand=False, 
        title="[bold color(51)]SYSTEM INITIALIZATION[/]",
        title_align="left"
    ))

def render_status(action: str, message: str, style: str = "white") -> None:
    """Print a single line status update."""
    i = icon(action)
    console.print(f"{i} [{style}]{message}[/]")

def render_error(message: str) -> None:
    """Print a styled error panel."""
    i = icon("error")
    err_console.print()
    err_console.print(Panel(Text(message, style="red"), border_style="red", expand=False, title=f"{i} ERROR"))

def render_warning(message: str) -> None:
    """Print a styled warning panel."""
    i = icon("warn")
    console.print()
    console.print(Panel(Text(message, style="yellow"), border_style="yellow", expand=False, title=f"{i} WARNING"))

def confirm(prompt_text: str) -> bool:
    """Interactive confirmation prompt."""
    i = icon("warn")
    return typer.confirm(f"{i} {prompt_text}", default=False)

def render_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    """Render a structured Rich Table with auto-wrap fixes."""
    console.print()
    table = Table(
        title=title, 
        border_style="cyan", 
        header_style="bold magenta", 
        show_lines=True,
        box=box.ROUNDED if HAS_UNICODE else box.ASCII
    )
    
    if headers:
        table.add_column(headers[0], justify="center", no_wrap=True)
        for h in headers[1:]:
            table.add_column(h, justify="left", overflow="fold")
            
    for r in rows:
        table.add_row(*r)
        
    console.print(table)
    console.print()
    
def render_tree_from_paths(root_dir: str, paths: list[str]) -> Tree:
    """Render a Rich tree layout from a list of paths."""
    tree = Tree(f"[bold magenta]{root_dir}[/]")
    
    for relative_path in paths:
        parts = Path(relative_path).parts
        current_node = tree
        for part in parts:
            # This is a simplified linear attachment. For a true tree structure,
            # you'd need to check if a node already exists before adding.
            # For now, we just add the full path as a leaf.
            pass # The original snippet had a pass here, implying simple attachment.
        tree.add(relative_path) # Adding the full relative path as a leaf
        
    return tree

def render_diff(delta: Any) -> None:
    """Render a DeltaResult cleanly to the console."""
    console.print()
    if not any([delta.added, delta.modified, delta.deleted]):
        console.print("[dim italic]No changes detected between snapshot and target directory.[/]")
        return
        
    if delta.added:
        console.print("[bold green]Added:[/]")
        for p in delta.added:
            console.print(f"  [green]+[/] {p}")
    if delta.modified:
        console.print("[bold yellow]Modified:[/]")
        for p in delta.modified:
            console.print(f"  [yellow]~[/] {p}")
    if delta.deleted:
        console.print("[bold red]Deleted:[/]")
        for p in delta.deleted:
            console.print(f"  [red]-[/] {p}")
            
def render_success_summary(title: str, stats: dict) -> None:
    """Render a clean summary panel for operations."""
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    i_success = icon("success")
    console.print(Panel(table, title=f"[bold green]{i_success} {title}[/]", border_style="green", expand=False))

def render_tree(tree: Tree) -> None:
    """Render a Rich tree layout."""
    console.print(Panel(tree, border_style="magenta", title="Tree Preview"))

@contextmanager
def render_progress(title: str = "Operation in progress...") -> Generator[Progress, None, None]:
    """Provide a unified Progress context manager."""
    progress = Progress(
        SpinnerColumn(spinner_name="dots2", style="cyan"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40, style="magenta", complete_style="cyan"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        DownloadColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )
    console.print(f"[{title}]", style="bold cyan")
    with progress:
        yield progress
