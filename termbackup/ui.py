"""
Rich Terminal UI components.
Provides cyberpunk aesthetics, neon gradients, unicode fallback.
"""
import sys
from contextlib import contextmanager
from typing import Dict, Generator

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

console = Console()
err_console = Console(stderr=True)

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
    
    # Add matrix/sci-fi glitched trailing text
    banner_text.append("\n[  NEXUS MATRIX ENGINE v1.0 ⚡ ZERO-TRUST CRYPTO VAULT  ]\n", style="bold cyan")
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
        expand=True,
        collapse_padding=True
    )
    
    if headers:
        table.add_column(headers[0], justify="center", no_wrap=True)
        for h in headers[1:]:
            table.add_column(h, justify="left", overflow="fold")
            
    for r in rows:
        table.add_row(*r)
        
    console.print(table)
    console.print()
    
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
