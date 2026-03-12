"""
record_dashboard.py — Records the Autify Engine Dashboard Demo as MP4.

Opens demo_dashboard.html in headless Chromium via Playwright,
records the self-playing demo sequence, and converts to MP4.

Usage:
    python record_dashboard.py
"""

import asyncio
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(SCRIPT_DIR, "demo_dashboard.html")
WEBM_OUT = os.path.join(SCRIPT_DIR, "dashboard_recording.webm")
MP4_OUT = os.path.join(SCRIPT_DIR, "dashboard_recording.mp4")


async def record():
    from playwright.async_api import async_playwright

    video_tmp = os.path.join(SCRIPT_DIR, "_pw_dash_tmp")
    os.makedirs(video_tmp, exist_ok=True)

    print("⏺  Launching headless Chromium (1280×720) …")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=video_tmp,
            record_video_size={"width": 1280, "height": 720},
        )
        page = await ctx.new_page()

        file_url = "file:///" + HTML_FILE.replace("\\", "/")
        await page.goto(file_url, wait_until="networkidle")

        print("⏺  Recording dashboard demo (~47 s) — please wait …")

        try:
            await page.wait_for_function(
                "document.title === 'DONE'",
                timeout=120_000,
            )
            # Hold 2.5 s after DONE for clean ending
            await asyncio.sleep(2.5)
        except Exception as exc:
            print(f"⚠  Timeout/error: {exc}")

        vid_path = await page.video.path()
        await ctx.close()
        await browser.close()

    if os.path.exists(vid_path):
        shutil.move(vid_path, WEBM_OUT)
        shutil.rmtree(video_tmp, ignore_errors=True)
        mb = os.path.getsize(WEBM_OUT) / 1_048_576
        print(f"✔  WebM saved → {WEBM_OUT}  ({mb:.1f} MB)")
        return True

    print("✘  Video file not found.")
    return False


def convert_to_mp4():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    if not ffmpeg:
        print("ℹ  ffmpeg not found — keeping WebM.")
        print("   Install:  pip install imageio-ffmpeg")
        return

    print(f"⏺  Converting WebM → MP4 ({os.path.basename(ffmpeg)}) …")
    r = subprocess.run(
        [ffmpeg, "-y", "-i", WEBM_OUT,
         "-c:v", "libx264", "-preset", "fast",
         "-crf", "23", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", MP4_OUT],
        capture_output=True, text=True,
    )
    if r.returncode == 0 and os.path.exists(MP4_OUT):
        mb = os.path.getsize(MP4_OUT) / 1_048_576
        print(f"✔  MP4 saved → {MP4_OUT}  ({mb:.1f} MB)")
        if mb > 15:
            print("⚠  File > 15 MB. Re-encode with higher CRF if needed.")
    else:
        print(f"⚠  ffmpeg error: {r.stderr[:300]}")


async def main():
    print("━" * 56)
    print("  Autify Engine — Dashboard Video Recorder")
    print("━" * 56)

    ok = await record()
    if ok:
        convert_to_mp4()

    print("\n✔  Done!  Files in:", SCRIPT_DIR)


if __name__ == "__main__":
    asyncio.run(main())
