"""
record_demo.py — Records the Autify Engine Retail Demo as a video.

Pipeline:
  1. Runs demo_retail.py internally, capturing all ANSI output with timestamps
  2. Generates an HTML page that replays the output via xterm.js
  3. Uses Playwright (headless Chromium) to record the replay as WebM
  4. Converts to MP4 via ffmpeg (if available)

Usage:
    python record_demo.py

Requirements (auto-installed if missing):
    pip install rich playwright
    python -m playwright install chromium
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

OUT = sys.__stdout__          # safe handle for our own status messages
TERM_WIDTH = 110              # must match demo_retail.py


# ═══════════════════════════════════════════════════════════════════════
#  1.  CAPTURE DEMO OUTPUT WITH TIMING
# ═══════════════════════════════════════════════════════════════════════

class OutputCapture:
    """File-like object that records every write() with a timestamp
    while pretending to be a real terminal so Rich emits full ANSI."""

    def __init__(self):
        self.records: list[tuple[float, str]] = []
        self._start: float = time.time()

    def write(self, text: str) -> int:
        self.records.append((time.time() - self._start, text))
        return len(text)

    def flush(self):
        pass

    def isatty(self) -> bool:          # Rich checks this
        return True

    @property
    def encoding(self) -> str:
        return "utf-8"


def capture_demo() -> list[tuple[float, str]]:
    """Import & run demo_retail, returning [(elapsed_sec, ansi_text), …]."""
    from rich.console import Console

    cap = OutputCapture()

    import demo_retail                          # import the demo module
    demo_retail.console = Console(              # swap in our capturing console
        file=cap,
        width=TERM_WIDTH,
        force_terminal=True,
        color_system="truecolor",
    )

    print("⏺  Capturing demo output (this takes ~20 s) …", file=OUT, flush=True)
    demo_retail.main()

    dur = cap.records[-1][0] if cap.records else 0
    print(f"✔  Captured {len(cap.records)} chunks over {dur:.1f}s", file=OUT, flush=True)
    return cap.records


# ═══════════════════════════════════════════════════════════════════════
#  2.  GROUP SMALL WRITES & BUILD XTERM.JS HTML
# ═══════════════════════════════════════════════════════════════════════

def group_writes(records, gap_ms: int = 30) -> list[dict]:
    """Merge writes that arrive within `gap_ms` of each other."""
    groups: list[dict] = []
    buf = ""
    t0 = 0.0
    for t, text in records:
        ms = round(t * 1000)
        if not buf:
            buf, t0 = text, ms
        elif ms - t0 < gap_ms:
            buf += text
        else:
            groups.append({"t": int(t0), "d": buf})
            buf, t0 = text, ms
    if buf:
        groups.append({"t": int(t0), "d": buf})
    return groups


def build_replay_html(groups: list[dict], path: str) -> None:
    """Write an HTML file that replays recorded ANSI in xterm.js."""
    data_json = json.dumps(groups, ensure_ascii=False)

    html = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Autify Engine — Retail Demo Recording</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
<style>
  *    { margin:0; padding:0; box-sizing:border-box; }
  html,body { background:#0d1117; height:100%%; overflow:hidden; }
  #terminal { width:100%%; height:100%%; padding:10px 18px; }
  .xterm     { height:100%%; }
</style>
</head><body>
<div id="terminal"></div>

<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
<script>
// ── Data injected by record_demo.py ──
const DATA = """ + data_json + r""";

// ── Terminal setup ──
const term = new Terminal({
  theme: {
    background:    '#0d1117',
    foreground:    '#e6edf3',
    cursor:        '#e6edf3',
    cursorAccent:  '#0d1117',
    selection:     '#264f78',
    black:         '#484f58',
    red:           '#ff7b72',
    green:         '#3fb950',
    yellow:        '#d29922',
    blue:          '#58a6ff',
    magenta:       '#bc8cff',
    cyan:          '#39c5cf',
    white:         '#b1bac4',
    brightBlack:   '#6e7681',
    brightRed:     '#ffa198',
    brightGreen:   '#56d364',
    brightYellow:  '#e3b341',
    brightBlue:    '#79c0ff',
    brightMagenta: '#d2a8ff',
    brightCyan:    '#56d4dd',
    brightWhite:   '#f0f6fc',
  },
  fontSize:       15,
  fontFamily:     "'Cascadia Code','Consolas','Courier New',monospace",
  lineHeight:     1.15,
  cursorBlink:    false,
  cursorStyle:    'block',
  scrollback:     10000,
  convertEol:     true,
});

const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminal'));
fitAddon.fit();
window.addEventListener('resize', () => fitAddon.fit());

// ── Replay engine ──
const PRE_DELAY  = 1000;   // 1 s blank screen before splash
const POST_DELAY = 2500;   // 2.5 s hold after final output

function replay() {
  let i = 0;
  function step() {
    if (i >= DATA.length) {
      setTimeout(() => { document.title = 'DONE'; }, POST_DELAY);
      return;
    }
    term.write(DATA[i].d);
    i++;
    if (i < DATA.length) {
      const gap = Math.min(DATA[i].t - DATA[i-1].t, 3000);
      setTimeout(step, Math.max(gap, 1));
    } else {
      step();            // last chunk → trigger end
    }
  }
  setTimeout(step, PRE_DELAY);
}

document.fonts.ready.then(() => { fitAddon.fit(); replay(); });
</script>
</body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✔  HTML replay page → {path}", file=OUT, flush=True)


# ═══════════════════════════════════════════════════════════════════════
#  3.  RECORD WITH PLAYWRIGHT
# ═══════════════════════════════════════════════════════════════════════

async def record_video(html_path: str, webm_path: str) -> bool:
    """Open the replay in headless Chromium and save the video."""
    from playwright.async_api import async_playwright

    video_tmp = os.path.join(SCRIPT_DIR, "_pw_tmp")
    os.makedirs(video_tmp, exist_ok=True)

    print("⏺  Launching headless Chromium …", file=OUT, flush=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=video_tmp,
            record_video_size={"width": 1280, "height": 720},
        )
        page = await ctx.new_page()
        file_url = "file:///" + html_path.replace("\\", "/")
        await page.goto(file_url, wait_until="networkidle")

        print("⏺  Recording demo playback — please wait …", file=OUT, flush=True)

        try:
            await page.wait_for_function(
                "document.title === 'DONE'",
                timeout=180_000,
            )
        except Exception as exc:
            print(f"⚠  Replay wait: {exc}", file=OUT, flush=True)

        vid_path = await page.video.path()
        await ctx.close()
        await browser.close()

    if os.path.exists(vid_path):
        shutil.move(vid_path, webm_path)
        shutil.rmtree(video_tmp, ignore_errors=True)
        mb = os.path.getsize(webm_path) / 1_048_576
        print(f"✔  WebM saved → {webm_path}  ({mb:.1f} MB)", file=OUT, flush=True)
        return True

    print("✘  Video file not found after recording.", file=OUT, flush=True)
    return False


# ═══════════════════════════════════════════════════════════════════════
#  4.  CONVERT TO MP4 (optional, needs ffmpeg)
# ═══════════════════════════════════════════════════════════════════════

def convert_to_mp4(webm: str, mp4: str) -> bool:
    ffmpeg = shutil.which("ffmpeg")

    # Fall back to bundled ffmpeg from imageio-ffmpeg if installed
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    if not ffmpeg:
        print("ℹ  ffmpeg not found — keeping WebM (plays fine on most devices).", file=OUT, flush=True)
        print("   Install:  pip install imageio-ffmpeg", file=OUT, flush=True)
        print("   Then re-run, or manually:  ffmpeg -i demo_recording.webm -c:v libx264 demo_recording.mp4", file=OUT, flush=True)
        return False

    print(f"⏺  Converting WebM → MP4 (using {os.path.basename(ffmpeg)}) …", file=OUT, flush=True)
    r = subprocess.run(
        [ffmpeg, "-y", "-i", webm,
         "-c:v", "libx264", "-preset", "fast",
         "-crf", "23", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", mp4],
        capture_output=True, text=True,
    )
    if r.returncode == 0 and os.path.exists(mp4):
        mb = os.path.getsize(mp4) / 1_048_576
        print(f"✔  MP4 saved → {mp4}  ({mb:.1f} MB)", file=OUT, flush=True)
        if mb > 15:
            print("⚠  File > 15 MB. Try: ffmpeg -i demo_recording.mp4 -crf 28 demo_small.mp4", file=OUT, flush=True)
        return True

    print(f"⚠  ffmpeg failed: {r.stderr[:300]}", file=OUT, flush=True)
    return False


# ═══════════════════════════════════════════════════════════════════════
#  DEPENDENCY CHECK
# ═══════════════════════════════════════════════════════════════════════

def ensure_deps():
    """Make sure playwright is installed and Chromium is downloaded."""
    try:
        import playwright
    except ImportError:
        print("⏺  Installing playwright …", file=OUT, flush=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Check if chromium browser binary exists
    print("⏺  Ensuring Chromium browser is available …", file=OUT, flush=True)
    r = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"⚠  Chromium install note: {r.stderr[:300]}", file=OUT, flush=True)
    else:
        print("✔  Chromium ready", file=OUT, flush=True)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    print("━" * 60, file=OUT)
    print("  Autify Engine — Demo Video Recorder", file=OUT)
    print("━" * 60, file=OUT, flush=True)

    # 0. Dependencies
    ensure_deps()

    # 1. Capture
    records = capture_demo()

    # 2. Build HTML
    groups = group_writes(records)
    html_path = os.path.join(SCRIPT_DIR, "demo_replay.html")
    build_replay_html(groups, html_path)

    # 3. Record
    webm_path = os.path.join(SCRIPT_DIR, "demo_recording.webm")
    ok = await record_video(html_path, webm_path)
    if not ok:
        print("✘  Recording failed — check network/CDN access for xterm.js.", file=OUT, flush=True)
        return

    # 4. Convert
    mp4_path = os.path.join(SCRIPT_DIR, "demo_recording.mp4")
    convert_to_mp4(webm_path, mp4_path)

    print("\n✔  All done!  Files in:", file=OUT)
    print(f"   {SCRIPT_DIR}", file=OUT, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
