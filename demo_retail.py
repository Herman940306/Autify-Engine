"""
Autify Engine V1 — Retail Module Live Demo
───────────────────────────────────────────
A cinematic terminal demonstration using Rich.
Run:  python demo_retail.py
"""

import time
import sys
from datetime import datetime, timedelta

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.live import Live
    from rich.layout import Layout
    from rich.markdown import Markdown
    from rich import box
except ImportError:
    print("This demo requires the 'rich' library.")
    print("Install it with:  pip install rich")
    sys.exit(1)

console = Console(width=110)

# ── Timing helpers ────────────────────────────────────────────────────
def pause(seconds: float = 0.6):
    time.sleep(seconds)

def typewriter(text: str, style: str = "", delay: float = 0.018):
    """Print text character-by-character for dramatic effect."""
    for ch in text:
        console.print(ch, end="", style=style, highlight=False)
        time.sleep(delay)
    console.print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 0 — SPLASH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_splash():
    console.clear()
    banner = r"""
     █████╗ ██╗   ██╗████████╗██╗███████╗██╗   ██╗
    ██╔══██╗██║   ██║╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
    ███████║██║   ██║   ██║   ██║█████╗   ╚████╔╝
    ██╔══██║██║   ██║   ██║   ██║██╔══╝    ╚██╔╝
    ██║  ██║╚██████╔╝   ██║   ██║██║        ██║
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝
    """
    console.print(banner, style="bold cyan", justify="center")
    console.print(
        Align.center(
            Text("C O R E   E N G I N E   V 1 . 0 . 0", style="bold white on blue")
        )
    )
    console.print()
    console.print(Align.center(Text("Zero-Cloud · Local-First · Human-In-The-Loop", style="dim italic")))
    console.print()
    pause(1.5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 1 — BOOT SEQUENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_boot():
    console.print(Rule("[bold yellow]PHASE 1 — SYSTEM INITIALIZATION[/]"))
    console.print()

    boot_steps = [
        ("Loading core configuration",          "core.config",       0.4),
        ("Initializing SQLite database",         "database.database", 0.5),
        ("Binding to port 18080",                "api.main",          0.3),
        ("Starting local LLM bridge (Ollama)",   "llm.orchestrator",  0.6),
        ("Registering template engine",          "templates/*",       0.3),
        ("Loading parsers (CSV · PDF · XLSX)",   "parsers.parser",    0.4),
        ("Mounting analysis engine",             "analysis.engine",   0.3),
    ]

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[dim]{task.fields[module]}"),
        console=console,
        transient=False,
    ) as progress:
        for desc, module, dur in boot_steps:
            task = progress.add_task(desc, total=100, module=module)
            steps = 20
            for _ in range(steps):
                time.sleep(dur / steps)
                progress.advance(task, 100 / steps)

    console.print()

    # License validation
    console.print("  [bold cyan]▸[/] Validating hardware-bound license …", end=" ")
    pause(0.8)
    console.print("[bold green]✔ LICENSE VALID[/]")
    fp_hash = "a3f7c1…d942e8"
    console.print(f"    [dim]Fingerprint: SHA-256({fp_hash})  ·  Expires: 2027-03-01[/]")
    console.print()

    # 10 LLM Laws
    console.print("  [bold cyan]▸[/] Enforcing [bold]10 LLM Laws[/] …", end=" ")
    pause(0.5)
    console.print("[bold green]✔ ALL LAWS ACTIVE[/]")
    laws_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2), expand=False)
    laws_table.add_column(style="dim", width=4)
    laws_table.add_column(style="white")
    laws = [
        "All outputs are DRAFTS — never auto-executed.",
        "Human approval required before any action.",
        "No data leaves the local machine (Zero-Cloud).",
        "All inputs are validated and sanitized.",
        "Deterministic analysis — no randomness in KPIs.",
        "Append-only audit logs — immutable history.",
        "Hardware-bound licensing — one device per key.",
        "No PII in LLM prompts — template variables only.",
        "True Data Only — failures return errors, never templates.",
        "All drafts carry draft_flag=True until human approval.",
    ]
    for i, law in enumerate(laws, 1):
        laws_table.add_row(f"§{i}", law)
    console.print(laws_table)
    console.print()

    # Module loading
    console.print("  [bold cyan]▸[/] Loading module: [bold magenta]Retail Operations[/] …", end=" ")
    pause(0.7)
    console.print("[bold green]✔ LOADED[/]")
    console.print("    [dim]Templates: retail_pos_reporting · retail_inventory_alert[/]")
    console.print()
    pause(0.5)
    console.print(
        Panel(
            Align.center(Text("AUTIFY ENGINE READY", style="bold green")),
            border_style="green",
            padding=(0, 4),
        )
    )
    pause(1.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 2 — NATURAL LANGUAGE INPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_input():
    console.print()
    console.print(Rule("[bold yellow]PHASE 2 — NATURAL LANGUAGE QUERY[/]"))
    console.print()

    query = "Check yesterday's sales and draft a restock email for low-stock items."

    console.print("  [bold cyan]OPERATOR >[/] ", end="")
    typewriter(query, style="bold white", delay=0.035)
    console.print()
    pause(0.5)

    # Intent decomposition
    console.print("  [bold cyan]▸[/] Intent Decomposition (local LLM) …")
    pause(0.6)

    intent_table = Table(
        title="Extracted Intents",
        box=box.ROUNDED,
        title_style="bold",
        border_style="cyan",
        show_lines=True,
    )
    intent_table.add_column("#", style="bold", width=3, justify="center")
    intent_table.add_column("Intent", style="green")
    intent_table.add_column("Tool Chain", style="yellow")
    intent_table.add_column("Mode", style="magenta")

    intent_table.add_row("1", "Retrieve yesterday's sales data", "SQL → Analysis Engine", "READ")
    intent_table.add_row("2", "Identify low-stock SKUs", "Inventory Analysis", "READ")
    intent_table.add_row("3", "Draft restock notification email", "Template Engine → LLM", "[bold]DRAFT ONLY[/]")

    console.print(intent_table)
    console.print()
    pause(1.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 3 — TOOL-CALLING / PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_tool_calling():
    console.print(Rule("[bold yellow]PHASE 3 — AGENTIC TOOL PIPELINE[/]"))
    console.print()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # ── Step 3a: SQL Query ────────────────────────────────────────────
    console.print("  [bold white on blue] STEP 1/3 [/]  [bold]SQL Querying Local Database[/]")
    console.print()
    sql = f"SELECT sku, product_name, units_sold, revenue\n    FROM   pos_transactions\n    WHERE  sale_date = '{yesterday}'\n    ORDER  BY units_sold DESC;"
    console.print(Panel(sql, title="[bold]Generated SQL[/]", border_style="blue", padding=(0, 2)))
    pause(0.5)

    with Progress(
        SpinnerColumn("dots12"),
        TextColumn("[bold]{task.description}"),
        console=console,
        transient=True,
    ) as p:
        t = p.add_task("Executing against SQLite (data/db.sqlite) …", total=None)
        time.sleep(1.2)

    # Simulated result set
    sales_table = Table(
        title=f"POS Results — {yesterday}",
        box=box.SIMPLE_HEAVY,
        title_style="bold",
        border_style="white",
    )
    sales_table.add_column("SKU", style="cyan")
    sales_table.add_column("Product", style="white")
    sales_table.add_column("Units Sold", justify="right", style="green")
    sales_table.add_column("Revenue (R)", justify="right", style="green")
    sales_table.add_column("Stock Left", justify="right", style="red")

    rows = [
        ("RTL-4521", "Premium Brake Pads (Set)",     "134", "52,130.00",  "8"),
        ("RTL-8833", "Synthetic Engine Oil 5W-30",    "97",  "24,250.00",  "3"),
        ("RTL-1107", "LED Headlight Bulb H7",        "82",  "18,040.00",  "41"),
        ("RTL-3390", "Cabin Air Filter (Universal)",  "64",  "7,680.00",   "5"),
        ("RTL-5502", "Windshield Wiper Blades 22\"",  "51",  "8,670.00",   "62"),
        ("RTL-9012", "Spark Plug Set (Iridium)",      "48",  "14,400.00",  "2"),
        ("RTL-6678", "Transmission Fluid ATF+4",      "39",  "9,750.00",   "22"),
    ]
    for row in rows:
        stock_style = "bold red" if int(row[4]) < 10 else ""
        sales_table.add_row(row[0], row[1], row[2], row[3], Text(row[4], style=stock_style))

    console.print(sales_table)
    console.print(f"  [dim]↳ 7 rows · query time: 12 ms · source: local SQLite[/]")
    console.print()
    pause(1.0)

    # ── Step 3b: Analysis Engine ──────────────────────────────────────
    console.print("  [bold white on magenta] STEP 2/3 [/]  [bold]Deterministic Inventory Analysis[/]")
    console.print()

    with Progress(
        SpinnerColumn("dots12"),
        TextColumn("[bold]{task.description}"),
        console=console,
        transient=True,
    ) as p:
        t = p.add_task("Running analysis.engine.run_analysis() …", total=None)
        time.sleep(1.0)

    kpi_cards = [
        Panel(
            Align.center(Text("R135,920", style="bold green") + Text("\nTotal Revenue", style="dim")),
            border_style="green", width=22,
        ),
        Panel(
            Align.center(Text("515", style="bold green") + Text("\nUnits Sold", style="dim")),
            border_style="green", width=22,
        ),
        Panel(
            Align.center(Text("R263.92", style="bold green") + Text("\nAvg Basket", style="dim")),
            border_style="green", width=22,
        ),
        Panel(
            Align.center(Text("3 ⚠", style="bold red") + Text("\nLow-Stock SKUs", style="dim")),
            border_style="red", width=22,
        ),
    ]
    console.print(Columns(kpi_cards, padding=(0, 1)))
    console.print()

    # Anomalies
    anom_table = Table(
        title="⚠  Anomalies Detected (Z-Score > 3σ)",
        box=box.ROUNDED,
        title_style="bold red",
        border_style="red",
    )
    anom_table.add_column("SKU", style="cyan")
    anom_table.add_column("Product", style="white")
    anom_table.add_column("Stock", justify="right", style="bold red")
    anom_table.add_column("Reorder Point", justify="right", style="yellow")
    anom_table.add_column("Status")

    anom_table.add_row("RTL-9012", "Spark Plug Set (Iridium)",   "2",  "15", Text("▼ CRITICAL", style="bold red"))
    anom_table.add_row("RTL-8833", "Synthetic Engine Oil 5W-30", "3",  "20", Text("▼ CRITICAL", style="bold red"))
    anom_table.add_row("RTL-3390", "Cabin Air Filter",           "5",  "12", Text("▼ LOW",      style="bold yellow"))
    anom_table.add_row("RTL-4521", "Premium Brake Pads (Set)",   "8",  "10", Text("▼ LOW",      style="bold yellow"))

    console.print(anom_table)
    console.print()
    pause(1.0)

    # ── Step 3c: Draft Mode Gate ──────────────────────────────────────
    console.print("  [bold white on red] STEP 3/3 [/]  [bold]Logic Check — Draft-Only Mode[/]")
    console.print()

    checks = [
        ("config.DRAFT_ONLY == True",            True),
        ("Law §1: Output flagged as DRAFT",      True),
        ("Law §2: Human approval gate attached",  True),
        ("Law §3: Zero external API calls",       True),
        ("Law §8: No PII in LLM prompt",          True),
    ]
    for label, ok in checks:
        mark = "[bold green]✔ PASS[/]" if ok else "[bold red]✘ FAIL[/]"
        console.print(f"    {mark}  {label}")
        pause(0.25)

    console.print()
    pause(0.5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 4 — DRAFT OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_output():
    console.print(Rule("[bold yellow]PHASE 4 — GENERATED DRAFT[/]"))
    console.print()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")

    draft_body = f"""[bold]To:[/]       procurement@company.local
[bold]Subject:[/]  ⚠ Restock Alert — {yesterday} — 4 SKUs Below Threshold
[bold]Priority:[/] [bold red]HIGH[/]

Dear Procurement Team,

Following yesterday's sales analysis, the Autify Engine has identified
[bold]4 SKUs[/] that have fallen below their reorder points:

  [bold red]▼ CRITICAL[/]
    • RTL-9012  Spark Plug Set (Iridium)    — [bold]2[/] remaining  (reorder: 15)
    • RTL-8833  Synthetic Engine Oil 5W-30  — [bold]3[/] remaining  (reorder: 20)

  [bold yellow]▼ LOW[/]
    • RTL-3390  Cabin Air Filter            — [bold]5[/] remaining  (reorder: 12)
    • RTL-4521  Premium Brake Pads (Set)    — [bold]8[/] remaining  (reorder: 10)

[bold]Recommended Action:[/]
  Place purchase orders for above SKUs at standard volumes.
  Yesterday's total revenue: [bold green]R135,920.00[/] across 515 units.

Regards,
Autify Engine V1 — Retail Operations Module

[dim italic]This draft was generated by a local LLM (llama3.2:3b) using
template: retail_inventory_alert v1.0.0
No data was transmitted to any external service.[/]"""

    draft_panel = Panel(
        draft_body,
        title="[bold white on red] ◆  RESTOCK DRAFT  ◆ [/]",
        subtitle="[bold white on red] ⏳ PENDING HUMAN APPROVAL [/]",
        border_style="red",
        padding=(1, 3),
    )
    console.print(draft_panel)
    console.print()

    # Draft metadata
    meta = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    meta.add_column(style="bold cyan", width=20)
    meta.add_column(style="white")
    meta.add_row("Draft ID",        "DRF-20260311-0042")
    meta.add_row("draft_flag",      "[bold green]True[/]  (immutable until approved)")
    meta.add_row("Template",        "retail_inventory_alert v1.0.0")
    meta.add_row("LLM Model",       "llama3.2:3b (local, port 11434)")
    meta.add_row("Generated At",    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    meta.add_row("Approval Status", "[bold yellow]⏳ PENDING[/]")
    console.print(meta)
    console.print()
    pause(1.5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 5 — SECURITY & PRIVACY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_security():
    console.print(Rule("[bold yellow]PHASE 5 — SECURITY & PRIVACY AUDIT[/]"))
    console.print()

    # Network monitor
    console.print("  [bold cyan]▸[/] Network Activity Monitor …")
    pause(0.5)

    net_table = Table(
        box=box.ROUNDED,
        border_style="green",
        title="Network Connections During Session",
        title_style="bold",
    )
    net_table.add_column("Destination", style="white")
    net_table.add_column("Port", justify="right")
    net_table.add_column("Bytes Sent", justify="right", style="green")
    net_table.add_column("Protocol")
    net_table.add_column("Purpose", style="dim")

    net_table.add_row("localhost", "11434", "4,216 B", "HTTP", "LLM inference (local Ollama)")
    net_table.add_row("localhost", "18080", "1,892 B", "HTTP", "API ↔ Dashboard (loopback)")
    net_table.add_row("[bold green]0.0.0.0 (external)[/]", "—", "[bold green]0 B[/]", "—", "[bold green]NONE[/]")

    console.print(net_table)
    console.print()

    # Privacy log
    privacy_log = Table(
        box=box.HEAVY,
        border_style="green",
        title="🔒  PRIVACY LOG",
        title_style="bold green",
        show_lines=True,
    )
    privacy_log.add_column("Check", style="white", width=40)
    privacy_log.add_column("Result", style="bold green", justify="center", width=16)
    privacy_log.add_column("Evidence", style="dim", width=38)

    privacy_log.add_row(
        "External API calls",
        "✔  0 calls",
        "No outbound connections detected",
    )
    privacy_log.add_row(
        "Bytes transmitted externally",
        "✔  0 bytes",
        "All traffic on 127.0.0.1 loopback",
    )
    privacy_log.add_row(
        "PII in LLM prompts",
        "✔  Clean",
        "Template variables only (Law §8)",
    )
    privacy_log.add_row(
        "Telemetry / analytics",
        "✔  Disabled",
        "TELEMETRY_ENABLED = false",
    )
    privacy_log.add_row(
        "LLM model location",
        "✔  Local",
        "Ollama on localhost:11434",
    )
    privacy_log.add_row(
        "Data storage",
        "✔  Local",
        "SQLite at data/db.sqlite",
    )

    console.print(privacy_log)
    console.print()

    # Final guarantee stamp
    guarantee = Panel(
        Align.center(
            Text.assemble(
                ("ZERO-CLOUD GUARANTEE\n", "bold white"),
                ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "green"),
                ("0 bytes transmitted to external APIs\n", "bold green"),
                ("0 third-party services contacted\n", "bold green"),
                ("All processing on local hardware\n", "bold green"),
                ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "green"),
                (f"Verified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "dim"),
            )
        ),
        border_style="bold green",
        padding=(1, 4),
    )
    console.print(guarantee)
    console.print()

    # Audit log entry
    console.print("  [bold cyan]▸[/] Appending to immutable audit log …", end=" ")
    pause(0.4)
    console.print("[bold green]✔ WRITTEN[/]")
    console.print("    [dim]↳ data/audit.log  ·  entry #1,247  ·  append-only (Law §6)[/]")
    console.print()
    pause(1.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PHASE 6 — SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def phase_summary():
    console.print(Rule("[bold yellow]SESSION COMPLETE[/]"))
    console.print()

    summary = Table(box=box.DOUBLE, border_style="cyan", title="Pipeline Summary", title_style="bold")
    summary.add_column("Stage", style="bold white", width=30)
    summary.add_column("Status", justify="center", width=14)
    summary.add_column("Duration", justify="right", width=10)

    summary.add_row("System Initialization",      "[bold green]✔ Done[/]", "1.8s")
    summary.add_row("NL Query → Intent Parsing",  "[bold green]✔ Done[/]", "0.4s")
    summary.add_row("SQL → Data Retrieval",        "[bold green]✔ Done[/]", "0.012s")
    summary.add_row("Deterministic Analysis",      "[bold green]✔ Done[/]", "0.08s")
    summary.add_row("Draft Generation (LLM)",      "[bold green]✔ Done[/]", "1.2s")
    summary.add_row("Draft-Only Gate Check",       "[bold green]✔ PASS[/]", "—")
    summary.add_row("Privacy & Security Audit",    "[bold green]✔ PASS[/]", "—")
    summary.add_row("External Data Transmission",  "[bold green]✔ 0 bytes[/]", "—")

    console.print(summary)
    console.print()
    console.print(
        Align.center(
            Text.assemble(
                ("Autify Engine V1", "bold cyan"),
                (" · ", "dim"),
                ("Retail Operations Module", "bold magenta"),
                (" · ", "dim"),
                ("All rights reserved © 2026", "dim"),
            )
        )
    )
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    try:
        phase_splash()
        phase_boot()
        phase_input()
        phase_tool_calling()
        phase_output()
        phase_security()
        phase_summary()
    except KeyboardInterrupt:
        console.print("\n[bold red]Demo interrupted.[/]")
        sys.exit(0)


if __name__ == "__main__":
    main()
